Reconciliation Microservice

This FastAPI microservice compares two Excel files and produces a reconciliation result.

Endpoints:
- POST /reconcile : returns JSON result using existing RRN/Refnum_F37 merge logic
- POST /reconcile/download : returns an Excel file with sheets: only_in_eth, only_in_zzb, matched_eth, matched_zzb

Run:

```powershell
cd back-end
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `front-end/index.html` in a browser to test.
