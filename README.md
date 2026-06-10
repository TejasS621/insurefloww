# InsureFloww

This folder is currently a clean project scaffold for the new InsureFloww rebuild.

The structure combines:

- the target product architecture from the current planning docs
- the layered FastAPI organization from the referenced tutorial
- separate service boundaries for `main_backend` and `provider_backend`

## Current Structure

```txt
InsureFloww/
  backend/
    main_backend/
      app/
        commons/
        core/
          apis/
            routes/
            schemas/
              requests/
              responses/
          controllers/
          cruds/
          database/
          models/
            shared/
          providers/
          services/
          utils/
            emails/
    provider_backend/
      app/
        commons/
        core/
          apis/
            routes/
            schemas/
              requests/
              responses/
          controllers/
          cruds/
          database/
          events/
          models/
            shared/
          services/
          utils/
            emails/
  frontend/
    public/
    src/
      assets/
      components/
        ui/
      pages/
        landing/
        auth/
        application/
        quotes/
        payment/
        policy/
        dashboard/
        profile/
        admin/
      services/
      store/
      utils/
  docs/
    adr/
    architecture/
    postman/
    reference/
  scripts/
```

## Docs

- [Architecture Notes](C:\InsureFloww\docs\architecture\DOCUMENTATION.md)
- [Implementation Plan](C:\InsureFloww\docs\architecture\IMPLEMENTATION_PLAN.md)
- [ADR Notes](C:\InsureFloww\docs\adr\ADR.md)
- [ADR Index](C:\InsureFloww\docs\adr\README.md)

## Status

Only the folder structure and documentation layout are in place right now.
No old application code has been migrated into this scaffold.
