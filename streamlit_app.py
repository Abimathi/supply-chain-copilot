# Supply Chain Copilot — AI-Powered Manufacturing Control Tower Streamlit Application
# Co-authored with CoCo
import streamlit as st
import json
import os
import pandas as pd

conn = st.connection("snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL"))

st.set_page_config(layout="wide")

# ── Theme CSS ──
st.markdown("""
<style>
    /* Base — medium grey, no white anywhere */
    .stApp { background-color: #d6dae0; color: #1a1a2e; }
    section[data-testid="stSidebar"] { background-color: #c8cdd4; }

    /* Force tab panels and all containers to match */
    .stTabs [data-baseweb="tab-panel"],
    [data-testid="stVerticalBlock"],
    [data-testid="stHorizontalBlock"],
    .element-container { background-color: transparent !important; }

    /* Dataframe / table area — subtle, not white */
    .stDataFrame, .stDataFrame > div { background-color: #ccd1d9 !important; border-radius: 6px; }

    /* Headers */
    h1, h2, h3, h4, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 { color: #1a3a5c; }
    /* Metrics */
    [data-testid="stMetricValue"] { color: #1a1a2e; font-size: 1rem; }
    [data-testid="stMetricLabel"] { color: #444; font-size: 0.78rem; }

    /* KPI cards via HTML */
    .kpi-row { display: flex; gap: 10px; margin: 8px 0 12px 0; }
    .kpi-card { flex: 1; background: #bfc5ce; border-radius: 8px; padding: 12px 16px;
                text-align: center; border: 1px solid #aab0b8; }
    .kpi-val { font-size: 1.3rem; font-weight: 700; color: #1a3a5c; margin: 0; }
    .kpi-lbl { font-size: 0.75rem; color: #555; margin: 0; }

    /* Chat */
    .user-msg { background: #c2cad6; border-left: 3px solid #2563eb; padding: 10px 14px;
                margin: 6px 0; border-radius: 6px; color: #1a1a2e; }
    .asst-msg { background: #c8ddd0; border-left: 3px solid #16a34a; padding: 10px 14px;
                margin: 6px 0; border-radius: 6px; color: #1a1a2e; }

    /* Buttons */
    .stButton>button { background-color: #bfc5ce; color: #1a1a2e; border: 1px solid #a0a6ae;
                       font-size: 0.75rem; padding: 4px 10px; }
    .stButton>button:hover { background-color: #aab0b8; border-color: #2563eb; }

    /* Sidebar text — white on dark sidebar */
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown h3, section[data-testid="stSidebar"] .stMarkdown h4,
    section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] label { color: #ffffff !important; }
    section[data-testid="stSidebar"] .stCaption, section[data-testid="stSidebar"] small { color: #d0d0d0 !important; }
    /* Sidebar button visible */
    section[data-testid="stSidebar"] .stButton>button { background-color: #3a4a5c; color: #ffffff; border: 1px solid #5a6a7c; }
    section[data-testid="stSidebar"] .stButton>button:hover { background-color: #4a5a6c; }
    /* Sidebar expander */
    section[data-testid="stSidebar"] .streamlit-expanderHeader { color: #ffffff !important; background-color: #3a4a5c; }
    section[data-testid="stSidebar"] .streamlit-expanderContent { background-color: #2a3a4c; color: #d0d0d0; }

    /* Inputs / selectbox — no white */
    .stTextInput>div>div>input, .stSelectbox>div>div { background-color: #c8cdd4 !important; color: #1a1a2e; }

    /* Expanders */
    .streamlit-expanderHeader { background-color: #c2c8d0; border-radius: 4px; }

    /* Layout — maximize width, tight padding */
    .block-container { padding: 0.5rem 1rem 0 1rem; max-width: 100%; }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 0.4rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }

    /* Progress bars */
    .stProgress > div > div { background-color: #a0a6ae; }
    .stProgress > div > div > div { background-color: #2563eb; }

    /* Remove extra Streamlit spacing */
    .css-1d391kg, .css-18e3th9 { padding: 0.5rem 1rem; }
</style>
""", unsafe_allow_html=True)

# ── Constants ──
DB = "SUPPLY_CHAIN_COPILOT"
ANALYTICS = f"{DB}.ANALYTICS"
AI = f"{DB}.AI"
AGENT_NAME = f"{AI}.SUPPLY_CHAIN_AGENT"
SEARCH_SVC = f"{AI}.SUPPLY_CHAIN_DOCUMENT_SEARCH"
LLM_MODEL = "llama3.1-70b"

# ── Helpers ──
@st.cache_data(ttl=300)
def run_sql(query):
    return conn.query(query)

def run_sql_nocache(query):
    return conn.query(query, ttl=0)

@st.cache_data(ttl=300)
def get_control_tower():
    return run_sql(f"SELECT * FROM {ANALYTICS}.VW_SUPPLY_CHAIN_CONTROL_TOWER ORDER BY PLANT_RISK_SCORE DESC")

@st.cache_data(ttl=300)
def get_part_risk():
    return run_sql(f"SELECT * FROM {ANALYTICS}.VW_PART_RISK ORDER BY PART_RISK_SCORE DESC")

@st.cache_data(ttl=300)
def get_supply_position(plant_name=None, part_name=None):
    q = f"SELECT * FROM {ANALYTICS}.VW_SUPPLY_POSITION WHERE 1=1"
    if plant_name: q += f" AND PLANT_NAME = '{plant_name}'"
    if part_name: q += f" AND PART_NAME = '{part_name}'"
    return run_sql(q + " ORDER BY DAYS_OF_INVENTORY ASC")

@st.cache_data(ttl=300)
def get_supplier_performance():
    return run_sql(f"SELECT * FROM {ANALYTICS}.VW_SUPPLIER_PERFORMANCE ORDER BY SUPPLIER_RISK_SCORE DESC")

@st.cache_data(ttl=300)
def get_customer_impact(plant_filter=None, priority_filter=None):
    q = f"""SELECT CUSTOMER_NAME, CUSTOMER_PRIORITY, PLANT_NAME, PART_NAME,
            COUNT(ORDER_LINE_ID) AS AT_RISK_ORDERS, ROUND(SUM(OPEN_ORDER_VALUE),2) AS REVENUE_AT_RISK
        FROM {ANALYTICS}.VW_CUSTOMER_ORDER_RISK
        WHERE CALCULATED_AT_RISK_FLAG = TRUE AND ACTUAL_DELIVERY_DATE IS NULL AND ORDER_STATUS != 'CANCELLED'"""
    if plant_filter: q += f" AND PLANT_NAME = '{plant_filter}'"
    if priority_filter: q += f" AND CUSTOMER_PRIORITY = '{priority_filter}'"
    return run_sql(q + " GROUP BY 1,2,3,4 ORDER BY REVENUE_AT_RISK DESC LIMIT 50")

def search_documents(query, limit=5):
    escaped = query.replace("'", "\\'").replace('"', '\\"')
    try:
        df = run_sql_nocache(f"""SELECT PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
            '{SEARCH_SVC}',
            '{{"query": "{escaped}", "columns": ["DOCUMENT_ID","DOCUMENT_TYPE","TITLE","ENTITY_NAME","EVENT_DATE","SEVERITY","DOCUMENT_TEXT"], "limit": {limit}}}'
        ))['results'] AS results""")
        if df.empty: return []
        raw = df.iloc[0, 0]
        return json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return []

def fmt_cr(val):
    if val is None or pd.isna(val): return "N/A"
    return f"₹{val/1e7:.2f} Cr"

def fmt_pct(val):
    if val is None or pd.isna(val): return "N/A"
    return f"{val:.1f}%"

# ── SQL templates ──
TEMPLATES = {
    "highest_risk_plant": f"SELECT PLANT_NAME, PLANT_RISK_SCORE, RISK_LEVEL, CUSTOMER_EXPOSURE_SCORE, REVENUE_EXPOSURE_SCORE, SHORTAGE_SEVERITY_SCORE, INBOUND_DISRUPTION_SCORE, AT_RISK_ORDER_COUNT, REVENUE_AT_RISK, CRITICAL_SHORTAGE_PART_COUNT, DELAYED_INBOUND_SHIPMENTS, MOST_CRITICAL_PART, MOST_CRITICAL_PART_DAYS_OF_INVENTORY, TOP_RISK_SUPPLIER, TOP_RISK_SUPPLIER_SCORE FROM {ANALYTICS}.VW_SUPPLY_CHAIN_CONTROL_TOWER ORDER BY PLANT_RISK_SCORE DESC",
    "why_plant_risk": f"SELECT PLANT_NAME, PLANT_RISK_SCORE, RISK_LEVEL, CUSTOMER_EXPOSURE_SCORE, REVENUE_EXPOSURE_SCORE, SHORTAGE_SEVERITY_SCORE, INBOUND_DISRUPTION_SCORE, AT_RISK_ORDER_COUNT, REVENUE_AT_RISK, CRITICAL_SHORTAGE_PART_COUNT, MOST_CRITICAL_PART, MOST_CRITICAL_PART_DAYS_OF_INVENTORY, TOP_RISK_SUPPLIER, TOP_RISK_SUPPLIER_SCORE, DELAYED_INBOUND_SHIPMENTS FROM {ANALYTICS}.VW_SUPPLY_CHAIN_CONTROL_TOWER WHERE PLANT_RISK_SCORE = (SELECT MAX(PLANT_RISK_SCORE) FROM {ANALYTICS}.VW_SUPPLY_CHAIN_CONTROL_TOWER)",
    "crankshaft_supply_gap": f"SELECT * FROM {ANALYTICS}.VW_SUPPLY_POSITION WHERE PART_NAME = 'Crankshaft Assembly' AND PLANT_NAME = 'Chennai Assembly Plant'",
    "doi": f"SELECT PLANT_NAME, PART_NAME, DAYS_OF_INVENTORY, QUANTITY_ON_HAND, QUANTITY_AVAILABLE, STOCK_STATUS FROM {ANALYTICS}.VW_SUPPLY_POSITION WHERE PART_NAME = 'Crankshaft Assembly' AND PLANT_NAME = 'Chennai Assembly Plant'",
    "bharat_forge_otd": f"SELECT SUPPLIER_NAME, OTD_PCT, SUPPLIER_RISK_SCORE, DELIVERED_SHIPMENT_COUNT, LATE_SHIPMENT_COUNT, AVG_DELAY_DAYS, ACTIVE_DELAYED_SHIPMENT_COUNT FROM {ANALYTICS}.VW_SUPPLIER_PERFORMANCE WHERE SUPPLIER_NAME = 'Bharat Forge Ltd'",
    "bf_delayed_shipments": f"SELECT SHIPMENT_ID, PART_NAME, PLANT_NAME, EXPECTED_ARRIVAL_DATE, CURRENT_ESTIMATED_ARRIVAL_DATE, EXPECTED_DELAY_DAYS, DELAY_REASON FROM {ANALYTICS}.VW_SHIPMENT_RISK WHERE SUPPLIER_NAME = 'Bharat Forge Ltd' AND IS_EXPECTED_LATE = TRUE",
    "exposed_customers": f"SELECT CUSTOMER_NAME, CUSTOMER_PRIORITY, PLANT_NAME, PART_NAME, COUNT(ORDER_LINE_ID) AS AT_RISK_ORDERS, ROUND(SUM(OPEN_ORDER_VALUE),2) AS REVENUE_AT_RISK FROM {ANALYTICS}.VW_CUSTOMER_ORDER_RISK WHERE CALCULATED_AT_RISK_FLAG = TRUE AND ACTUAL_DELIVERY_DATE IS NULL AND ORDER_STATUS != 'CANCELLED' GROUP BY 1,2,3,4 ORDER BY REVENUE_AT_RISK DESC LIMIT 20",
    "revenue_at_risk": f"SELECT PLANT_NAME, SUM(CASE WHEN CALCULATED_AT_RISK_FLAG THEN OPEN_ORDER_VALUE ELSE 0 END) AS REVENUE_AT_RISK, COUNT_IF(CALCULATED_AT_RISK_FLAG) AS AT_RISK_ORDERS FROM {ANALYTICS}.VW_CUSTOMER_ORDER_RISK WHERE ACTUAL_DELIVERY_DATE IS NULL AND ORDER_STATUS != 'CANCELLED' GROUP BY PLANT_NAME ORDER BY REVENUE_AT_RISK DESC",
    "pune_vs_chennai": f"SELECT PLANT_NAME, QUANTITY_ON_HAND, QUANTITY_AVAILABLE, DAYS_OF_INVENTORY, NEAR_TERM_OPEN_DEMAND, PROJECTED_SUPPLY_GAP, STOCK_STATUS, SAFETY_STOCK_QTY FROM {ANALYTICS}.VW_SUPPLY_POSITION WHERE PART_NAME = 'Crankshaft Assembly' AND PLANT_NAME IN ('Chennai Assembly Plant','Pune Manufacturing Hub')",
    "top_parts": f"SELECT PART_NAME, CRITICALITY, PART_RISK_SCORE, PRIMARY_SUPPLIER_NAME, PRIMARY_SUPPLIER_OTD_PCT, TOTAL_SHORTAGE_QTY, AT_RISK_ORDER_COUNT, REVENUE_AT_RISK FROM {ANALYTICS}.VW_PART_RISK ORDER BY PART_RISK_SCORE DESC LIMIT 10",
    "exec_briefing_data": f"SELECT PLANT_NAME, PLANT_RISK_SCORE, RISK_LEVEL, AT_RISK_ORDER_COUNT, REVENUE_AT_RISK, MOST_CRITICAL_PART, MOST_CRITICAL_PART_DAYS_OF_INVENTORY, TOP_RISK_SUPPLIER, TOP_RISK_SUPPLIER_SCORE, DELAYED_INBOUND_SHIPMENTS FROM {ANALYTICS}.VW_SUPPLY_CHAIN_CONTROL_TOWER ORDER BY PLANT_RISK_SCORE DESC LIMIT 1"
}

def match_template(q):
    ql = q.lower()
    if any(k in ql for k in ["highest risk plant","which plant","all plants","plant risk","risk status"]): return "highest_risk_plant"
    if any(k in ql for k in ["why","explain"]) and any(k in ql for k in ["risk","high risk","chennai"]): return "why_plant_risk"
    if "supply gap" in ql and "crankshaft" in ql: return "crankshaft_supply_gap"
    if any(k in ql for k in ["days of inventory","doi","how many days"]) and "crankshaft" in ql: return "doi"
    if "bharat forge" in ql and any(k in ql for k in ["otd","on-time","on time","delivery"]): return "bharat_forge_otd"
    if "bharat forge" in ql and any(k in ql for k in ["delayed","late","shipment"]): return "bf_delayed_shipments"
    if any(k in ql for k in ["customer","who is exposed","which customer"]): return "exposed_customers"
    if "revenue" in ql and "risk" in ql: return "revenue_at_risk"
    if any(k in ql for k in ["pune","another plant","can pune","help chennai","compare"]): return "pune_vs_chennai"
    if any(k in ql for k in ["top parts","highest risk part","part risk"]): return "top_parts"
    if any(k in ql for k in ["briefing","executive","30 second","summary"]): return "exec_briefing_data"
    return None

def route_question(q):
    ql = q.lower()
    if any(k in ql for k in ["why","recommend","what should","briefing","root cause","can another","can pune","what action","explain risk","what to do","executive"]): return "both"
    if any(k in ql for k in ["notice","document","evidence","agreement","sla","quality","logistics","procurement","expedite"]): return "search"
    return "analytics"

def synthesize_response(question, analytics_data, search_results):
    at = analytics_data.head(10).to_string(index=False, max_colwidth=60) if analytics_data is not None and not analytics_data.empty else ""
    st_text = ""
    if search_results:
        for d in search_results[:5]:
            st_text += f"\n- [{d.get('DOCUMENT_TYPE','')}] {d.get('TITLE','')} ({d.get('ENTITY_NAME','')}): {d.get('DOCUMENT_TEXT','')[:250]}...\n"
    prompt = f"""You are a manufacturing supply-chain control tower assistant. Answer concisely for executives.

Question: {question}

ANALYTICS DATA:
{at if at else "N/A"}

DOCUMENT EVIDENCE:
{st_text if st_text else "N/A"}

Rules: Use analytics for facts, documents for causes. Do not invent. Revenue in INR crore (1 Cr=10M). Percentages with 1 decimal. Structure: **Risk Summary**, **Business Impact**, **Root Cause Evidence** (if docs), **Recommended Actions** (if asked). Recommendations are suggestions only. Max 150 words. No technical/Snowflake terms."""
    try:
        return run_sql_nocache(f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{LLM_MODEL}', '{prompt.replace(chr(39), chr(39)+chr(39))}') AS r").iloc[0,0]
    except Exception as e:
        return f"Error: {e}"

def call_agent(question):
    try:
        escaped = question.replace('"', '\\"').replace("'", "\\'")
        resp = json.loads(run_sql_nocache(f"""SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN('{AGENT_NAME}',
            $${{"messages":[{{"role":"user","content":[{{"type":"text","text":"{escaped}"}}]}}]}}$$) AS r""").iloc[0,0])
        if resp.get("code") in ("391920","399504"): return None
        for item in resp.get("content",[]):
            if item.get("type") == "text": return item["text"]
        return None
    except Exception:
        return None

def process_chat(question):
    if st.session_state.get("try_agent", True):
        r = call_agent(question)
        if r:
            st.session_state["exec_mode"] = "Agent"
            return r
        st.session_state["try_agent"] = False
        st.session_state["exec_mode"] = "AI Copilot"
    route = route_question(question)
    tpl = match_template(question)
    analytics_data = None
    search_results = None
    if route in ("analytics","both"):
        if tpl and tpl in TEMPLATES:
            try: analytics_data = run_sql_nocache(TEMPLATES[tpl])
            except: pass
        else:
            try:
                gp = f"Generate a single Snowflake SQL SELECT to answer: {question}. Views: {ANALYTICS}.VW_SUPPLY_CHAIN_CONTROL_TOWER, {ANALYTICS}.VW_PART_RISK, {ANALYTICS}.VW_SUPPLIER_PERFORMANCE, {ANALYTICS}.VW_SUPPLY_POSITION, {ANALYTICS}.VW_CUSTOMER_ORDER_RISK, {ANALYTICS}.VW_SHIPMENT_RISK, {ANALYTICS}.VW_LANDED_COST. Return ONLY SQL."
                gs = run_sql_nocache(f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{LLM_MODEL}','{gp.replace(chr(39),chr(39)+chr(39))}') AS r").iloc[0,0].strip()
                if "```" in gs:
                    gs = gs.split("```")[1]
                    if gs.lower().startswith("sql"): gs = gs[3:]
                    gs = gs.strip()
                analytics_data = run_sql_nocache(gs)
            except: pass
    if route in ("search","both"):
        search_results = search_documents(question, 5)
    return synthesize_response(question, analytics_data, search_results)

# ── Session state ──
if "messages" not in st.session_state: st.session_state.messages = []
if "exec_mode" not in st.session_state: st.session_state["exec_mode"] = "AI Copilot"
if "try_agent" not in st.session_state: st.session_state["try_agent"] = True

# ══════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════
st.markdown("## Supply Chain Copilot")
st.markdown("##### AI-Powered Manufacturing Control Tower")

ct_data = get_control_tower()
sup_data = get_supplier_performance()
ships = run_sql(f"SELECT COUNT(*) AS c FROM {ANALYTICS}.VW_SHIPMENT_RISK WHERE SHIPMENT_STATUS IN ('IN_TRANSIT','DELAYED')")
n_ships = int(ships.iloc[0, 0])
mode = st.session_state["exec_mode"]

st.markdown(f"""
<div class="kpi-row">
    <div class="kpi-card"><p class="kpi-val">{len(ct_data)}</p><p class="kpi-lbl">Plants</p></div>
    <div class="kpi-card"><p class="kpi-val">{len(sup_data)}</p><p class="kpi-lbl">Suppliers</p></div>
    <div class="kpi-card"><p class="kpi-val">{n_ships}</p><p class="kpi-lbl">Active Shipments</p></div>
    <div class="kpi-card"><p class="kpi-val">{mode}</p><p class="kpi-lbl">Mode</p></div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# TABS
# ══════════════════════════════════════════
tab_dash, tab_drill, tab_whatif = st.tabs(["Control Tower", "Deep Dive", "What-If"])

# ── TAB 1: CONTROL TOWER ──
with tab_dash:
    if not ct_data.empty:
        top = ct_data.iloc[0]
        worst = sup_data.loc[sup_data["OTD_PCT"].idxmin()] if not sup_data.empty and sup_data["OTD_PCT"].notna().any() else None
        st.markdown(f"""
<div class="kpi-row">
    <div class="kpi-card"><p class="kpi-val">{top["PLANT_NAME"].replace(" Assembly Plant","").replace(" Manufacturing Hub","")}</p><p class="kpi-lbl">Highest Risk Plant</p></div>
    <div class="kpi-card"><p class="kpi-val">{top['PLANT_RISK_SCORE']:.1f}/100</p><p class="kpi-lbl">Risk Score</p></div>
    <div class="kpi-card"><p class="kpi-val">{fmt_cr(top["REVENUE_AT_RISK"])}</p><p class="kpi-lbl">Revenue at Risk</p></div>
    <div class="kpi-card"><p class="kpi-val">{int(top["CRITICAL_SHORTAGE_PART_COUNT"])}</p><p class="kpi-lbl">Critical Shortages</p></div>
    <div class="kpi-card"><p class="kpi-val">{int(top["DELAYED_INBOUND_SHIPMENTS"])}</p><p class="kpi-lbl">Delayed Inbound</p></div>
    <div class="kpi-card"><p class="kpi-val">{worst['SUPPLIER_NAME'].split(' ')[0] + ' ' + fmt_pct(worst['OTD_PCT']) if worst is not None else 'N/A'}</p><p class="kpi-lbl">Worst Supplier OTD</p></div>
</div>
""", unsafe_allow_html=True)

        st.markdown("#### Plant Risk Overview")
        disp = ct_data[["PLANT_NAME","PLANT_RISK_SCORE","RISK_LEVEL","AT_RISK_ORDER_COUNT","REVENUE_AT_RISK","CRITICAL_SHORTAGE_PART_COUNT","DELAYED_INBOUND_SHIPMENTS","MOST_CRITICAL_PART","TOP_RISK_SUPPLIER"]].copy()
        disp["REVENUE_AT_RISK"] = disp["REVENUE_AT_RISK"].apply(fmt_cr)
        st.dataframe(disp, use_container_width=True)

        st.markdown("#### Risk Explainability")
        sel_plant = st.selectbox("Plant", ct_data["PLANT_NAME"].tolist(), key="expl")
        pr = ct_data[ct_data["PLANT_NAME"] == sel_plant].iloc[0]
        e1, e2 = st.columns([3, 2])
        with e1:
            for nm, col, mx in [("Customer Exposure","CUSTOMER_EXPOSURE_SCORE",25),("Revenue Exposure","REVENUE_EXPOSURE_SCORE",25),("Shortage Severity","SHORTAGE_SEVERITY_SCORE",30),("Inbound Disruption","INBOUND_DISRUPTION_SCORE",20)]:
                v = float(pr[col])
                pct_int = int(min(v / mx, 1.0) * 100)
                st.text(f"{nm}: {v:.1f} / {mx}")
                st.progress(pct_int)
        with e2:
            st.metric("Total", f"{pr['PLANT_RISK_SCORE']:.1f}/100")
            st.metric("Level", pr["RISK_LEVEL"])
            if pr["MOST_CRITICAL_PART"]: st.metric("Critical Part", str(pr["MOST_CRITICAL_PART"]))
            if pr["TOP_RISK_SUPPLIER"]: st.metric("Risk Supplier", str(pr["TOP_RISK_SUPPLIER"]))

        st.markdown("#### Top Risk Parts")
        pts = get_part_risk().head(10)[["PART_NAME","CRITICALITY","PART_RISK_SCORE","PRIMARY_SUPPLIER_NAME","PRIMARY_SUPPLIER_OTD_PCT","TOTAL_SHORTAGE_QTY","AT_RISK_ORDER_COUNT","REVENUE_AT_RISK"]].copy()
        pts["REVENUE_AT_RISK"] = pts["REVENUE_AT_RISK"].apply(fmt_cr)
        pts["PRIMARY_SUPPLIER_OTD_PCT"] = pts["PRIMARY_SUPPLIER_OTD_PCT"].apply(fmt_pct)
        st.dataframe(pts, use_container_width=True)

# ── TAB 2: DEEP DIVE ──
with tab_drill:
    sec = st.radio("", ["Supply Position","Suppliers","Customer Impact","Documents"], horizontal=True)
    if sec == "Supply Position":
        sp_all = get_supply_position()
        s1, s2 = st.columns(2)
        fp = s1.selectbox("Plant", ["All"] + sorted(sp_all["PLANT_NAME"].unique()), key="sp_p")
        fpt = s2.selectbox("Part", ["All"] + sorted(sp_all["PART_NAME"].unique()), key="sp_pt")
        d = get_supply_position(fp if fp != "All" else None, fpt if fpt != "All" else None)
        if not d.empty:
            cols = ["PLANT_NAME","PART_NAME","STOCK_STATUS","QUANTITY_ON_HAND","QUANTITY_AVAILABLE","DAYS_OF_INVENTORY","NEAR_TERM_OPEN_DEMAND","PROJECTED_SUPPLY_GAP","DELAYED_INBOUND_COUNT","SHORTAGE_FLAG"]
            st.dataframe(d[[c for c in cols if c in d.columns]].head(50), use_container_width=True)
    elif sec == "Suppliers":
        sd = get_supplier_performance()[["SUPPLIER_NAME","OTD_PCT","SUPPLIER_RISK_SCORE","DELIVERED_SHIPMENT_COUNT","LATE_SHIPMENT_COUNT","AVG_DELAY_DAYS","ACTIVE_DELAYED_SHIPMENT_COUNT","IS_CRITICAL"]].copy()
        sd["OTD_PCT"] = sd["OTD_PCT"].apply(fmt_pct)
        st.dataframe(sd, use_container_width=True)
    elif sec == "Customer Impact":
        fc1, fc2 = st.columns(2)
        cp = fc1.selectbox("Plant", ["All"] + sorted(ct_data["PLANT_NAME"].tolist()), key="ci_p")
        cpri = fc2.selectbox("Priority", ["All","PLATINUM","GOLD","SILVER"], key="ci_pri")
        ci = get_customer_impact(cp if cp != "All" else None, cpri if cpri != "All" else None)
        if not ci.empty:
            ci["REVENUE_AT_RISK"] = ci["REVENUE_AT_RISK"].apply(fmt_cr)
            st.dataframe(ci, use_container_width=True)
        else: st.info("No at-risk orders.")
    elif sec == "Documents":
        sq = st.text_input("Search documents", "Bharat Forge crankshaft delay", key="ds")
        if st.button("Search", key="ds_btn"):
            res = search_documents(sq, 5)
            if res:
                for doc in res:
                    with st.expander(f"[{doc.get('DOCUMENT_TYPE','')}] {doc.get('TITLE','')}"):
                        st.markdown(f"**{doc.get('ENTITY_NAME','')}** | {doc.get('EVENT_DATE','')} | {doc.get('SEVERITY','')}")
                        st.markdown(doc.get("DOCUMENT_TEXT","")[:500])
            else: st.info("No documents found.")

# ── TAB 3: WHAT-IF ──
with tab_whatif:
    st.markdown("#### What-If Simulation")
    st.caption("Model interventions. No actual data is modified.")
    sp_all = get_supply_position()
    gaps = sp_all[sp_all["PROJECTED_SUPPLY_GAP"] > 0].sort_values("PROJECTED_SUPPLY_GAP", ascending=False)
    if gaps.empty:
        st.success("No active supply gaps.")
    else:
        w1, w2 = st.columns(2)
        wp = w1.selectbox("Plant", gaps["PLANT_NAME"].unique(), key="wi_p")
        wpt = w2.selectbox("Part", gaps[gaps["PLANT_NAME"] == wp]["PART_NAME"].unique(), key="wi_pt")
        row = sp_all[(sp_all["PLANT_NAME"] == wp) & (sp_all["PART_NAME"] == wpt)]
        if not row.empty:
            r = row.iloc[0]
            gap = int(r["PROJECTED_SUPPLY_GAP"])
            st.markdown(f"""
<div class="kpi-row">
    <div class="kpi-card"><p class="kpi-val">{int(r['QUANTITY_AVAILABLE']):,}</p><p class="kpi-lbl">Available</p></div>
    <div class="kpi-card"><p class="kpi-val">{int(r['NEAR_TERM_OPEN_DEMAND']):,}</p><p class="kpi-lbl">Demand</p></div>
    <div class="kpi-card"><p class="kpi-val">{int(r['USABLE_INBOUND_QTY']):,}</p><p class="kpi-lbl">Inbound</p></div>
    <div class="kpi-card"><p class="kpi-val">{gap:,}</p><p class="kpi-lbl">Current Gap</p></div>
</div>
""", unsafe_allow_html=True)
            i1, i2, i3, i4 = st.columns(4)
            exp = i1.number_input("Expedite", 0, 10000, 0, 50, key="wi_e")
            xfr = i2.number_input("Transfer", 0, 10000, 0, 50, key="wi_x")
            add = i3.number_input("New Inbound", 0, 10000, 0, 50, key="wi_a")
            dfr = i4.number_input("Defer", 0, 10000, 0, 50, key="wi_d")
            new_gap = max(0, gap - exp - xfr - add - dfr)
            reduct = gap - new_gap
            pct = (reduct / gap * 100) if gap > 0 else 0
            st.markdown(f"""
<div class="kpi-row">
    <div class="kpi-card"><p class="kpi-val">{gap:,}</p><p class="kpi-lbl">Before</p></div>
    <div class="kpi-card"><p class="kpi-val">{new_gap:,}</p><p class="kpi-lbl">After</p></div>
    <div class="kpi-card"><p class="kpi-val">{pct:.0f}%</p><p class="kpi-lbl">Reduction</p></div>
</div>
""", unsafe_allow_html=True)
            if new_gap == 0: st.success("Gap fully closed by simulated interventions.")
            elif pct > 50: st.warning(f"Gap reduced {pct:.0f}%. Further action needed.")
            st.caption("Simulation only — no data modified.")

# ── SIDEBAR: AI COPILOT ──
with st.sidebar.expander("Ask Copilot", expanded=False):
    st.caption("Ask about plant risk, shortages, suppliers, customers, evidence, or recommended actions.")
    quick = [
        ("Why top risk?", "Why is the highest-risk plant at risk?"),
        ("Revenue exposed?", "What customer revenue is exposed?"),
        ("Can another plant help?", "Can another plant help with the critical part shortage?"),
        ("What should we do?", "What should we do to mitigate the top supply chain risk?"),
    ]
    q1, q2 = st.columns(2)
    for i, (label, full_q) in enumerate(quick):
        target = q1 if i % 2 == 0 else q2
        if target.button(label, key=f"float_qq{i}", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": full_q})

    if not st.session_state.messages:
        st.info("Try: Why is the highest-risk plant at risk?")
    for msg in st.session_state.messages[-8:]:
        cls = "user-msg" if msg["role"] == "user" else "asst-msg"
        pre = "**You:**" if msg["role"] == "user" else "**Copilot:**"
        st.markdown(f'<div class="{cls}">{pre} {msg["content"]}</div>', unsafe_allow_html=True)

    col_in, col_btn = st.columns([5, 1])
    user_input = col_in.text_input("Ask the Control Tower...", key="floating_chat_input", label_visibility="collapsed")
    send = col_btn.button("Ask", key="floating_send_btn")
    if send and user_input.strip():
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        with st.spinner("Analyzing risk, impact and evidence..."):
            answer = process_chat(st.session_state.messages[-1]["content"])
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

# ── SIDEBAR: EXECUTIVE ACTIONS ──
st.sidebar.markdown("<h3 style='color:#ffffff !important; margin-bottom:0.6rem;'>Executive Actions</h3>", unsafe_allow_html=True)
if st.sidebar.button("Generate Briefing"):
    with st.sidebar:
        with st.spinner("Generating..."):
            b = process_chat("Give me a concise 30-second executive briefing on the highest supply chain risk. Include plant, critical part, supplier, revenue, and top 3 actions. Under 100 words.")
            st.markdown(b)
st.sidebar.markdown("---")
st.sidebar.caption(f"Mode: {st.session_state['exec_mode']}")
st.sidebar.caption("Supply Chain Copilot v1.0")
with st.sidebar.expander("Debug"):
    st.markdown(
        f"<div style='color:#ffffff !important; line-height:1.8;'>"
        f"<b>LLM:</b> {LLM_MODEL}<br>"
        f"<b>Agent tried:</b> {not st.session_state.get('try_agent', True)}"
        f"</div>",
        unsafe_allow_html=True
    )
