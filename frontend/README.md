## Frontend Workspace

This folder contains the three independent frontend applications for InsureFlow.

### Frontends

- `user-frontend`: customer-facing experience
- `user-admin-frontend`: admin console for customer, transaction, payment, policy, ticket, and dashboard workflows
- `provider-admin-frontend`: provider-side admin console for providers, brokers, sync operations, and provider policy tooling

### Backend Alignment

- `user-frontend` -> main backend at `http://127.0.0.1:8000/api/v1`
- `user-admin-frontend` -> main backend at `http://127.0.0.1:8000/api/v1`
- `provider-admin-frontend` -> provider backend at `http://127.0.0.1:8001/api/v1`

### Recommended Commands

Run each app from the frontend workspace root:

```powershell
npm run dev:user
npm run dev:user-admin
npm run dev:provider-admin
```
