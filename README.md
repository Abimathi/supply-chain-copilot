# Supply Chain Copilot — AI-Powered Manufacturing Control Tower

**Team:** Supply Chain Copilot &nbsp;|&nbsp; **Problem Statement:** MFG – Supply Chain Ontology & Governed Conversational Analytics
**Event:** CoCo CLI Hackathon (GCC Edition) — YourStory × Snowflake × H2S

Real-time risk intelligence, root-cause analysis, and recommended actions for manufacturing supply chains — powered entirely by **Snowflake + CoCo CLI**.

▶️ **Watch the demo:** [YouTube]([https://youtu.be/REPLACE_WITH_VIDEO_ID](https://youtu.be/afqixzsGURk?si=SPy8uSlgkE-sdBkn)) &nbsp;|&nbsp; [local MP4](Supply_Chain_Copilot_Demo.mp4)

---

## The problem

Manufacturing supply chains lack a single pane of glass for risk visibility across plants, suppliers, and customer orders. Plant managers and executives react to disruptions **after** they hit production — missing early warning signals from supplier delays, inventory shortages, and inbound logistics failures. Root-cause analysis means manually cross-referencing spreadsheets, supplier notices, and quality holds, taking hours instead of seconds.

## The solution

Supply Chain Copilot computes **composite risk scores (0–100)** across every plant — fully explainable by customer exposure, revenue exposure, shortage severity, and inbound disruption — straight from live Snowflake data. An embedded AI Copilot answers natural-language questions, retrieves document evidence, and recommends actions in seconds. A What-If simulator lets managers model interventions (expedite, transfer, new inbound, defer) before committing resources.

### Key features
- **Control Tower** — plant-level composite risk scores, KPIs, and a full explainability breakdown
- **AI Copilot** — natural-language Q&A over live analytics + document evidence, no SQL required
- **Deep Dive** — part-level supply position, supplier OTD performance, and customer order risk
- **What-If Simulation** — model expedite/transfer/inbound/defer scenarios and see risk-reduction update live
- **Document Intelligence** — 90 operational documents (supplier delay notices, quality holds, SLAs) indexed via Cortex Search

## Architecture

| Layer | Contents |
|---|---|
| **Data** (`CORE` schema) | 11-table star schema — `DIM_CUSTOMER`, `DIM_SUPPLIER`, `DIM_PART`, `DIM_PLANT`, `FACT_CUSTOMER_ORDER`, `FACT_INVENTORY`, `FACT_PURCHASE_ORDER`, `FACT_SHIPMENT`, plus bridge tables — and `SUPPLY_CHAIN_DOCUMENTS` (90 unstructured docs) |
| **Analytics** (`ANALYTICS` schema) | 7 views computing plant/part/supplier/customer risk in real time (CTEs + window functions) |
| **AI / Cortex** (`AI` schema) | Cortex Search Service (`arctic-embed-m-v1.5`), Semantic View `SV_SUPPLY_CHAIN_COPILOT`, Cortex LLM `llama3.1-70b` |
| **Application** (`APP` schema) | Streamlit in Snowflake app with 3 tabs — Control Tower, Deep Dive, What-If — plus an embedded AI Copilot panel |

Built conversationally with **CoCo CLI** skills: `sql-author`, `data-discovery` + `dynamic-tables`, `document-intelligence`, `cortex-ai-function-studio`, `agent-studio`, and `streamlit-in-workspaces`.

## Repository contents

```
streamlit_app.py                  # App source (also mirrored under streamlit_app/ for deployment)
streamlit_app/                    # Snowflake CLI project (snow streamlit deploy)
  ├─ streamlit_app.py
  ├─ snowflake.yml
  ├─ pyproject.toml
  └─ .streamlit/config.toml
generate_ppt.py                   # Helper script to generate the pitch deck
Supply_Chain_Copilot_Hackathon.pptx
Supply_Chain_Copilot_Demo.mp4     # Recorded walkthrough
```

## Running / deploying

```bash
# Deploy the Streamlit-in-Snowflake app
cd streamlit_app
snow streamlit deploy
```

The app connects via `st.connection("snowflake", ...)` using your configured Snowflake connection.

## Impact

| | |
|---|---|
| **Risk Visibility** | 0 → real-time composite risk scores across all 5 plants |
| **Time to Insight** | Hours → 5 seconds via natural-language AI Copilot |
| **Revenue Protection** | ₹ Crore-level exposure identified by plant and part |
| **Decision Speed** | What-If scenario simulation in seconds |
