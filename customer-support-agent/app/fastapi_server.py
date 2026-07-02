from fastapi import FastAPI, Request
import json
import datetime
import sys, os
# Ensure the app directory is in PYTHONPATH when run as a script
sys.path.append(os.path.dirname(__file__))
from agent import CustomerSupportAgent

app = FastAPI()


@app.post('/run')
async def run_workflow(req: Request):
    try:
        data = await req.json()
        if not data:
            # Empty payload – use mock demo data
            data = {
                "crm": [
                    {"account_name": "Acme Corp", "deal_stage": "Negotiation", "days_in_stage": 120, "last_contact_days_ago": 45},
                    {"account_name": "Initech", "deal_stage": "Proposal", "days_in_stage": 15, "last_contact_days_ago": 2}
                ],
                "invoices": [
                    {"invoice_id": "INV-1001", "customer": "Acme Corp", "amount": 50000.0, "status": "Overdue", "due_days_overdue": 90},
                    {"invoice_id": "INV-1002", "customer": "Initech", "amount": 12000.0, "status": "Paid", "due_days_overdue": 0}
                ],
                "customers": [
                    {"name": "Acme Corp", "support_tickets_open": 5, "satisfaction_score": 2.1, "contract_expiry": "2026-08-31"},
                    {"name": "Initech", "support_tickets_open": 0, "satisfaction_score": 4.8, "contract_expiry": "2027-12-31"}
                ],
                "transactions": [
                    {"transaction_id": "TXN-501", "customer": "Acme Corp", "type": "Subscription Renewal Payment", "status": "Failed", "amount": 50000.0}
                ],
                "notes": "Demo mock data for auto‑mock when empty"
            }
    except Exception:
        # malformed JSON or no body – fall back to mock data
        data = {
            "crm": [
                {"account_name": "Acme Corp", "deal_stage": "Negotiation", "days_in_stage": 120, "last_contact_days_ago": 45},
                {"account_name": "Initech", "deal_stage": "Proposal", "days_in_stage": 15, "last_contact_days_ago": 2}
            ],
            "invoices": [
                {"invoice_id": "INV-1001", "customer": "Acme Corp", "amount": 50000.0, "status": "Overdue", "due_days_overdue": 90},
                {"invoice_id": "INV-1002", "customer": "Initech", "amount": 12000.0, "status": "Paid", "due_days_overdue": 0}
            ],
            "customers": [
                {"name": "Acme Corp", "support_tickets_open": 5, "satisfaction_score": 2.1, "contract_expiry": "2026-08-31"},
                {"name": "Initech", "support_tickets_open": 0, "satisfaction_score": 4.8, "contract_expiry": "2027-12-31"}
            ],
            "transactions": [
                {"transaction_id": "TXN-501", "customer": "Acme Corp", "type": "Subscription Renewal Payment", "status": "Failed", "amount": 50000.0}
            ],
            "notes": "Demo mock data for auto‑mock when empty"
        }
    result = CustomerSupportAgent().run(data)
    try:
        analysis = json.loads(result)
    except Exception:
        analysis = {"raw": result}
    output = {
        "generated_at": datetime.datetime.now(datetime.UTC).replace(microsecond=0).isoformat() + "Z",
        "analysis": analysis
    }
    return {"result": output}


# ----------------------------------------------------------------------
# Launch script – runs the FastAPI server on a non‑conflicting port (8001)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    # Use a port that does not clash with the ADK UI (default 8000)
    uvicorn.run(app, host="0.0.0.0", port=8001)
