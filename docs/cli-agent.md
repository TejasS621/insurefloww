# InsureFlow CLI

Run the CLI with:

```powershell
python -m insureflow_cli --help
```

Common flows:

```powershell
python -m insureflow_cli auth customer-otp
python -m insureflow_cli auth customer-verify
python -m insureflow_cli quote generate
python -m insureflow_cli quote select
python -m insureflow_cli payment initiate
python -m insureflow_cli payment status
python -m insureflow_cli policy list
python -m insureflow_cli ticket create
python -m insureflow_cli auth admin-login
python -m insureflow_cli broker list
```

The CLI stores tokens in a local session file and uses the existing main backend APIs.
