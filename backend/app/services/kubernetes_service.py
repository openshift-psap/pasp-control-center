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
        
        configuration = client.Configuration.get_default_copy()
        configuration.retries = 1
        
        self._api_client = client.ApiClient(configuration)
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

    def get_topology(self) -> Dict[str, Any]:
        """Get cluster topology with detailed node information for visualization."""
        try:
            nodes = self.core_v1.list_node()
            pods = self.core_v1.list_pod_for_all_namespaces()
            
            # Group pods by node
            pods_by_node = {}
            for pod in pods.items:
                node_name = pod.spec.node_name
                if node_name:
                    if node_name not in pods_by_node:
                        pods_by_node[node_name] = []
                    pods_by_node[node_name].append({
                        "name": pod.metadata.name,
                        "namespace": pod.metadata.namespace,
                        "phase": pod.status.phase,
                    })
            
            topology_nodes = []
            control_plane_nodes = []
            worker_nodes = []
            infra_nodes = []
            
            for node in nodes.items:
                roles = self._get_node_roles(node)
                labels = node.metadata.labels or {}
                
                # Parse instance type and zone from labels
                instance_type = labels.get("node.kubernetes.io/instance-type", 
                                          labels.get("beta.kubernetes.io/instance-type", "unknown"))
                zone = labels.get("topology.kubernetes.io/zone",
                                 labels.get("failure-domain.beta.kubernetes.io/zone", "unknown"))
                region = labels.get("topology.kubernetes.io/region",
                                   labels.get("failure-domain.beta.kubernetes.io/region", "unknown"))
                
                # Get GPU information from labels (populated by NVIDIA GPU Operator)
                gpu_count = node.status.capacity.get("nvidia.com/gpu", "0")
                gpu_product = labels.get("nvidia.com/gpu.product", "")
                gpu_memory = labels.get("nvidia.com/gpu.memory", "")
                
                # Build GPU type string
                if gpu_product:
                    gpu_type = gpu_product.replace("-", " ")
                    if gpu_memory:
                        gpu_memory_gb = int(gpu_memory) // 1024 if gpu_memory.isdigit() else gpu_memory
                        gpu_type = f"{gpu_type} ({gpu_memory_gb}GB)"
                else:
                    gpu_type = "N/A" if gpu_count == "0" else "Unknown GPU"
                
                node_info = {
                    "name": node.metadata.name,
                    "status": self._get_node_status(node),
                    "roles": roles,
                    "cpu": node.status.capacity.get("cpu", "0"),
                    "memory": node.status.capacity.get("memory", "0"),
                    "memory_gb": round(self._parse_memory(node.status.capacity.get("memory", "0")) / (1024**3), 1),
                    "gpu": gpu_count,
                    "gpu_type": gpu_type,
                    "instance_type": instance_type,
                    "zone": zone,
                    "region": region,
                    "pod_count": len(pods_by_node.get(node.metadata.name, [])),
                    "os_image": node.status.node_info.os_image if node.status.node_info else "unknown",
                    "kernel_version": node.status.node_info.kernel_version if node.status.node_info else "unknown",
                    "container_runtime": node.status.node_info.container_runtime_version if node.status.node_info else "unknown",
                    "kubelet_version": node.status.node_info.kubelet_version if node.status.node_info else "unknown",
                    "architecture": node.status.node_info.architecture if node.status.node_info else "unknown",
                    "internal_ip": self._get_node_ip(node, "InternalIP"),
                    "external_ip": self._get_node_ip(node, "ExternalIP"),
                }
                
                topology_nodes.append(node_info)
                
                if "master" in roles or "control-plane" in roles:
                    control_plane_nodes.append(node_info)
                elif "infra" in roles:
                    infra_nodes.append(node_info)
                else:
                    worker_nodes.append(node_info)
            
            return {
                "nodes": topology_nodes,
                "control_plane": control_plane_nodes,
                "workers": worker_nodes,
                "infra": infra_nodes,
                "total_nodes": len(topology_nodes),
                "zones": list(set(n["zone"] for n in topology_nodes if n["zone"] != "unknown")),
            }
        except Exception as e:
            logger.error(f"Error getting topology: {e}")
            return {"nodes": [], "error": str(e)}

    def _get_node_ip(self, node, ip_type: str) -> Optional[str]:
        """Get node IP address of specified type."""
        if node.status.addresses:
            for addr in node.status.addresses:
                if addr.type == ip_type:
                    return addr.address
        return None

    def get_ocp_details(self) -> Dict[str, Any]:
        """Get OpenShift-specific cluster details."""
        try:
            custom_api = client.CustomObjectsApi(self._api_client)
            
            ocp_details = {
                "cluster_version": None,
                "cluster_id": None,
                "platform": None,
                "infrastructure": None,
                "network_type": None,
                "ingress_domain": None,
                "update_available": False,
                "available_updates": [],
            }
            
            # Get ClusterVersion
            try:
                cv = custom_api.get_cluster_custom_object(
                    group="config.openshift.io",
                    version="v1",
                    plural="clusterversions",
                    name="version"
                )
                ocp_details["cluster_version"] = cv.get("status", {}).get("desired", {}).get("version")
                ocp_details["cluster_id"] = cv.get("spec", {}).get("clusterID")
                
                # Check for available updates
                available = cv.get("status", {}).get("availableUpdates", [])
                if available:
                    ocp_details["update_available"] = True
                    ocp_details["available_updates"] = [u.get("version") for u in available[:5]]
                
                # Get conditions
                conditions = cv.get("status", {}).get("conditions", [])
                ocp_details["conditions"] = [
                    {"type": c.get("type"), "status": c.get("status"), "message": c.get("message", "")[:100]}
                    for c in conditions
                ]
            except Exception as e:
                logger.warning(f"Could not get ClusterVersion: {e}")
            
            # Get Infrastructure
            try:
                infra = custom_api.get_cluster_custom_object(
                    group="config.openshift.io",
                    version="v1",
                    plural="infrastructures",
                    name="cluster"
                )
                ocp_details["platform"] = infra.get("status", {}).get("platform")
                ocp_details["infrastructure"] = infra.get("status", {}).get("infrastructureName")
                ocp_details["api_server_url"] = infra.get("status", {}).get("apiServerURL")
                ocp_details["api_server_internal"] = infra.get("status", {}).get("apiServerInternalURI")
            except Exception as e:
                logger.warning(f"Could not get Infrastructure: {e}")
            
            # Get Network config
            try:
                network = custom_api.get_cluster_custom_object(
                    group="config.openshift.io",
                    version="v1",
                    plural="networks",
                    name="cluster"
                )
                ocp_details["network_type"] = network.get("status", {}).get("networkType")
                ocp_details["cluster_network"] = network.get("status", {}).get("clusterNetwork", [])
                ocp_details["service_network"] = network.get("status", {}).get("serviceNetwork", [])
            except Exception as e:
                logger.warning(f"Could not get Network: {e}")
            
            # Get Ingress
            try:
                ingress = custom_api.get_cluster_custom_object(
                    group="config.openshift.io",
                    version="v1",
                    plural="ingresses",
                    name="cluster"
                )
                ocp_details["ingress_domain"] = ingress.get("spec", {}).get("domain")
            except Exception as e:
                logger.warning(f"Could not get Ingress: {e}")
            
            return ocp_details
        except Exception as e:
            logger.error(f"Error getting OCP details: {e}")
            return {"error": str(e)}

    def get_operators(self) -> List[Dict[str, Any]]:
        """Get installed operators (ClusterServiceVersions)."""
        try:
            custom_api = client.CustomObjectsApi(self._api_client)
            
            operators = []
            
            # Get ClusterServiceVersions from all namespaces
            try:
                csvs = custom_api.list_cluster_custom_object(
                    group="operators.coreos.com",
                    version="v1alpha1",
                    plural="clusterserviceversions"
                )
                
                seen = set()
                for csv in csvs.get("items", []):
                    name = csv.get("spec", {}).get("displayName") or csv.get("metadata", {}).get("name")
                    if name in seen:
                        continue
                    seen.add(name)
                    
                    operators.append({
                        "name": name,
                        "namespace": csv.get("metadata", {}).get("namespace"),
                        "version": csv.get("spec", {}).get("version"),
                        "phase": csv.get("status", {}).get("phase"),
                        "display_name": csv.get("spec", {}).get("displayName"),
                        "description": (csv.get("spec", {}).get("description") or "")[:200],
                        "provider": csv.get("spec", {}).get("provider", {}).get("name"),
                    })
            except Exception as e:
                logger.warning(f"Could not get CSVs: {e}")
            
            return sorted(operators, key=lambda x: x.get("name", ""))
        except Exception as e:
            logger.error(f"Error getting operators: {e}")
            return []

    def get_workloads(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get pods and deployments with node information."""
        try:
            pods_list = []
            deployments_list = []
            
            # Get pods
            if namespace:
                pods = self.core_v1.list_namespaced_pod(namespace)
            else:
                pods = self.core_v1.list_pod_for_all_namespaces()
            
            for pod in pods.items:
                # Skip system pods for cleaner view unless specifically requested
                ns = pod.metadata.namespace
                if not namespace and ns in ["kube-system", "openshift-kube-scheduler", 
                                             "openshift-kube-controller-manager", 
                                             "openshift-kube-apiserver", "openshift-etcd"]:
                    continue
                
                pods_list.append({
                    "name": pod.metadata.name,
                    "namespace": ns,
                    "node": pod.spec.node_name,
                    "phase": pod.status.phase,
                    "ip": pod.status.pod_ip,
                    "containers": [c.name for c in pod.spec.containers],
                    "restarts": sum(cs.restart_count for cs in (pod.status.container_statuses or []) if cs.restart_count),
                    "created": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None,
                })
            
            # Get deployments
            apps_v1 = client.AppsV1Api(self._api_client)
            if namespace:
                deployments = apps_v1.list_namespaced_deployment(namespace)
            else:
                deployments = apps_v1.list_deployment_for_all_namespaces()
            
            for dep in deployments.items:
                ns = dep.metadata.namespace
                if not namespace and ns.startswith("openshift-"):
                    continue
                    
                deployments_list.append({
                    "name": dep.metadata.name,
                    "namespace": ns,
                    "replicas": dep.spec.replicas,
                    "ready_replicas": dep.status.ready_replicas or 0,
                    "available_replicas": dep.status.available_replicas or 0,
                })
            
            # Group pods by node for visualization
            pods_by_node = {}
            for pod in pods_list:
                node = pod.get("node") or "unscheduled"
                if node not in pods_by_node:
                    pods_by_node[node] = []
                pods_by_node[node].append(pod)
            
            return {
                "pods": pods_list[:100],  # Limit for performance
                "deployments": deployments_list[:50],
                "pods_by_node": pods_by_node,
                "total_pods": len(pods_list),
                "total_deployments": len(deployments_list),
            }
        except Exception as e:
            logger.error(f"Error getting workloads: {e}")
            return {"pods": [], "deployments": [], "error": str(e)}

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

                # Try to create a service account with a long-lived token
                logger.info(f"Creating service account for persistent access to {cluster_name}")
                sa_result = await KubernetesService.create_service_account_token(
                    api_server, access_token, cluster_name
                )
                
                # Use the SA token if available, otherwise fall back to OAuth token
                if sa_result.get("success") and sa_result.get("token"):
                    final_token = sa_result["token"]
                    auth_type = "service-account"
                    logger.info(f"Using service account token for {cluster_name} (long-lived)")
                else:
                    final_token = access_token
                    auth_type = "oauth-token"
                    logger.warning(f"Using OAuth token for {cluster_name} (will expire)")

                # Generate kubeconfig with the token
                kubeconfig_content = KubernetesService._generate_kubeconfig_token(
                    api_server, cluster_name, final_token
                )
                
                filepath = KubernetesService.save_kubeconfig(
                    kubeconfig_content, storage_path, cluster_name
                )
                
                return {
                    "success": True,
                    "kubeconfig_path": filepath,
                    "api_server": api_server,
                    "auth_type": auth_type,
                    "service_account": sa_result.get("service_account") if sa_result.get("success") else None
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
    async def create_service_account_token(
        api_server: str,
        initial_token: str,
        cluster_name: str
    ) -> Dict[str, Any]:
        """
        Create a service account with a long-lived token for persistent cluster access.
        This avoids the OAuth token expiration issue.
        """
        sa_name = "pasp-control-center"
        namespace = "pasp-system"
        
        try:
            async with httpx.AsyncClient(verify=False, timeout=30.0) as http_client:
                headers = {
                    "Authorization": f"Bearer {initial_token}",
                    "Content-Type": "application/json"
                }
                
                # Step 1: Create namespace (ignore if exists)
                ns_body = {
                    "apiVersion": "v1",
                    "kind": "Namespace",
                    "metadata": {"name": namespace}
                }
                ns_resp = await http_client.post(
                    f"{api_server}/api/v1/namespaces",
                    headers=headers,
                    json=ns_body
                )
                if ns_resp.status_code not in [200, 201, 409]:  # 409 = already exists
                    logger.warning(f"Failed to create namespace: {ns_resp.status_code} {ns_resp.text[:200]}")
                
                # Step 2: Create ServiceAccount
                sa_body = {
                    "apiVersion": "v1",
                    "kind": "ServiceAccount",
                    "metadata": {
                        "name": sa_name,
                        "namespace": namespace,
                        "labels": {
                            "app": "pasp-control-center",
                            "managed-by": "pasp-control-center"
                        }
                    }
                }
                sa_resp = await http_client.post(
                    f"{api_server}/api/v1/namespaces/{namespace}/serviceaccounts",
                    headers=headers,
                    json=sa_body
                )
                if sa_resp.status_code not in [200, 201, 409]:
                    logger.warning(f"Failed to create SA: {sa_resp.status_code} {sa_resp.text[:200]}")
                
                # Step 3: Create ClusterRoleBinding for cluster-reader permissions
                crb_name = f"pasp-control-center-{cluster_name.replace(' ', '-').lower()[:20]}"
                crb_body = {
                    "apiVersion": "rbac.authorization.k8s.io/v1",
                    "kind": "ClusterRoleBinding",
                    "metadata": {
                        "name": crb_name,
                        "labels": {
                            "app": "pasp-control-center",
                            "managed-by": "pasp-control-center"
                        }
                    },
                    "roleRef": {
                        "apiGroup": "rbac.authorization.k8s.io",
                        "kind": "ClusterRole",
                        "name": "cluster-admin"  # Using cluster-admin for full visibility
                    },
                    "subjects": [{
                        "kind": "ServiceAccount",
                        "name": sa_name,
                        "namespace": namespace
                    }]
                }
                crb_resp = await http_client.post(
                    f"{api_server}/apis/rbac.authorization.k8s.io/v1/clusterrolebindings",
                    headers=headers,
                    json=crb_body
                )
                if crb_resp.status_code not in [200, 201, 409]:
                    logger.warning(f"Failed to create CRB: {crb_resp.status_code} {crb_resp.text[:200]}")
                
                # Step 4: Create a Secret for the service account token (legacy approach for long-lived token)
                secret_name = f"{sa_name}-token"
                secret_body = {
                    "apiVersion": "v1",
                    "kind": "Secret",
                    "metadata": {
                        "name": secret_name,
                        "namespace": namespace,
                        "annotations": {
                            "kubernetes.io/service-account.name": sa_name
                        },
                        "labels": {
                            "app": "pasp-control-center",
                            "managed-by": "pasp-control-center"
                        }
                    },
                    "type": "kubernetes.io/service-account-token"
                }
                secret_resp = await http_client.post(
                    f"{api_server}/api/v1/namespaces/{namespace}/secrets",
                    headers=headers,
                    json=secret_body
                )
                
                if secret_resp.status_code == 409:
                    # Secret exists, fetch it
                    pass
                elif secret_resp.status_code not in [200, 201]:
                    logger.warning(f"Failed to create secret: {secret_resp.status_code} {secret_resp.text[:200]}")
                
                # Step 5: Wait briefly and fetch the token from the secret
                import asyncio
                await asyncio.sleep(2)  # Give K8s time to populate the token
                
                secret_get_resp = await http_client.get(
                    f"{api_server}/api/v1/namespaces/{namespace}/secrets/{secret_name}",
                    headers=headers
                )
                
                if secret_get_resp.status_code == 200:
                    secret_data = secret_get_resp.json()
                    token_b64 = secret_data.get("data", {}).get("token")
                    if token_b64:
                        import base64
                        sa_token = base64.b64decode(token_b64).decode('utf-8')
                        logger.info(f"Successfully created service account token for {cluster_name}")
                        return {
                            "success": True,
                            "token": sa_token,
                            "service_account": f"{namespace}/{sa_name}",
                            "token_type": "service-account"
                        }
                
                # Fallback: Try TokenRequest API (OpenShift 4.11+)
                token_request_body = {
                    "apiVersion": "authentication.k8s.io/v1",
                    "kind": "TokenRequest",
                    "spec": {
                        "expirationSeconds": 31536000  # 1 year
                    }
                }
                token_req_resp = await http_client.post(
                    f"{api_server}/api/v1/namespaces/{namespace}/serviceaccounts/{sa_name}/token",
                    headers=headers,
                    json=token_request_body
                )
                
                if token_req_resp.status_code in [200, 201]:
                    token_data = token_req_resp.json()
                    sa_token = token_data.get("status", {}).get("token")
                    if sa_token:
                        logger.info(f"Successfully created service account token via TokenRequest for {cluster_name}")
                        return {
                            "success": True,
                            "token": sa_token,
                            "service_account": f"{namespace}/{sa_name}",
                            "token_type": "token-request",
                            "expires_in": "1 year"
                        }
                
                # If we get here, SA creation worked but token retrieval failed
                # Return the original token as fallback
                logger.warning(f"Could not retrieve SA token, using original token")
                return {
                    "success": False,
                    "error": "Could not retrieve service account token",
                    "fallback": True
                }
                
        except Exception as e:
            logger.error(f"Error creating service account: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": True
            }

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
