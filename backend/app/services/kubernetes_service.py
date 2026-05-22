from kubernetes import client, config
from kubernetes.client.rest import ApiException
from typing import Dict, Any, List, Optional
import yaml
import os
import tempfile
import logging
import httpx
import ssl
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class KubernetesService:
    def __init__(self, kubeconfig_path: str):
        self.kubeconfig_path = kubeconfig_path
        self._api_client = None
        self._core_v1 = None
        self._version_api = None

    def _load_config(self):
        if not os.path.exists(self.kubeconfig_path):
            raise FileNotFoundError(f"Kubeconfig not found: {self.kubeconfig_path}")
        
        config.load_kube_config(config_file=self.kubeconfig_path)
        self._api_client = client.ApiClient()
        self._core_v1 = client.CoreV1Api(self._api_client)
        self._version_api = client.VersionApi(self._api_client)

    @property
    def core_v1(self):
        if self._core_v1 is None:
            self._load_config()
        return self._core_v1

    @property
    def version_api(self):
        if self._version_api is None:
            self._load_config()
        return self._version_api

    def get_cluster_info(self) -> Dict[str, Any]:
        try:
            version_info = self.version_api.get_code()
            nodes = self.core_v1.list_node()
            
            gpu_count = 0
            node_details = []
            
            for node in nodes.items:
                node_info = {
                    "name": node.metadata.name,
                    "status": self._get_node_status(node),
                    "roles": self._get_node_roles(node),
                    "cpu": node.status.capacity.get("cpu", "unknown"),
                    "memory": node.status.capacity.get("memory", "unknown"),
                    "gpu": node.status.capacity.get("nvidia.com/gpu", "0"),
                }
                node_details.append(node_info)
                gpu_count += int(node.status.capacity.get("nvidia.com/gpu", 0))

            return {
                "status": "healthy",
                "cluster_version": f"{version_info.git_version}",
                "node_count": str(len(nodes.items)),
                "gpu_count": str(gpu_count),
                "nodes": node_details,
                "api_server": self._get_api_server_url()
            }
        except ApiException as e:
            logger.error(f"Kubernetes API error: {e}")
            return {"status": "error", "error": str(e)}
        except Exception as e:
            logger.error(f"Error getting cluster info: {e}")
            return {"status": "unreachable", "error": str(e)}

    def _get_node_status(self, node) -> str:
        for condition in node.status.conditions:
            if condition.type == "Ready":
                return "Ready" if condition.status == "True" else "NotReady"
        return "Unknown"

    def _get_node_roles(self, node) -> List[str]:
        roles = []
        labels = node.metadata.labels or {}
        for label in labels:
            if label.startswith("node-role.kubernetes.io/"):
                role = label.replace("node-role.kubernetes.io/", "")
                roles.append(role)
        return roles if roles else ["worker"]

    def _get_api_server_url(self) -> Optional[str]:
        try:
            with open(self.kubeconfig_path, 'r') as f:
                kubeconfig = yaml.safe_load(f)
            
            current_context = kubeconfig.get('current-context')
            for context in kubeconfig.get('contexts', []):
                if context.get('name') == current_context:
                    cluster_name = context.get('context', {}).get('cluster')
                    for cluster in kubeconfig.get('clusters', []):
                        if cluster.get('name') == cluster_name:
                            return cluster.get('cluster', {}).get('server')
        except Exception as e:
            logger.error(f"Error reading API server URL: {e}")
        return None

    def get_namespaces(self) -> List[str]:
        try:
            namespaces = self.core_v1.list_namespace()
            return [ns.metadata.name for ns in namespaces.items]
        except Exception as e:
            logger.error(f"Error getting namespaces: {e}")
            return []

    def get_resource_usage(self) -> Dict[str, Any]:
        try:
            nodes = self.core_v1.list_node()
            pods = self.core_v1.list_pod_for_all_namespaces()
            
            total_cpu_capacity = 0
            total_memory_capacity = 0
            total_gpu_capacity = 0
            
            for node in nodes.items:
                cpu = node.status.capacity.get("cpu", "0")
                if cpu.endswith("m"):
                    total_cpu_capacity += int(cpu[:-1]) / 1000
                else:
                    total_cpu_capacity += int(cpu)
                
                memory = node.status.capacity.get("memory", "0Ki")
                total_memory_capacity += self._parse_memory(memory)
                total_gpu_capacity += int(node.status.capacity.get("nvidia.com/gpu", 0))

            running_pods = sum(1 for pod in pods.items if pod.status.phase == "Running")
            
            return {
                "total_cpu_cores": total_cpu_capacity,
                "total_memory_gb": round(total_memory_capacity / (1024 ** 3), 2),
                "total_gpus": total_gpu_capacity,
                "running_pods": running_pods,
                "total_pods": len(pods.items),
                "total_nodes": len(nodes.items)
            }
        except Exception as e:
            logger.error(f"Error getting resource usage: {e}")
            return {}

    def _parse_memory(self, memory_str: str) -> int:
        multipliers = {
            'Ki': 1024,
            'Mi': 1024 ** 2,
            'Gi': 1024 ** 3,
            'Ti': 1024 ** 4,
            'K': 1000,
            'M': 1000 ** 2,
            'G': 1000 ** 3,
            'T': 1000 ** 4,
        }
        
        for suffix, multiplier in multipliers.items():
            if memory_str.endswith(suffix):
                return int(memory_str[:-len(suffix)]) * multiplier
        
        try:
            return int(memory_str)
        except ValueError:
            return 0

    def check_health(self) -> bool:
        try:
            self.version_api.get_code()
            return True
        except Exception:
            return False

    @staticmethod
    def parse_kubeconfig(content: str) -> Dict[str, Any]:
        try:
            kubeconfig = yaml.safe_load(content)
            
            contexts = [ctx.get('name') for ctx in kubeconfig.get('contexts', [])]
            clusters = [c.get('name') for c in kubeconfig.get('clusters', [])]
            current_context = kubeconfig.get('current-context')
            
            api_server = None
            for context in kubeconfig.get('contexts', []):
                if context.get('name') == current_context:
                    cluster_name = context.get('context', {}).get('cluster')
                    for cluster in kubeconfig.get('clusters', []):
                        if cluster.get('name') == cluster_name:
                            api_server = cluster.get('cluster', {}).get('server')
                            break
            
            return {
                "valid": True,
                "contexts": contexts,
                "clusters": clusters,
                "current_context": current_context,
                "api_server": api_server
            }
        except yaml.YAMLError as e:
            return {"valid": False, "error": f"Invalid YAML: {str(e)}"}
        except Exception as e:
            return {"valid": False, "error": str(e)}

    @staticmethod
    def save_kubeconfig(content: str, storage_path: str, cluster_name: str) -> str:
        os.makedirs(storage_path, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in cluster_name)
        filepath = os.path.join(storage_path, f"{safe_name}.kubeconfig")
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        os.chmod(filepath, 0o600)
        return filepath

    @staticmethod
    async def login_with_credentials(
        api_server: str,
        username: str,
        password: str,
        storage_path: str,
        cluster_name: str
    ) -> Dict[str, Any]:
        """
        Authenticate to OpenShift using username/password (kubeadmin) and generate a kubeconfig.
        This uses the OAuth token request flow.
        """
        api_server = api_server.rstrip('/')
        logger.info(f"Attempting login to: {api_server} with user: {username}")
        
        # Validate that this looks like an API server URL, not a console URL
        if 'console' in api_server.lower() and 'api.' not in api_server.lower():
            # Try to convert console URL to API URL
            # console-openshift-console.apps.cluster.domain -> api.cluster.domain:6443
            import re
            match = re.search(r'apps\.(.+)', api_server)
            if match:
                suggested_api = f"https://api.{match.group(1)}:6443"
                return {
                    "success": False, 
                    "error": f"It looks like you provided a console URL. Please use the API server URL instead. Try: {suggested_api}"
                }
        
        try:
            async with httpx.AsyncClient(verify=False, timeout=30.0) as http_client:
                # First, try to get OAuth metadata from the API server
                oauth_metadata_url = f"{api_server}/.well-known/oauth-authorization-server"
                oauth_server = None
                
                try:
                    metadata_resp = await http_client.get(oauth_metadata_url)
                    if metadata_resp.status_code == 200:
                        try:
                            oauth_metadata = metadata_resp.json()
                            oauth_server = oauth_metadata.get('issuer', '').rstrip('/')
                            logger.info(f"Found OAuth server: {oauth_server}")
                        except Exception:
                            pass
                except Exception as e:
                    logger.warning(f"Could not fetch OAuth metadata: {e}")

                access_token = None
                
                # Method 1: Use the OAuth authorize endpoint with challenging client
                oauth_base = oauth_server or api_server
                oauth_token_url = f"{oauth_base}/oauth/authorize?client_id=openshift-challenging-client&response_type=token"
                
                try:
                    auth_resp = await http_client.get(
                        oauth_token_url,
                        auth=(username, password),
                        follow_redirects=False
                    )
                    
                    # Check for token in redirect location (OAuth implicit flow)
                    if auth_resp.status_code in [301, 302, 303, 307, 308]:
                        location = auth_resp.headers.get('location', '')
                        if 'access_token=' in location:
                            import urllib.parse
                            parsed = urllib.parse.urlparse(location)
                            fragment_params = urllib.parse.parse_qs(parsed.fragment)
                            if 'access_token' in fragment_params:
                                access_token = fragment_params['access_token'][0]
                                logger.info("Got token via OAuth redirect")
                    
                    # Check X-CSRF-Token header
                    if not access_token:
                        csrf_token = auth_resp.headers.get('X-CSRF-Token')
                        if csrf_token:
                            access_token = csrf_token
                            logger.info("Got token via X-CSRF-Token header")
                except Exception as e:
                    logger.warning(f"OAuth authorize failed: {e}")

                # Method 2: Request token via oauthaccesstokens API
                if not access_token:
                    try:
                        token_request_url = f"{api_server}/apis/oauth.openshift.io/v1/oauthaccesstokens"
                        headers = {"Content-Type": "application/json"}
                        
                        # Try using basic auth header to request a token
                        import base64
                        basic_auth = base64.b64encode(f"{username}:{password}".encode()).decode()
                        headers["Authorization"] = f"Basic {basic_auth}"
                        
                        # First check if we can access the API at all
                        api_check = await http_client.get(
                            f"{api_server}/api/v1",
                            headers=headers
                        )
                        
                        if api_check.status_code == 200:
                            # Basic auth works directly with the API
                            kubeconfig_content = KubernetesService._generate_kubeconfig_basic_auth(
                                api_server, cluster_name, username, password
                            )
                            filepath = KubernetesService.save_kubeconfig(
                                kubeconfig_content, storage_path, cluster_name
                            )
                            return {
                                "success": True,
                                "kubeconfig_path": filepath,
                                "api_server": api_server,
                                "auth_type": "basic"
                            }
                        elif api_check.status_code == 401:
                            # Need proper OAuth - this is expected for most clusters
                            pass
                        else:
                            logger.warning(f"API check returned {api_check.status_code}")
                    except Exception as e:
                        logger.warning(f"Basic auth check failed: {e}")

                # Method 3: Try direct token request to OAuth server  
                if not access_token and oauth_server:
                    try:
                        # Use the WWW-Authenticate challenge flow
                        challenge_url = f"{oauth_server}/oauth/authorize?response_type=token&client_id=openshift-challenging-client"
                        challenge_resp = await http_client.head(challenge_url)
                        
                        if challenge_resp.status_code == 401:
                            # Now send with auth
                            token_resp = await http_client.get(
                                challenge_url,
                                auth=(username, password),
                                follow_redirects=False
                            )
                            
                            if token_resp.status_code in [301, 302, 303, 307, 308]:
                                location = token_resp.headers.get('location', '')
                                if 'access_token=' in location:
                                    import urllib.parse
                                    parsed = urllib.parse.urlparse(location)
                                    fragment_params = urllib.parse.parse_qs(parsed.fragment)
                                    if 'access_token' in fragment_params:
                                        access_token = fragment_params['access_token'][0]
                                        logger.info("Got token via challenge flow")
                    except Exception as e:
                        logger.warning(f"Challenge flow failed: {e}")

                if not access_token:
                    return {
                        "success": False,
                        "error": "Authentication failed. Please check your credentials and ensure the API server URL is correct (should be like https://api.cluster.domain:6443)"
                    }

                # Generate kubeconfig with the obtained token
                kubeconfig_content = KubernetesService._generate_kubeconfig_token(
                    api_server, cluster_name, access_token
                )
                
                filepath = KubernetesService.save_kubeconfig(
                    kubeconfig_content, storage_path, cluster_name
                )
                
                return {
                    "success": True,
                    "kubeconfig_path": filepath,
                    "api_server": api_server,
                    "auth_type": "token"
                }

        except httpx.ConnectError as e:
            logger.error(f"Connection error to {api_server}: {e}")
            return {"success": False, "error": f"Cannot connect to {api_server}. Please verify the URL is correct and accessible. Error: {str(e)}"}
        except httpx.TimeoutException as e:
            logger.error(f"Timeout connecting to {api_server}: {e}")
            return {"success": False, "error": f"Connection timed out to {api_server}. The cluster may be unreachable."}
        except Exception as e:
            import traceback
            logger.error(f"Error during login to {api_server}: {e}")
            logger.error(traceback.format_exc())
            return {"success": False, "error": f"Login error: {str(e)}"}

    @staticmethod
    def _generate_kubeconfig_token(api_server: str, cluster_name: str, token: str) -> str:
        """Generate a kubeconfig file content using a bearer token."""
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in cluster_name)
        
        kubeconfig = {
            'apiVersion': 'v1',
            'kind': 'Config',
            'current-context': safe_name,
            'clusters': [{
                'name': safe_name,
                'cluster': {
                    'server': api_server,
                    'insecure-skip-tls-verify': True
                }
            }],
            'contexts': [{
                'name': safe_name,
                'context': {
                    'cluster': safe_name,
                    'user': safe_name
                }
            }],
            'users': [{
                'name': safe_name,
                'user': {
                    'token': token
                }
            }]
        }
        
        return yaml.dump(kubeconfig, default_flow_style=False)

    @staticmethod
    def _generate_kubeconfig_basic_auth(api_server: str, cluster_name: str, username: str, password: str) -> str:
        """Generate a kubeconfig file content using basic auth."""
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in cluster_name)
        
        kubeconfig = {
            'apiVersion': 'v1',
            'kind': 'Config',
            'current-context': safe_name,
            'clusters': [{
                'name': safe_name,
                'cluster': {
                    'server': api_server,
                    'insecure-skip-tls-verify': True
                }
            }],
            'contexts': [{
                'name': safe_name,
                'context': {
                    'cluster': safe_name,
                    'user': safe_name
                }
            }],
            'users': [{
                'name': safe_name,
                'user': {
                    'username': username,
                    'password': password
                }
            }]
        }
        
        return yaml.dump(kubeconfig, default_flow_style=False)
