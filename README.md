# InsureFloww

InsureFloww is a broker-led insurance platform with:

- `backend/main_backend` for customer, admin, payment, policy, and ticket APIs
- `backend/provider_backend` for quote generation, provider payments, and provider sync flows
- `frontend` for the customer and admin UI

## Local Setup

1. Make sure MongoDB is running on `mongodb://localhost:27017/`.
2. Use the root `.env` file for backend settings.
3. Optionally copy `frontend/.env.example` into `frontend/.env` if you want to override the default API base URL.

## Local Startup Order

1. Start the provider backend:
   `powershell -ExecutionPolicy Bypass -File .\scripts\start-provider-backend.ps1`
2. Start the main backend:
   `powershell -ExecutionPolicy Bypass -File .\scripts\start-main-backend.ps1`
3. Start the frontend:
   `powershell -ExecutionPolicy Bypass -File .\scripts\start-frontend.ps1`

## Key Local URLs

- Frontend: `http://127.0.0.1:5173`
- Main backend docs: `http://127.0.0.1:8000/docs`
- Provider backend docs: `http://127.0.0.1:8001/docs`

## Reference Docs

- [Architecture Notes](C:/InsureFloww/docs/architecture/DOCUMENTATION.md)
- [Implementation Plan](C:/InsureFloww/docs/architecture/IMPLEMENTATION_PLAN.md)
- [ADR Notes](C:/InsureFloww/docs/adr/ADR.md)
- [ADR Index](C:/InsureFloww/docs/adr/README.md)
