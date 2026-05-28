# Contributing to PSAP Control Center

## Branch Protection

The `main` branch is protected. All changes must go through a pull request with at least one approval.

## Workflow

1. **Create a branch** from `main`:

   ```bash
   git checkout main
   git pull
   git checkout -b your-branch-name
   ```

2. **Make your changes** and commit:

   ```bash
   git add -A
   git commit -m "feat: short description of the change"
   ```

3. **Push your branch**:

   ```bash
   git push -u origin your-branch-name
   ```

4. **Open a Pull Request** on GitHub:

   ```bash
   gh pr create --title "Your PR title" --body "Description of changes"
   ```

   Or use the link GitHub prints after pushing.

5. **Get a review** — at least one team member must approve.

6. **Merge** — once approved, merge via GitHub. Delete the branch after merging.

## Commit Messages

Use the conventional format:

```
<type>: <short description>
```

Types:

| Type       | When to use                                    |
| ---------- | ---------------------------------------------- |
| `feat`     | New feature or capability                      |
| `fix`      | Bug fix                                        |
| `docs`     | Documentation only                             |
| `refactor` | Code change that doesn't fix a bug or add a feature |
| `style`    | Formatting, whitespace, lint fixes             |
| `test`     | Adding or updating tests                       |
| `chore`    | Build process, dependencies, CI                |

Examples:

```
feat: add Hearth GPU discovery to dashboard
fix: resolve token expiration on cluster refresh
docs: update deployment guide for OCP 4.16
refactor: extract reservation conflict logic into utility
```

## Development Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
ADMIN_USERNAME=admin ADMIN_PASSWORD=admin \
  uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server runs on port 3000 and proxies `/api` requests to the backend on port 8000.

### Type Checking

```bash
# Backend (Python syntax)
cd backend
python -m py_compile app/main.py

# Frontend (TypeScript)
cd frontend
npx tsc --noEmit --skipLibCheck
```

## Code Standards

### Backend (Python)

- Follow PEP 8 (79 char line limit)
- Use the project's structured logger, not `print()` or `logging.getLogger()`:

  ```python
  from app.utils.logger import create_logger
  logger = create_logger("YourModule")
  logger.info("Something happened:", some_data)
  ```

- Use async/await for all database operations
- Add `Depends(require_auth)` to any new write endpoint

### Frontend (TypeScript)

- Use the project's logger, not `console.log()`:

  ```typescript
  import { createLogger } from '../utils/logger'
  const logger = createLogger('YourComponent')
  logger.info('Something happened:', data)
  ```

- Use TanStack Query hooks for data fetching (see `hooks/` directory for patterns)
- Use Tailwind CSS for styling — avoid inline styles or CSS modules

## Project Structure

```
backend/app/
├── api/           # Route handlers (thin — delegate to services)
├── core/          # Config, database, auth
├── models/        # SQLAlchemy ORM models
├── schemas/       # Pydantic request/response DTOs
├── services/      # Business logic
└── utils/         # Logger and shared utilities

frontend/src/
├── components/    # Reusable UI components
├── pages/         # Route-level page components
├── hooks/         # TanStack Query hooks (data fetching + mutations)
├── services/      # Axios API client
├── stores/        # State management (auth)
├── types/         # Shared TypeScript interfaces
└── utils/         # Logger and shared utilities
```

## Adding a New Feature

Typical flow for a new backend feature:

1. Add/update the **model** in `models/`
2. Add **schemas** in `schemas/`
3. Add **service logic** in `services/`
4. Add **API routes** in `api/` (with `require_auth` on write endpoints)
5. Register the router in `api/__init__.py`

Typical flow for the corresponding frontend work:

1. Add **types** in `types/index.ts`
2. Add **API functions** in `services/api.ts`
3. Add **hooks** in `hooks/`
4. Add/update **page or component** in `pages/` or `components/`

## Deploying Changes to OCP

After your PR is merged to `main`:

```bash
git checkout main && git pull

# Rebuild whichever changed
oc start-build psap-control-center-backend --from-dir=./backend --follow
oc start-build psap-control-center-frontend --from-dir=./frontend --follow
```

Pods restart automatically with the new images. See [deploy/README.md](../deploy/README.md) for the full deployment guide.
