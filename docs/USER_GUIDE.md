# PSAP Control Center — User Guide

## Accessing the Application

Open the Control Center in your browser:

**Production (OCP)**: https://control-center.apps.psap-automation.ibm.rhperfscale.org

**Local development**: http://localhost:3000

You can browse everything without signing in. To make changes (add clusters, create reservations, etc.), click **Sign In** in the top-right corner.

## Signing In

1. Click the **Sign In** button in the header
2. Enter the admin username and password
3. Click **Sign In**

Once authenticated, the header shows your username and a **Sign Out** button. Your session lasts until you close the browser tab.

## Dashboard

The Dashboard gives you an overview of:

- **Cluster stats** — total clusters, healthy count, total GPUs, active reservations
- **Active Reservations** — currently in-use clusters with user details and time remaining
- **Upcoming Reservations** — scheduled for the next 7 days
- **Past Reservations** — completed and cancelled from the last 30 days
- **Hearth GPU Inventory** — GPU types and counts from connected Hearth clusters (if configured)

## Managing Clusters

### Adding a Cluster

1. Go to **Clusters** in the sidebar
2. Click **Add Cluster**
3. Enter a **name** and optional **description**
4. Choose one of two connection methods:

**Kubeconfig Upload:**
- Select the **Kubeconfig** tab
- Drag and drop your kubeconfig file or click to browse
- The file is validated before saving

**Kubeadmin Credentials:**
- Select the **Credentials** tab
- Enter the **API server URL** (e.g., `https://api.cluster.example.com:6443`)
- Enter the **username** (usually `kubeadmin`) and **password**
- The system authenticates via OAuth and creates a service account for persistent access

5. Click **Add Cluster**

The cluster appears in the grid with a health status check running automatically.

### Viewing Cluster Details

Click any cluster card to see:

- **Topology** — visual map of control plane, worker, and infrastructure nodes with GPU details
- **OCP Details** — OpenShift version, platform, network type, ingress domain, available updates
- **Operators** — installed OLM operators and their status
- **Workloads** — running pods and deployments (filterable by namespace)
- **Current User** — who has the cluster reserved right now

Click any node in the topology view to see detailed specs (CPU, memory, GPU type, OS, kubelet version, IPs).

### Refreshing Cluster Status

On the cluster detail page, click **Refresh** to pull live data from the Kubernetes API. Status also auto-refreshes every 60 seconds.

### Removing a Cluster

1. Go to **Clusters**
2. Click the trash icon on the cluster card
3. Confirm the deletion

This does **not** affect the actual cluster — it only removes it from the Control Center. Any active or scheduled reservations for that cluster are automatically cancelled with a note.

## Managing Reservations

### Creating a Reservation

1. Go to **Reservations** in the sidebar
2. Click **New Reservation**
3. Fill in:
   - **Cluster** — select from the dropdown
   - **Title** — what you're doing (e.g., "vLLM benchmark run")
   - **Your Name** and **Email**
   - **Team** (optional)
   - **Start Time** and **End Time**
   - **Purpose** (optional — testing, development, demo, etc.)
   - **Notes** (optional)
4. Click **Create**

If the time slot conflicts with an existing reservation on that cluster, you'll see an error message with the conflicting reservation's details.

### Editing a Reservation

1. Click on a reservation in the list
2. Modify the fields
3. Click **Save**

Time changes are re-checked for conflicts.

### Cancelling a Reservation

1. Find the reservation in the list
2. Click **Cancel**
3. The reservation moves to "Cancelled" status with a timestamp

Cancelled reservations are preserved for historical records.

### Reservation Statuses

| Status    | Meaning |
| --------- | ------- |
| Scheduled | Reserved for a future time |
| Active    | Currently in use (start time has passed, end time hasn't) |
| Completed | End time has passed |
| Cancelled | Manually cancelled or auto-cancelled (cluster removed) |

Status transitions happen automatically in the background every 60 seconds.

## Calendar

### Reservations Page Calendar

The mini weekly calendar at the top of the Reservations page shows hourly slots from 6 AM to 10 PM. Each cluster's reservations are color-coded. Overlapping reservations on different clusters show split views with count badges.

### Full Calendar Page

Go to **Calendar** in the sidebar for month, week, or day views. Use the **cluster filter** dropdown to show reservations for specific clusters.

Reservation colors match their cluster's assigned color for easy identification.

## Hearth Integration

Hearth provides GPU inventory discovery from a management cluster running the Hearth operator.

### Connecting Hearth

1. Click the **Hearth** indicator in the sidebar (or the connect prompt on the Dashboard)
2. Upload the kubeconfig for the Hearth management cluster
3. Once connected, GPU inventory appears on the Dashboard and cluster detail pages

### What Hearth Shows

- **Dashboard** — table of all Hearth-discovered clusters with GPU types and counts
- **Cluster Detail** — if a cluster name matches a Hearth cluster, you'll see its lock status, GPU hardware, and kubeconfig validity

### Disconnecting Hearth

Click the Hearth indicator in the sidebar and choose **Disconnect**. This removes the management cluster kubeconfig. Cluster data in the Control Center is not affected.

## Tips

- **Colors are automatic** — each cluster gets a unique color from a palette. Reservations inherit their cluster's color.
- **Bookmarks** — cluster detail pages have stable URLs (`/clusters/{id}`), so you can bookmark frequently used clusters.
- **API docs** — developers can access the full API at `/docs` (Swagger UI) for scripting or automation.
- **View-only by default** — share the URL with anyone on the team. They can browse without needing credentials.
