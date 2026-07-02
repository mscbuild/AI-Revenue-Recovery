import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
import os
from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("customer_support_mcp")

# ---------- Tool definitions ----------

@mcp.tool()
def get_customer_overview(customer_name: str) -> str:
    """Return a JSON string with basic info for a given customer.
    Used by the revenue analyst workflow to fetch details without re‑parsing the full payload.
    """
    try:
        with open("data/customers.json", "r", encoding="utf-8") as f:
            customers = json.load(f)
        record = next((c for c in customers if c.get("name") == customer_name), None)
        if not record:
            return json.dumps({"error": "Customer not found"})
        return json.dumps(record)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def list_overdue_invoices(days_threshold: int = 30) -> List[Dict[str, Any]]:
    """Return a list of invoices that are overdue for more than *days_threshold* days.
    The revenue analyst uses this to prioritize collection risks.
    """
    try:
        with open("data/invoices.json", "r", encoding="utf-8") as f:
            invoices = json.load(f)
        overdue = [inv for inv in invoices if inv.get("status") == "Overdue" and inv.get("due_days_overdue", 0) >= days_threshold]
        return overdue
    except Exception as e:
        return [{"error": str(e)}]

@mcp.tool()
def summarize_transactions(customer_name: str) -> str:
    """Provide a short summary of recent transactions for *customer_name*.
    Returns a plain‑text paragraph ready to be injected into a prompt.
    """
    try:
        with open("data/transactions.json", "r", encoding="utf-8") as f:
            txns = json.load(f)
        cust_txns = [t for t in txns if t.get("customer") == customer_name]
        if not cust_txns:
            return f"No transactions found for {customer_name}."
        lines = [f"{t['transaction_id']}: {t['type']} ({t['status']}) – ${t['amount']}" for t in cust_txns]
        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving transactions: {e}"

if __name__ == "__main__":
    # Configuration from environment variables
    host = os.getenv("CRM_SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("CRM_SERVER_PORT", "8001"))
    transport = os.getenv("CRM_SERVER_TRANSPORT", "sse")
    mcp.run(transport=transport, host=host, port=port)
