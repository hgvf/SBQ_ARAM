import streamlit as st
import requests
import json
import yaml
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="ARAM - Agentic Research Analysis Machine", page_icon="📊", layout="wide")


def load_model_registry():
    p = Path("configs/model_registry.yaml")
    if p.exists():
        with open(p) as f:
            data = yaml.safe_load(f)
        return list(data.get("models", {}).keys())
    return ["default_reasoner", "report_writer", "fingpt_sentiment"]


def load_config():
    p = Path("configs/config.yaml")
    if p.exists():
        with open(p) as f:
            return yaml.safe_load(f)
    return {}


def get_api_base():
    cfg = load_config()
    return cfg.get("ui", {}).get("api_base_url", "http://localhost:8000")


def check_api_health(api_base):
    try:
        r = requests.get(f"{api_base}/health", timeout=3)
        return r.status_code == 200, r.json()
    except Exception:
        return False, {}


def run_workflow(api_base, workflow, ticker, date, query, model_alias, save_trace):
    endpoint_map = {
        "TradingAgents": "/workflows/tradingagents/run",
        "FinRobot": "/workflows/finrobot/run",
        "Auto": "/workflows/run",
    }
    endpoint = endpoint_map.get(workflow, "/workflows/run")
    payload = {
        "ticker": ticker,
        "date": date,
        "query": query,
        "model_alias": model_alias,
        "save_trace": save_trace,
    }
    r = requests.post(f"{api_base}{endpoint}", json=payload, timeout=300)
    r.raise_for_status()
    return r.json()


def check_sbq_available():
    try:
        r = requests.get("http://localhost:8001/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


# ── Sidebar ────────────────────────────────────────────────────────────────
st.sidebar.title("⚙️ ARAM Settings")

api_base = get_api_base()
api_ok, api_info = check_api_health(api_base)
if api_ok:
    st.sidebar.success(f"API: Connected ({api_info.get('version', '')})")
else:
    st.sidebar.error("API: Not connected — start the FastAPI server")

model_options = load_model_registry()
selected_model = st.sidebar.selectbox("LLM Model", model_options, index=0, help="Select model alias from model_registry.yaml")

workflow_type = st.sidebar.selectbox("Workflow", ["TradingAgents", "FinRobot", "Auto"], help="Select the analysis workflow")

save_trace = st.sidebar.checkbox("Save trace", value=True)

st.sidebar.markdown("---")
st.sidebar.markdown("**External Services**")
sbq_available = check_sbq_available()
if sbq_available:
    st.sidebar.success("SBQ-Quant: Connected")
else:
    st.sidebar.warning("SBQ-Quant: Not available")

# ── Main ───────────────────────────────────────────────────────────────────
st.title("📊 ARAM — Agentic Research Analysis Machine")
st.caption("Financial multi-agent analysis powered by TradingAgents & FinRobot workflows")

col1, col2 = st.columns([1, 1])
with col1:
    ticker = st.text_input("Ticker Symbol", value="NVDA", placeholder="e.g. NVDA, AAPL, 2330.TW").upper()
with col2:
    company_name = st.text_input("Company Name (optional)", placeholder="e.g. NVIDIA Corporation")

col3, col4 = st.columns([1, 1])
with col3:
    analysis_date = st.date_input("Analysis Date", value=datetime.today())
with col4:
    query = st.text_input("Query (optional)", placeholder="e.g. Generate a full research report and trading decision")

run_btn = st.button("🚀 Run Analysis", type="primary", use_container_width=True, disabled=not api_ok)

# ── Results ────────────────────────────────────────────────────────────────
if run_btn and ticker:
    with st.spinner(f"Running {workflow_type} workflow for {ticker}..."):
        try:
            result = run_workflow(
                api_base=api_base,
                workflow=workflow_type,
                ticker=ticker,
                date=str(analysis_date),
                query=query or f"Analyze {ticker} ({company_name})",
                model_alias=selected_model,
                save_trace=save_trace,
            )
        except Exception as e:
            st.error(f"Workflow failed: {e}")
            st.stop()

    st.success(f"Analysis complete! Trace ID: {result.get('trace_id', 'N/A')}")

    data = result.get("result", result)

    # TradingAgents result display
    if workflow_type in ("TradingAgents", "Auto") and "decision" in data:
        st.markdown("## 📈 Trading Decision")
        decision_col, conf_col, risk_col = st.columns(3)
        decision = data.get("decision", "hold").upper()
        confidence = data.get("confidence", 0)
        risk_level = data.get("risk_assessment", {}).get("risk_level", "N/A")

        decision_color = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡", "INCREASE_WEIGHT": "🟢", "DECREASE_WEIGHT": "🔴"}.get(decision, "⚪")
        decision_col.metric("Decision", f"{decision_color} {decision}")
        conf_col.metric("Confidence", f"{confidence:.0%}")
        risk_col.metric("Risk Level", risk_level)

        col_bull, col_bear = st.columns(2)
        with col_bull:
            st.markdown("**🐂 Bull Case**")
            bull_case = data.get("bull_case", [])
            if isinstance(bull_case, list):
                for item in bull_case:
                    st.markdown(f"- {item}")
            else:
                st.write(bull_case)

        with col_bear:
            st.markdown("**🐻 Bear Case**")
            bear_case = data.get("bear_case", [])
            if isinstance(bear_case, list):
                for item in bear_case:
                    st.markdown(f"- {item}")
            else:
                st.write(bear_case)

        with st.expander("📊 Sentiment Analysis"):
            st.json(data.get("sentiment", {}))

        with st.expander("📉 Technical Analysis"):
            st.json(data.get("technical", {}))

        with st.expander("📋 Fundamental Analysis"):
            st.json(data.get("fundamental", {}))

        with st.expander("🛡️ Risk Assessment"):
            st.json(data.get("risk_assessment", {}))

        st.markdown("---")
        st.markdown("**⬇️ Download Results**")
        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button(
                label="📥 Download Decision JSON",
                data=json.dumps(data, indent=2, default=str),
                file_name=f"{ticker}_{analysis_date}_decision.json",
                mime="application/json",
            )

    # FinRobot result display
    if workflow_type in ("FinRobot", "Auto") and "report_markdown" in data:
        st.markdown("## 📄 Research Report")

        rating = data.get("rating_view", "N/A")
        st.info(f"**Rating View:** {rating}")

        thesis = data.get("investment_thesis", [])
        risks = data.get("key_risks", [])
        val_view = data.get("valuation_view", "")

        col_t, col_r = st.columns(2)
        with col_t:
            st.markdown("**💡 Investment Thesis**")
            if isinstance(thesis, list):
                for t in thesis:
                    st.markdown(f"- {t}")
            else:
                st.write(thesis)

        with col_r:
            st.markdown("**⚠️ Key Risks**")
            if isinstance(risks, list):
                for r in risks:
                    st.markdown(f"- {r}")
            else:
                st.write(risks)

        if val_view:
            st.markdown(f"**📊 Valuation View:** {val_view}")

        st.markdown("---")
        st.markdown("### Full Report")
        report_md = data.get("report_markdown", "")
        if report_md:
            st.markdown(report_md)
        else:
            st.info("No report content generated.")

        with st.expander("🔍 Data Analysis Details"):
            st.json(data.get("data_analysis", {}))

        with st.expander("💭 Concept Analysis Details"):
            st.json(data.get("concept_analysis", {}))

        with st.expander("📊 Valuation Details"):
            st.json(data.get("valuation", {}))

        st.markdown("---")
        dl3, dl4 = st.columns(2)
        with dl3:
            if report_md:
                st.download_button(
                    label="📥 Download Report (Markdown)",
                    data=report_md,
                    file_name=f"{ticker}_{analysis_date}_report.md",
                    mime="text/markdown",
                )
        with dl4:
            st.download_button(
                label="📥 Download Report Data (JSON)",
                data=json.dumps({k: v for k, v in data.items() if k != "report_markdown"}, indent=2, default=str),
                file_name=f"{ticker}_{analysis_date}_report_data.json",
                mime="application/json",
            )

    # SBQ-Quant signals (optional)
    if sbq_available:
        with st.expander("🔢 SBQ-Quant Signals (Optional)", expanded=False):
            try:
                signals_r = requests.get(f"http://localhost:8001/signals", params={"ticker": ticker, "date": str(analysis_date)}, timeout=10)
                if signals_r.status_code == 200:
                    st.json(signals_r.json())
                else:
                    st.info("No signal data available.")
            except Exception:
                st.info("SBQ-Quant signals unavailable.")

# ── Recent Traces ──────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 🗂️ Recent Traces")
traces_dir = Path("storage/traces")
if traces_dir.exists():
    trace_files = sorted(traces_dir.glob("*.json"), reverse=True)[:10]
    if trace_files:
        for tf in trace_files:
            with open(tf) as f:
                trace_data = json.load(f)
            with st.expander(f"{trace_data.get('trace_id', tf.stem)} — {trace_data.get('ticker', '')} {trace_data.get('date', '')}"):
                st.json(trace_data)
    else:
        st.info("No traces yet. Run an analysis to generate traces.")
else:
    st.info("No traces directory found.")
