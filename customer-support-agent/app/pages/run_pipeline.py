import streamlit as st
import json
from typing import Any, Dict, List
from app.agent import CustomerSupportAgent

def run_pipeline_page():
    """Page that runs the agent on a provided payload and shows live trace."""
    st.header("🚀 Run Pipeline")
    st.caption("Upload a JSON payload and execute the revenue risk agent with real‑time trace logs.")

    # Input method
    input_method = st.radio("Select input method", ["File upload", "Raw JSON text"]) 
    payload: Dict[str, Any] = {}
    if input_method == "File upload":
        uploaded = st.file_uploader("Choose a JSON file", type=["json"])
        if uploaded:
            content = uploaded.getvalue().decode("utf-8")
            try:
                payload = json.loads(content)
                st.success("✅ Payload loaded")
            except Exception as e:
                st.error(f"Failed to parse JSON: {e}")
    else:
        raw = st.text_area("Paste JSON payload here", height=200)
        if raw:
            try:
                payload = json.loads(raw)
                st.success("✅ Payload loaded")
            except Exception as e:
                st.error(f"Invalid JSON: {e}")

    if payload:
        if st.button("Run Analysis", type="primary"):
            status = st.empty()
            progress = st.progress(0)
            status.info("🔧 Starting analysis…")
            agent = CustomerSupportAgent()
            result_str, trace = agent.run_with_trace(payload)
            status.success("✅ Analysis completed")
            progress.progress(100)

            st.subheader("📝 Execution Trace")
            for i, ev in enumerate(trace, 1):
                st.code(ev, language="text")

            st.subheader("🔎 Raw Output")
            try:
                result = json.loads(result_str)
            except Exception:
                result = {"raw": result_str}
            st.json(result)

            st.download_button(
                label="Download JSON result",
                data=json.dumps(result, indent=2),
                file_name="risk_analysis_result.json",
                mime="application/json",
            )
