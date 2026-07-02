import json
import pandas as pd
import streamlit as st
import plotly.express as px
from typing import Any, Dict, List
from app.agent import CustomerSupportAgent

def run_analysis_page():
    """Original analysis page (now a separate module)."""
    st.set_page_config(page_title="Revenue Risk Dashboard", layout="centered")
    st.title("📊 Revenue Risk Analysis Dashboard")
    st.caption("Upload a JSON payload or paste raw JSON to run the agent.")

    # Input method selection
    input_method = st.radio("Select input method", ("File upload", "Raw JSON text"))
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

            st.subheader("🔎 Raw Output")
            try:
                result = json.loads(result_str)
            except Exception:
                result = {"raw": result_str}
            st.json(result)

            with st.expander("📝 Execution Trace (ADK events)"):
                for ev in trace:
                    st.code(ev, language="text")

            # Risks handling
            risks: List[dict] = []
            if isinstance(result, dict) and "analysis" in result:
                analysis = result["analysis"]
                if isinstance(analysis, list):
                    risks = analysis
                elif isinstance(analysis, dict):
                    if isinstance(analysis.get("risks"), list):
                        risks = analysis["risks"]
                    else:
                        risks = [analysis]
            if risks:
                df = pd.DataFrame(risks)
                if not df.empty:
                    # Styled table
                    st.subheader("📊 Risks Table")
                    def style_sev(row):
                        color = "#d9ead3"
                        if row.get("risk_assessment") == "Medium":
                            color = "#fff2cc"
                        elif row.get("risk_assessment") == "High":
                            color = "#ffcccc"
                        return [f"background-color: {color}"] * len(row)
                    st.dataframe(df.style.apply(style_sev, axis=1))

                    # Plotly charts
                    if "risk_assessment" in df.columns:
                        severity = df["risk_assessment"].value_counts().reset_index()
                        severity.columns = ["Severity", "Count"]
                        fig_bar = px.bar(severity, x="Severity", y="Count", color="Severity",
                                         color_discrete_map={"Low": "#56c870", "Medium": "#f0c808", "High": "#f04747"},
                                         title="Risk Severity Distribution")
                        st.plotly_chart(fig_bar, use_container_width=True)
                        fig_pie = px.pie(severity, names="Severity", values="Count",
                                         color="Severity", title="Severity Share",
                                         color_discrete_map={"Low": "#56c870", "Medium": "#f0c808", "High": "#f04747"})
                        st.plotly_chart(fig_pie, use_container_width=True)
            st.download_button(label="Download JSON result",
                               data=json.dumps(result, indent=2),
                               file_name="risk_analysis_result.json",
                               mime="application/json")
    else:
        st.info("Provide a JSON payload to start analysis.")
