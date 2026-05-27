# Deploying PSAP Control Center on OpenShift

This guide deploys the PSAP Control Center on an OpenShift (OCP) cluster.

## Prerequisites

- `oc` CLI installed
- Credentials for the target cluster
- The internal image registry must be enabled (`Managed` state)

## Target Cluster

- **Console**: `https://console-openshift-console.apps.psap-automation.ibm.rhperfscale.org`
- **API**: `https://api.psap-automation.ibm.rhperfscale.org:6443`
- **App URL**: `https://control-center.apps.psap-automation.ibm.rhperfscale.org`

## Naming Convention

All resources use the `psap-control-center-*` prefix:

| Resource    | Name                                |
| ----------- | ----------------------------------- |
| Namespace   | `psap-control-center`               |
| Secrets     | `psap-control-center-admin`         |
|             | `psap-control-center-config`        |
| PVCs        | `psap-control-center-data`          |
|             | `psap-control-center-kubeconfigs`   |
| Builds      | `psap-control-center-backend`       |
|             | `psap-control-center-frontend`      |
| Deployments | `psap-control-center-backend`       |
|             | `psap-control-center-frontend`      |
| Services    | `psap-control-center-backend`       |
|             | `psap-control-center-frontend`      |
| Route       | `psap-control-center`               |

## Deployment Steps

### 1. Log in to the cluster

```bash
oc login https://api.psap-automation.ibm.rhperfscale.org:6443 \
  --username=<user> --password=<pass>
```

### 2. Verify the internal image registry is enabled

```bash
oc get configs.imageregistry.operator.openshift.io/cluster \
  -o jsonpath='{.spec.managementState}'
```

Expected output: `Managed`

### 3. Create the namespace

```bash
oc new-project psap-control-center
```

### 4. Create secrets

```bash
oc create secret generic psap-control-center-admin \
  --from-literal=ADMIN_USERNAME=admin \
  --from-literal=ADMIN_PASSWORD='<pick-a-secure-password>'

oc create secret generic psap-control-center-config \
  --from-literal=SECRET_KEY='<random-string>' \
  --from-literal=DATABASE_URL='sqlite+aiosqlite:///./data/psap_control_center.db' \
  --from-literal=LOG_LEVEL='INFO'
```

### 5. Create persistent volume claims

```bash
oc apply -f deploy/pvcs.yaml
```

### 6. Build images on-cluster

Before building the frontend, update `frontend/nginx.conf` so the proxy
points to the OCP service name:

```nginx
proxy_pass http://psap-control-center-backend:8000;
```

Then build both images:

```bash
# Backend
oc new-build --name=psap-control-center-backend --binary --strategy=docker
oc start-build psap-control-center-backend --from-dir=./backend --follow

# Frontend
oc new-build --name=psap-control-center-frontend --binary --strategy=docker
oc start-build psap-control-center-frontend --from-dir=./frontend --follow
```

Images are pushed to the internal registry automatically.

### 7. Deploy the backend

```bash
oc create deployment psap-control-center-backend \
  --image=image-registry.openshift-image-registry.svc:5000/psap-control-center/psap-control-center-backend:latest

oc set env deployment/psap-control-center-backend \
  --from=secret/psap-control-center-admin
oc set env deployment/psap-control-center-backend \
  --from=secret/psap-control-center-config
oc set env deployment/psap-control-center-backend \
  KUBECONFIG_STORAGE_PATH=/app/kubeconfigs

oc set volume deployment/psap-control-center-backend \
  --add --name=data --mount-path=/app/data \
  --claim-name=psap-control-center-data
oc set volume deployment/psap-control-center-backend \
  --add --name=kubeconfigs --mount-path=/app/kubeconfigs \
  --claim-name=psap-control-center-kubeconfigs

oc expose deployment psap-control-center-backend --port=8000
```

### 8. Deploy the frontend

```bash
oc create deployment psap-control-center-frontend \
  --image=image-registry.openshift-image-registry.svc:5000/psap-control-center/psap-control-center-frontend:latest

oc expose deployment psap-control-center-frontend --port=80
```

### 9. Create the route

```bash
oc create route edge psap-control-center \
  --service=psap-control-center-frontend \
  --hostname=control-center.apps.psap-automation.ibm.rhperfscale.org
```

### 10. Verify

```bash
# Check pods are running
oc get pods

# Check the route
oc get route psap-control-center

# Test the backend health endpoint
curl -k https://control-center.apps.psap-automation.ibm.rhperfscale.org/api/v1/health
```

The app should be accessible at:
`https://control-center.apps.psap-automation.ibm.rhperfscale.org`

## Rebuilding After Code Changes

```bash
# Rebuild backend
oc start-build psap-control-center-backend --from-dir=./backend --follow

# Rebuild frontend
oc start-build psap-control-center-frontend --from-dir=./frontend --follow

# Pods will restart automatically with the new images
```

## Authentication

- **Viewing** (all GET endpoints): No authentication required
- **Modifying** (create, edit, delete): Requires sign-in with the admin credentials stored in the `psap-control-center-admin` secret

## Updating the Admin Password

```bash
oc delete secret psap-control-center-admin
oc create secret generic psap-control-center-admin \
  --from-literal=ADMIN_USERNAME=admin \
  --from-literal=ADMIN_PASSWORD='<new-password>'

# Restart the backend to pick up the change
oc rollout restart deployment/psap-control-center-backend
```

## Teardown

```bash
oc delete project psap-control-center
```

This removes all resources in the namespace.
