import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from google import genai 

# ==========================================
#1. PAGE SETUP AND AI INITIALIZATION
# ==========================================
st.set_page_config(page_title="AI Revenue Agent Dashboard", layout="wide")
st.title("📊 Transaction and Account Analytics with AI Agent")

# Hide the top navigation bar of the multi-page mode
st.markdown("""
    <style>
        /* Hides the top panel with the list of pages */
        [data-testid="stSidebarNav"] {display: None;}
        header {visibility: hidden;}
        .stAppDeployButton {display: none;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    # Logo / branding
    st.markdown("### 🤖 Revenue Recovery Agent")
    st.divider()

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")

if GEMINI_KEY:
    # We use the current Client class to work with Google models
    ai_client = genai.Client(api_key=GEMINI_KEY)
else:
    ai_client = None
# ==========================================
# 2. ENGINE FUNCTIONS (MAIN REASONING ENGINE)
# ==========================================
def calculate_deal_impact(row):
    """Business rule for deals (>14 days without activity)"""
    days = row['last_activity_days']
    amount = row['value']
    if days <= 14:
        return 0.0, 0.0
    
    base_prob = 0.5
    if 'contract' in str(row['stage']).lower():
        base_prob = 0.8
    elif 'demo' in str(row['stage']).lower():
        base_prob = 0.4
        
    decay_factor = 0.8 if days <= 30 else 0.5
    current_prob = base_prob * decay_factor
    impact = amount * (base_prob - current_prob)
    priority_score = impact / 2
    return round(impact, 2), round(priority_score, 2)

def calculate_invoice_impact(row):
    """Business rule for invoices (>30 days overdue)"""
    days = row['days_overdue']
    amount = row['amount']
    if days <= 30 or str(row['status']).lower() == 'paid':
        return 0.0, 0.0
    
    impact = amount * 1.02  # Amount + 2% value of frozen capital
    priority_score = impact / 1
    return round(impact, 2), round(priority_score, 2)

def get_ai_explanation(item_name, item_type, impact, days, owner, stage_or_status):
    """Explainability block: AI or quality plug-in template"""
    if ai_client:
        try:
            prompt = f"""
            You are an autonomous business risk analyst. Explain the vulnerability to the commercial director.
            Object type: {item_type} ({item_name})
            Responsible: {owner}
            Status/Stage: {stage_or_status}
            Financial damage (Impact): ${impact}
            Delay duration: {days} days.
            Write your answer strictly in English, briefly (3 sentences) in the format: [Problem] -> [Why the priority dropped] -> [What specifically to do].
            """
            response = ai_client.chat.completions.create(
                model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], temperature=0.3
            )
            return response.choices.message.content
        except Exception:
            pass

    if "Deal" in item_type:
        return f"**[Problem]:** Deal '{item_name}' hung without activity on {days} days. **[Why the risk arose]:** At the stage '{stage_or_status}' The estimated probability of closure has decreased. Financial risk of lost profits: ${impact:,.2f}. **[Recommendation]:** To the Manager ({owner}) need to send personalized follow-up."
    else:
        return f"**[Problem]:** An overdue account has been detected '{item_name}' on {days} days. **[Why the risk arose]:** Payment delay status '{stage_or_status}' creates a threat of cash flow shortfall. Financial impact: ${impact:,.2f}. **[Recommendation]:** Send the client a formal claim for debt."
# ==========================================
# 3. DATA LOADING AND FILTERING
# ==========================================
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path):
        st.error(f"File {file_path} Not found! Please create it.")
        st.stop()
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    df_d = pd.json_normalize(data, record_path=['deals'])
    df_i = pd.json_normalize(data, record_path=['invoices'])
    return df_d, df_i

# Load raw data from JSON
df_deals, df_invoices = load_data("data.json")

# Enriching data with risk calculations before filtering
df_deals['revenue_risk'] = df_deals.apply(lambda r: calculate_deal_impact(r)[0], axis=1)
df_deals['priority_score'] = df_deals.apply(lambda r: calculate_deal_impact(r)[1], axis=1)

df_invoices['cash_risk'] = df_invoices.apply(lambda r: calculate_invoice_impact(r)[0], axis=1)
df_invoices['priority_score'] = df_invoices.apply(lambda r: calculate_invoice_impact(r)[1], axis=1)

# Filters side menu
st.sidebar.header("Data filters")
all_customers = sorted(list(set(df_deals['customer'].unique()) | set(df_invoices['customer'].unique())))
selected_customers = st.sidebar.multiselect("Select clients:", options=all_customers, default=all_customers)

# Apply user filters
df_deals_filtered = df_deals[df_deals['customer'].isin(selected_customers)]
df_invoices_filtered = df_invoices[df_invoices['customer'].isin(selected_customers)]

# ==========================================
# 4. AGENT'S SUMMARY FINANCIAL METRICS
# ==========================================
st.markdown("### 🎯 AI Agent Risk & Revenue Assessment")
m_col1, m_col2, m_col3, m_col4 = st.columns(4)

total_pipeline_risk = df_deals_filtered['revenue_risk'].sum()
total_cash_risk = df_invoices_filtered['cash_risk'].sum()
critical_deals_count = len(df_deals_filtered[df_deals_filtered['last_activity_days'] > 14])
critical_inv_count = len(df_invoices_filtered[df_invoices_filtered['days_overdue'] > 30])

with m_col1:
    st.metric("Revenue at Risk (Pending trades >14 days)", f"${total_pipeline_risk:,.2f}", 
              delta=f"{critical_deals_count} deals at risk" if critical_deals_count > 0 else None, delta_color="inverse")
with m_col2:
    st.metric("Cash Flow at Risk (Overdue >30 days)", f"${total_cash_risk:,.2f}", 
              delta=f"{critical_inv_count} accounts are critical" if critical_inv_count > 0 else None, delta_color="inverse")
with m_col3:
    st.metric("Total Amount of Transactions", f"${df_deals_filtered['value'].sum():,}")
with m_col4:
    st.metric("Amount of Invoices Issued", f"${df_invoices_filtered['amount'].sum():,}")

st.divider()

# Initialize the state for the sidebar so that clicking on buttons doesn't reset focus
if "selected_entity" not in st.session_state:
    st.session_state.selected_entity = None

# ==========================================
# 5. DRAWING TABS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["💼 Deal Funnel", "🧾 Account Analysis", "🚀 Run Pipeline", "💰 Risk Scoring"])

# --- TAB 1: TRANSACTIONS ---
with tab1:
    st.header("Analysis of current transactions")
    if df_deals_filtered.empty:
        st.warning("No data available for selected clients.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            fig_deals_bar = px.bar(df_deals_filtered, x="customer", y="value", color="stage", title="Transaction value by client")
            st.plotly_chart(fig_deals_bar, use_container_width=True)
        with col2:
            fig_deals_scatter = px.scatter(df_deals_filtered, x="last_activity_days", y="value", size="value", color="customer", title="Transaction activity")
            st.plotly_chart(fig_deals_scatter, use_container_width=True)

        st.write("### Table of transactions (Select a row for detailed AI analysis)")
        deals_to_display = df_deals_filtered.sort_values(by="priority_score", ascending=False)
        select_deal_event = st.dataframe(
            deals_to_display[["customer", "stage", "value", "last_activity_days", "revenue_risk", "priority_score"]], 
            use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row"
        )
        if select_deal_event and len(select_deal_event.selection.rows) > 0:
            row_idx = select_deal_event.selection.rows[0]
            st.session_state.selected_entity = {
                "data": deals_to_display.iloc[row_idx],
                "type": "Deal Risk Analysis (Stalled > 14 days)",
                "name": deals_to_display.iloc[row_idx]["customer"],
                "days": deals_to_display.iloc[row_idx]["last_activity_days"],
                "impact": deals_to_display.iloc[row_idx]["revenue_risk"],
                "owner": "Responsible CRM Manager",
                "status": deals_to_display.iloc[row_idx]["stage"]
            }

# --- TAB 2: INVOICES (YOUR CORRECTED CODE SNAP) ---
with tab2:
    st.header("Accounts receivable control")
    if df_invoices_filtered.empty:
        st.warning("No data available for selected clients.")
    else:
        overdue_critical = df_invoices_filtered[df_invoices_filtered['days_overdue'] > 15]
        if not overdue_critical.empty:
            st.error(f"🚨 WARNING: Detected {len(overdue_critical)} invoices overdue for more than 15 days!")
            
        fig_inv_bar = px.bar(df_invoices_filtered, x="customer", y="days_overdue", color="status", title="Days overdue")
        st.plotly_chart(fig_inv_bar, use_container_width=True)

        st.write("### Table of accounts (Select a row for detailed AI analysis)")
        invoices_to_display = df_invoices_filtered.sort_values(by="priority_score", ascending=False)

        def highlight_overdue(row):
            return ['background-color: #ffcccc; color: #000000;' if row['days_overdue'] > 15 else '' for _ in row]

        styled_invoices = invoices_to_display[["customer", "amount", "status", "days_overdue", "cash_risk", "priority_score"]].style.apply(highlight_overdue, axis=1)

        select_inv_event = st.dataframe(
            styled_invoices, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row"
        )

        if select_inv_event and len(select_inv_event.selection.rows) > 0:
            row_idx = select_inv_event.selection.rows[0]
            st.session_state.selected_entity = {
                "data": invoices_to_display.iloc[row_idx],
                "type": "Invoice Overdue Analysis (Overdue > 30 days)",
                "name": f"Invoice for {invoices_to_display.iloc[row_idx]['customer']}",
                "days": invoices_to_display.iloc[row_idx]["days_overdue"],
                "impact": invoices_to_display.iloc[row_idx]["cash_risk"],
                "owner": "Financial Controller",
                "status": invoices_to_display.iloc[row_idx]["status"]
                }

# --- TAB 3: INVOICES (YOUR CORRECTED CODE SNAP) ---
with tab3:
    st.header("Run Pipeline")
    if df_invoices_filtered.empty:
        st.warning("No data available for selected clients.")
         # ── Input Form ────────────────────────────────────────────────────────────
    col1, col2 = st.columns([3, 1])
    with col1:
        # Main company input — accepts comma-separated list
        companies_input = st.text_input(
            "Enter company names (comma separated)",
            placeholder="e.g. BlueOrbit, GreenEdge, TechNova",
            help="The pipeline will research each company individually.",
        )
    with col2:
        # Auto-approve toggle — passes --auto-approve flag to main.py
        auto_approve = st.toggle(
            "Auto-approve outreach",
            value=False,
            help="If ON, skips the human review step and saves all drafts automatically.",
        )
        # Optional: fast mode skips Gemini API for outreach drafting
    fast_mode = st.checkbox(
        "⚡ Fast mode (template-based drafts, no API calls for outreach)",
        value=False,
        help="Uses pre-written templates for email/LinkedIn drafts. Much faster.",
    )

    run_btn = st.button("🚀 Run Pipeline", type="primary", use_container_width=True)

    # --- TAB 4: RISK SCORING (FULL CORRECTED CODE) ---
with tab4:
    st.header("Risk Scoring & Management Dashboard")
    
    if df_deals_filtered.empty:
        st.warning("No data available for selected clients.")
    else:
        # In Pandas 2.0+, it is recommended to make a copy to avoid SettingWithCopyWarning
        df_deals_filtered = df_deals_filtered.copy()

        # ---------------------------------------------------------------------
        # 1. Automatic Risk Calculation (KeyError Protection)
        # ---------------------------------------------------------------------
        
        # Calculate risk_score based on days of inactivity (each day = 4 points, max 100)
        # For TechNova (21 days) it will be 84, for BlueOrbit (5 days) = 20
        if "risk_score" not in df_deals_filtered.columns:
            df_deals_filtered["risk_score"] = (df_deals_filtered["last_activity_days"] * 4).clip(upper=100)
            
        # Categorization of risk levels
        if "risk_level" not in df_deals_filtered.columns:
            def assign_risk_level(score):
                if score > 70: return "Critical"
                elif score > 30: return "Medium"
                return "Low"
            df_deals_filtered["risk_level"] = df_deals_filtered["risk_score"].apply(assign_risk_level)

        # Automatic AI status generation
        if "ai_status" not in df_deals_filtered.columns:
            df_deals_filtered["ai_status"] = df_deals_filtered["risk_level"].map({
                "Critical": "Freeze Sales / Urgent Contact",
                "Medium": "Planned follow-up on the proposal",
                "Low": "Active Development / Call"
            })

        # Stub for information about overdue (if the data is not pulled from the Invoices tab)
        if "overdue_info" not in df_deals_filtered.columns:
            df_deals_filtered["overdue_info"] = "Control according to regulations"

        # ---------------------------------------------------------------------
        # 2. METRICS CALCULATION BLOCK % REVENUE AT RISK
        # ---------------------------------------------------------------------
        total_pipeline = df_deals_filtered["value"].sum()
        
        # Filtering trades with medium and critical risk
        deals_at_risk = df_deals_filtered[df_deals_filtered["risk_level"].isin(["Critical", "Medium"])]
        revenue_at_risk = deals_at_risk["value"].sum()
        
        # Calculating the final percentage of the risk pipeline
        pct_revenue_at_risk = (revenue_at_risk / total_pipeline * 100) if total_pipeline > 0 else 0
        
        # Drawing KPI cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                label="Total Pipeline Value", 
                value=f"${total_pipeline:,.2f}"
            )
        with col2:
            st.metric(
                label="Revenue at Risk (Critical/Medium)", 
                value=f"${revenue_at_risk:,.2f}",
                delta=f"{len(deals_at_risk)} deals",
                delta_color="inverse"
            )
        with col3:
            risk_status = "🚨" if pct_revenue_at_risk > 20 else "⚠️" if pct_revenue_at_risk > 10 else "🟢"
            st.metric(
                label=f"{risk_status} % Revenue at Risk", 
                value=f"{pct_revenue_at_risk:.1f}%",
                help="Percentage of revenue from medium and critical risk transactions to the entire pipeline"
            )
            
        st.markdown("---") 

        # ---------------------------------------------------------------------
        # 3. ALERTS AND SCHEDULE CONSTRUCTION
        # ---------------------------------------------------------------------
        critical_risks = df_deals_filtered[df_deals_filtered['risk_score'] > 70]
        if not critical_risks.empty:
            st.error(f"🚨 CRITICAL WARNING: Detected {len(critical_risks)} clients with extreme risk scores (>70)!")

        # Risk Distribution Bar Chart
        fig_risk_bar = px.bar(
            df_deals_filtered, 
            x="customer", 
            y="risk_score", 
            color="risk_level", 
            title="Client Risk Index Distribution",
            color_discrete_map={"Critical": "#ff4b4b", "Medium": "#ffaa00", "Low": "#00b050"}
        )
        st.plotly_chart(fig_risk_bar, use_container_width=True)

        # ---------------------------------------------------------------------
        # 4. INTERACTIVE TABLE WITH ROW SELECT
        # ---------------------------------------------------------------------
        st.write("### Consolidated Risk Report (Select a row for detailed AI analysis)")
        risks_to_display = df_deals_filtered.sort_values(by="risk_score", ascending=False)

        # Highlighting high-risk lines
        def highlight_critical_risks(row):
            return ['background-color: #ffcccc; color: #000000;' if row['risk_score'] > 70 else '' for _ in row]

        styled_risks = risks_to_display[
            ["customer", "stage", "value", "last_activity_days", "overdue_info", "risk_level", "risk_score", "ai_status"]
        ].style.apply(highlight_critical_risks, axis=1)

        # Displaying a dataframe with a click event
        select_risk_event = st.dataframe(
            styled_risks, 
            use_container_width=True, 
            hide_index=True, 
            on_select="rerun", 
            selection_mode="single-row"
        )

        # Writing selected data to the session state for the AI ​​agent
        if select_risk_event and len(select_risk_event.selection.rows) > 0:
            row_idx = select_risk_event.selection.rows[0] # Исправлено: извлекаем первый элемент списка
            selected_row = risks_to_display.iloc[row_idx]
            
            st.session_state.selected_entity = {
                "data": selected_row,
                "type": "AI Risk Scoring Analysis (0-100)",
                "name": f"Risk Profile for {selected_row['customer']}",
                "days": selected_row["last_activity_days"],
                "impact": selected_row["value"],
                "owner": "Account Executive / Risk Manager",
                "status": selected_row["ai_status"]
            }
            
            # Visual confirmation of choice for the user
            st.success(f"Selected: **{selected_row['customer']}** (Risk Score: {selected_row['risk_score']}). AI Agent is analyzing...")
# ==========================================
# 6. DYNAMIC SIDEBAR (CLICK)
# ==========================================

if st.session_state.selected_entity:
    entity = st.session_state.selected_entity

    with st.sidebar:
        st.header("🔍 AI Agent Root-Cause Analysis")

        st.markdown(f"### {entity['name']}")
        st.caption(f"Category: {entity['type']}")

        st.divider()

        s_col1, s_col2 = st.columns(2)

        with s_col1:
            if entity["impact"] > 0:
                st.error(
                    f"Financial Impact:\n"
                    f"${entity['impact']:,.2f}"
                )
            else:
                st.success(
                    "Financial Impact:\n"
                    "$0.00 (Norm)"
                )

        with s_col2:
            st.warning(f"Delay:\n{entity['days']} days")

        st.write(f"Current status/stage: {entity['status']}")
        st.write(f"Responsible person: {entity['owner']}")

        st.divider()

        st.subheader("📊 Explanation of the reasons for the risk (Explainability)")

        with st.spinner("The agent generates a contextual report..."):
            explanation = get_ai_explanation(
                item_name=entity["name"],
                item_type=entity["type"],
                impact=entity["impact"],
                days=entity["days"],
                owner=entity["owner"],
                stage_or_status=entity["status"],
            )

        st.info(explanation)

        st.divider()

        st.subheader("⚡ Autonomous actions in 1 click")

        if "Deal" in entity["type"]:

            if st.button(
                "✉️ Generate an AI draft of a letter to a client",
                use_container_width=True,
            ):
                st.success(
                    "🤖 The draft reactivation letter has been created and sent to CRM HubSpot!"
                )

            if st.button(
                "📅 Assign the task 'Urgent call' to the manager'",
                use_container_width=True,
            ):
                st.success(
                    "✅ The task has been successfully created and added to the employee's calendar."
                )

        else:

            if st.button(
                "🔔 Send an automatic claim letter",
                use_container_width=True,
            ):
                st.success(
                    "🚀 A payment link demanding debt repayment was sent to the client."
                )

            if st.button(
                "🔄 Run the auto-debit script",
                use_container_width=True,
            ):
                st.info(
                    "⏳ The request has been sent to the payment gateway. Stripe/Commerce Hub..."
                )

        st.divider()

        if st.button(
            "❌ Close object analysis",
            use_container_width=True,
        ):
            st.session_state.selected_entity = None
            st.rerun()

else:
    with st.sidebar:
        st.info(
            "💡 Agent Instructions: Go to any tab and click"
            "to a line in the table of transactions or accounts. The agent instantly "
            "will develop a deep financial risk analysis here."
        )

