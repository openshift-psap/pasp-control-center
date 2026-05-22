# PASP Control Center

A comprehensive cluster management and reservation system for the Performance and Scale for AI Platforms (PSAP) team. This application provides observability into OCP cluster status, a reservation system with calendar views, and kubeconfig management capabilities.

## Features

### Current Features (Phase 1)
- **Cluster Management**: Add, monitor, and manage OCP clusters
- **Kubeconfig Upload**: Load kubeconfigs from the UI to connect new clusters
- **Cluster Health Monitoring**: Real-time status, node information, and resource usage
- **Reservation System**: Schedule cluster usage with conflict detection
- **Calendar Views**: Daily, weekly, and monthly views of cluster reservations
- **Current User Display**: See who is currently using each cluster

### Planned Features (Phase 2)
- **Automated Testing**: Configure and run performance benchmarks
- **Results Dashboard**: Integration with self-hosted MLFlow for experiment tracking

## Tech Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **Backend**: Python FastAPI, SQLAlchemy, Kubernetes client
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Deployment**: Docker, docker-compose

## Quick Start

### Prerequisites
- Docker and docker-compose
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/openshift-psap/pasp-control-center.git
cd pasp-control-center

# Copy environment file
cp .env.example .env

# Start the application
docker-compose up -d

# Access the UI at http://localhost:3000
# API docs at http://localhost:8000/docs
```

### Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT secret key | `change-in-production` |
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///./pasp_control_center.db` |
| `KUBECONFIG_STORAGE_PATH` | Path to store kubeconfigs | `./kubeconfigs` |
| `MLFLOW_BASE_URL` | MLFlow server URL (optional) | - |

### Adding Clusters

1. Navigate to the Clusters page
2. Click "Add Cluster"
3. Enter a name and optional description
4. Upload your kubeconfig file
5. The system will automatically connect and retrieve cluster information

## Architecture

```
pasp-control-center/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration, database
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom hooks
│   │   ├── services/       # API client
│   │   └── types/          # TypeScript types
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml       # Production compose
└── docker-compose.dev.yml   # Development compose
```

## API Documentation

Once the backend is running, access the interactive API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/clusters` | GET | List all clusters |
| `/api/v1/clusters` | POST | Add a new cluster |
| `/api/v1/clusters/{id}/refresh` | POST | Refresh cluster status |
| `/api/v1/reservations` | GET | List reservations |
| `/api/v1/reservations` | POST | Create a reservation |
| `/api/v1/reservations/calendar` | GET | Get calendar events |

## GitHub Repository Setup

To push this repository to the openshift-psap organization:

```bash
# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: PASP Control Center

- Cluster management with kubeconfig upload
- Reservation system with calendar views
- Modern React + FastAPI architecture
- Docker deployment support"

# Add remote (requires access to openshift-psap org)
git remote add origin https://github.com/openshift-psap/pasp-control-center.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Security

- Kubeconfigs are stored with restricted permissions (0600)
- Never commit kubeconfig files to the repository
- Use environment variables for sensitive configuration
- The `.gitignore` excludes sensitive files by default

## License

Apache License 2.0

## Related Projects

- [TOPSAIL](https://github.com/openshift-psap/topsail) - Test Orchestrator for Performance and Scalability of AI pLatforms
- [Performance Dashboard](https://github.com/openshift-psap/performance-dashboard) - RHAIIS benchmark analysis
- [Auto-tuning vLLM](https://github.com/openshift-psap/auto-tuning-vllm) - LLM deployment optimization
