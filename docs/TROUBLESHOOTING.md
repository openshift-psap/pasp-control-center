# Troubleshooting

## Cluster Issues

### Cluster shows "unreachable" or "error" status

**Cause**: The backend cannot reach the cluster's Kubernetes API.

**Check**:
- Is the cluster actually running? Try `oc login` to it manually.
- Is the API server URL correct? Check the cluster detail page.
- Is the kubeconfig still valid? Tokens may have expired.

**Fix**: On the cluster detail page, try **Reauthenticate** with fresh kubeadmin credentials. This creates a new service account token.

### Cluster shows "error" after adding via credentials

**Cause**: The OAuth token obtained during login may have expired before the service account was fully created.

**Fix**: Click **Reauthenticate** on the cluster detail page with the same kubeadmin credentials. The system will create a new long-lived service account token.

### "Invalid kubeconfig" error when uploading

**Cause**: The file is not valid YAML or doesn't contain the expected kubeconfig structure.

**Check**:
- Open the file and verify it has `apiVersion: v1`, `kind: Config`, and at least one cluster/context/user entry.
- Make sure it's not a different YAML file (e.g., a deployment manifest).

### "It looks like you provided a console URL"

**Cause**: You entered a URL like `https://console-openshift-console.apps.cluster.example.com` instead of the API URL.

**Fix**: Use the API server URL format: `https://api.cluster.example.com:6443`

## Authentication Issues

### 401 error when trying to create/edit/delete

**Cause**: You're not signed in, or your session expired (browser tab was closed).

**Fix**: Click **Sign In** in the top-right corner and enter the admin credentials.

### "Invalid credentials" when signing in

**Cause**: Wrong username or password.

**Check**: The credentials are set via `ADMIN_USERNAME` and `ADMIN_PASSWORD` environment variables on the backend. On OCP, these are in the `psap-control-center-admin` secret.

**Verify** (on OCP):
```bash
oc get secret psap-control-center-admin -o jsonpath='{.data.ADMIN_USERNAME}' | base64 -d
oc get secret psap-control-center-admin -o jsonpath='{.data.ADMIN_PASSWORD}' | base64 -d
```

### Write operations work in view but API calls return 401

**Cause**: The `Authorization` header is not being sent. This can happen if credentials are stored but the Axios interceptor isn't attaching them.

**Fix**: Sign out and sign back in. If the issue persists, clear sessionStorage in your browser's dev tools and sign in again.

## OCP Deployment Issues

### Frontend pod in CrashLoopBackOff with "Permission denied"

**Cause**: The standard `nginx:alpine` image requires root. OCP runs containers as a random non-root user.

**Fix**: The Dockerfile should use `nginxinc/nginx-unprivileged:alpine` and listen on port 8080 instead of 80. This is already configured in the current codebase. If you see this error, rebuild:

```bash
oc start-build psap-control-center-frontend --from-dir=./frontend --follow
```

### Backend pod in ImagePullBackOff

**Cause**: The image hasn't been built yet, or the build failed.

**Check**:
```bash
oc get builds
oc logs build/psap-control-center-backend-1
```

**Fix**: Run the build:
```bash
oc start-build psap-control-center-backend --from-dir=./backend --follow
```

### Frontend shows "Application is not available"

**Cause**: The frontend pod isn't running, or the route isn't pointing to the right service.

**Check**:
```bash
oc get pods
oc get route psap-control-center
oc get svc psap-control-center-frontend
```

Make sure the service port matches the container port (8080) and the route points to the frontend service.

### Frontend loads but API calls fail (network errors)

**Cause**: The nginx reverse proxy can't reach the backend service.

**Check** the nginx.conf has the correct service name:
```nginx
proxy_pass http://psap-control-center-backend:8000;
```

**Verify** the backend service exists:
```bash
oc get svc psap-control-center-backend
```

If you changed the service name, rebuild the frontend so nginx picks up the new config.

### Browser shows strikethrough on HTTPS

**Cause**: The OCP cluster uses a self-signed certificate from its internal CA. Your browser doesn't trust it.

**This is normal** for internal/lab clusters. The connection is still encrypted. Click through the browser warning ("Advanced" > "Proceed"). This is not a security problem for an internal team tool.

## Reservation Issues

### "Time slot conflicts with..." error

**Cause**: Another reservation overlaps with your requested time on the same cluster.

**Fix**: Choose a different time slot or a different cluster. The error message shows the conflicting reservation's title, user, and time range.

### Reservation still shows "scheduled" after start time

**Cause**: The background status updater runs every 60 seconds. There may be a brief delay.

**Fix**: Wait up to 60 seconds and refresh the page. If it still doesn't update, check that the backend is running:
```bash
oc logs deployment/psap-control-center-backend | tail -20
```

### Reservations disappeared after cluster was deleted

**Cause**: When a cluster is removed, its active/scheduled reservations are cancelled and the `cluster_id` link is removed. However, reservations are preserved with the cluster name for historical records.

**Find them**: Filter reservations by the "cancelled" status. They'll have a note like "[Auto-cancelled: Cluster 'name' was removed from Control Center]".

## Hearth Issues

### Hearth shows "disconnected"

**Cause**: No management cluster kubeconfig is configured, or the saved kubeconfig has expired.

**Fix**: Click the Hearth indicator in the sidebar and upload a fresh kubeconfig for the management cluster.

### Hearth connected but no clusters listed

**Cause**: No `FournosCluster` CRDs exist in the Hearth namespace, or the namespace is wrong.

**Check**: The default namespace is `hearth`. Verify CRDs exist:
```bash
oc get fournosclusters -n hearth --kubeconfig=<management-kubeconfig>
```

## Logging

### Enabling debug logs

**Backend**: Set `LOG_LEVEL=DEBUG` in the environment and restart:
```bash
# Local
LOG_LEVEL=DEBUG uvicorn app.main:app --reload

# OCP
oc set env deployment/psap-control-center-backend LOG_LEVEL=DEBUG
```

**Frontend**: Set `VITE_LOG_LEVEL=DEBUG` in `frontend/.env` and restart the dev server. For production, this must be set at build time.

### Reading backend logs on OCP

```bash
# Live logs
oc logs -f deployment/psap-control-center-backend

# Last 100 lines
oc logs deployment/psap-control-center-backend --tail=100
```

Log format: `<datetime> <context>: <level> - <message>`

Example:
```
2026-05-27 09:04:44.769 Main: INFO - Starting up PSAP Control Center...
2026-05-27 09:04:44.772 KubernetesService: ERROR - Connection timeout
```
