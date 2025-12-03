import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt  # kept, even though we don't draw a chart now
from io import BytesIO
from fpdf import FPDF
from difflib import SequenceMatcher
import re

# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="FTZ Savings AI Calculator",
    layout="wide",
    page_icon="💼",
)

st.title(" FTZ Savings – Agentic AI Calculator")
st.caption("Professional FTZ vs non-FTZ cost comparison with AI insights and exports.")

# ================== LAYOUT: TWO MAIN COLUMNS ==================
left_col, right_col = st.columns([1.0, 1.3])

# ================== LEFT: CUSTOMER DATA ASSUMPTIONS ==================
with left_col:
    st.markdown("### Customer Data Assumptions")

    c1, c2 = st.columns(2)

    with c1:
        shipments_per_week = st.number_input(
            "Number of Shipments per Week", min_value=1, value=2
        )
        avg_import_value = st.number_input(
            "Average Imported Value per Entry ($)",
            min_value=1_000,
            value=50_000,
            step=1_000,
        )
        export_sales_pct = st.number_input(
            "Export Sales (% of Sales)", min_value=0.0, max_value=100.0, value=1.0, step=0.1
        )
        off_spec_pct = st.number_input(
            "Off-Specification Merchandise (% of Sales)",
            min_value=0.0,
            max_value=100.0,
            value=0.25,
            step=0.05,
        )

    with c2:
        mpf_pct = st.number_input(
            "Merchandise Processing Fee (MPF % of imports)",
            min_value=0.0,
            max_value=100.0,
            value=0.3464,
            step=0.01,
        )
        hmf_pct = st.number_input(
            "Harbor Maintenance Fee (HMF % of imports)",
            min_value=0.0,
            max_value=100.0,
            value=0.1250,
            step=0.01,
        )
        broker_cost = st.number_input(
            "Broker Costs ($/entry)", min_value=0.0, value=125.0, step=25.0
        )
        avg_duty_pct = st.number_input(
            "Average Duty %", min_value=0.0, max_value=100.0, value=30.0, step=1.0
        )

    total_import_value = shipments_per_week * avg_import_value * 52
    st.markdown(
        f"**Total Value Imported (Annual):** :green[${total_import_value:,.0f}]"
    )

    # --- WITH FTZ operating costs ---
    st.markdown("### Costs With FTZ (Annual)")
    oc1, oc2, oc3, oc4 = st.columns(4)
    with oc1:
        ftz_consult = st.number_input("FTZ Consulting", value=50_000)
    with oc2:
        ftz_mgmt = st.number_input("FTZ Management", value=150_000)
    with oc3:
        ftz_software = st.number_input("FTZ Software Fee", value=40_000)
    with oc4:
        ftz_bond = st.number_input("FTZ Operator Bond", value=1_000)

    # --- WITHOUT FTZ operating costs ---
    st.markdown("### Costs Without FTZ (Annual)")
    n1, n2, n3, n4 = st.columns(4)
    with n1:
        noftz_consult = st.number_input("FTZ Consulting ", value=0)
    with n2:
        noftz_mgmt = st.number_input("FTZ Management ", value=0)
    with n3:
        noftz_software = st.number_input("FTZ Software Fee ", value=0)
    with n4:
        noftz_bond = st.number_input("FTZ Operator Bond ", value=0)

# ================== CALCULATIONS (MATCH EXCEL FORMULAS) ==================
export_sales = export_sales_pct / 100.0
off_spec = off_spec_pct / 100.0
mpf_rate = mpf_pct / 100.0
hmf_rate = hmf_pct / 100.0
avg_duty = avg_duty_pct / 100.0

# Duty
total_duty = total_import_value * avg_duty
duty_saved_export = total_import_value * export_sales * avg_duty
duty_saved_offspec = total_import_value * off_spec * avg_duty

total_net_duty_no_ftz = total_duty
total_net_duty_with_ftz = total_duty - duty_saved_export - duty_saved_offspec

# MPF: per-entry/per-week with cap 634.62
entries_per_year = shipments_per_week * 52
per_entry_mpf = min(avg_import_value * mpf_rate, 634.62)
mpf_no_ftz = per_entry_mpf * entries_per_year

per_week_mpf = min(shipments_per_week * avg_import_value * mpf_rate, 634.62)
mpf_with_ftz = per_week_mpf * 52

# Broker + HMF
total_broker_hmf_no_ftz = (
    entries_per_year * broker_cost
    + shipments_per_week * avg_import_value * hmf_rate
)

total_broker_hmf_with_ftz = (
    52 * broker_cost
    + shipments_per_week * avg_import_value * hmf_rate
)

# Totals before operating costs (row "Totals")
totals_without_ftz = (
    total_net_duty_no_ftz + mpf_no_ftz + total_broker_hmf_no_ftz
)
totals_with_ftz_pre_op = (
    total_net_duty_with_ftz + mpf_with_ftz + total_broker_hmf_with_ftz
)

# Operating costs
noftz_operating_costs = noftz_consult + noftz_mgmt + noftz_software + noftz_bond
ftz_operating_costs = ftz_consult + ftz_mgmt + ftz_software + ftz_bond

# Fully-loaded totals (used for Net Savings to Brand)
total_cost_without_ftz_full = totals_without_ftz + noftz_operating_costs
total_cost_with_ftz_full = totals_with_ftz_pre_op + ftz_operating_costs

net_savings_to_brand = total_cost_without_ftz_full - total_cost_with_ftz_full

# ================== RIGHT: COST COMPARISON TABLE ==================
with right_col:
    st.markdown("### FTZ Cost Comparison")

    summary_data = {
        "Category": [
            "Total Duty",
            "Duty Saved of Exported Goods",
            "Duty Saved on Non-Spec Goods",
            "Total Net Duty",
            "Total MPF",
            "Total Broker Costs + HMF",
            "Totals",
            "FTZ Consulting",
            "FTZ Management",
            "FTZ Software Fee",
            "FTZ Operator Bond",
            "Total Operating Costs",
            "Net Savings to Brand",
        ],
        "Without FTZ ($)": [
            total_duty,
            0.0,
            0.0,
            total_net_duty_no_ftz,
            mpf_no_ftz,
            total_broker_hmf_no_ftz,
            totals_without_ftz,
            noftz_consult,
            noftz_mgmt,
            noftz_software,
            noftz_bond,
            noftz_operating_costs,
            total_cost_without_ftz_full,
        ],
        "With FTZ ($)": [
            total_duty,
            -duty_saved_export,
            -duty_saved_offspec,
            total_net_duty_with_ftz,
            mpf_with_ftz,
            total_broker_hmf_with_ftz,
            totals_with_ftz_pre_op,
            ftz_consult,
            ftz_mgmt,
            ftz_software,
            ftz_bond,
            ftz_operating_costs,
            total_cost_with_ftz_full,
        ],
        "FTZ Savings ($)": [
            0.0,
            duty_saved_export,
            duty_saved_offspec,
            total_net_duty_no_ftz - total_net_duty_with_ftz,
            mpf_no_ftz - mpf_with_ftz,
            total_broker_hmf_no_ftz - total_broker_hmf_with_ftz,
            totals_without_ftz - totals_with_ftz_pre_op,
            noftz_consult - ftz_consult,
            noftz_mgmt - ftz_mgmt,
            noftz_software - ftz_software,
            noftz_bond - ftz_bond,
            noftz_operating_costs - ftz_operating_costs,
            net_savings_to_brand,
        ],
    }

    summary_df = pd.DataFrame(summary_data)

    numeric_cols = ["Without FTZ ($)", "With FTZ ($)", "FTZ Savings ($)"]

    def money_fmt(x):
        if pd.isna(x):
            return ""
        if isinstance(x, (int, float)):
            if x < 0:
                return f"(${abs(x):,.0f})"
            else:
                return f"${x:,.0f}"
        return x

    def red_if_negative(v):
        if isinstance(v, (int, float)) and v < 0:
            return "color: red;"
        return ""

    styled = (
        summary_df.style.format(money_fmt, subset=numeric_cols)
        .applymap(red_if_negative, subset=numeric_cols)
    )

    st.dataframe(styled, use_container_width=True, height=560)

# ================== AI INSIGHTS + EXPORTS SIDE BY SIDE ==================
st.markdown("---")
insights_col, export_col = st.columns([1.4, 1.0])

# --- AI Assistant Insights ---
with insights_col:
    st.subheader(" AI Assistant Insights")

    base_without = total_cost_without_ftz_full if total_cost_without_ftz_full != 0 else 1.0
    savings_pct = (net_savings_to_brand / base_without) * 100

    ai_text = f"""
Based on your current assumptions, your company could realize approximately **${net_savings_to_brand:,.0f} in net annual savings** by operating in an FTZ.

**Key drivers behind this result:**
- Duty Savings on Exports & Non-Spec Goods: ${duty_saved_export + duty_saved_offspec:,.0f}
- MPF Savings from weekly entry structure: ${mpf_no_ftz - mpf_with_ftz:,.0f}
- Broker + HMF Savings: ${(total_broker_hmf_no_ftz - total_broker_hmf_with_ftz):,.0f}
- Costs Without FTZ vs Costs With FTZ: ${noftz_operating_costs:,.0f} -> ${ftz_operating_costs:,.0f}

This equates to roughly **{savings_pct:.2f}% reduction** in your fully loaded logistics cost base, assuming shipment volumes and duty rates remain consistent.
"""
    st.info(ai_text)

# --- Export Results ---
with export_col:
    st.subheader("📄 Export Results")

    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        summary_df.to_excel(writer, index=False, sheet_name="FTZ Summary")
        sheet = writer.sheets["FTZ Summary"]
        sheet.set_column("A:D", 30)

    st.download_button(
        label="📊 Download Excel Summary",
        data=excel_buffer.getvalue(),
        file_name="FTZ_Savings_Summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    if st.button("📄 Generate PDF Summary Report"):
        # Sanitize Unicode for FPDF (Latin-1 only)
        safe_ai_text = (
            ai_text.replace("→", "->")
            .encode("latin-1", "ignore")
            .decode("latin-1")
        )

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, txt="FTZ Savings Summary Report", ln=True, align="C")
        pdf.set_font("Arial", "", 12)
        pdf.ln(10)
        pdf.multi_cell(0, 8, safe_ai_text)
        pdf.ln(5)
        # Simple currency fmt
        def _money_fmt(x):
            try:
                return f"${x:,.0f}" if x >= 0 else f"(${abs(x):,.0f})"
            except Exception:
                return str(x)
        pdf.cell(0, 10, f"Net Savings to Brand: {_money_fmt(net_savings_to_brand)}", ln=True)

        pdf_bytes = pdf.output(dest="S")
        if isinstance(pdf_bytes, str):
            pdf_bytes = pdf_bytes.encode("latin-1", "ignore")
        pdf_output = BytesIO(pdf_bytes)

        st.download_button(
            label="⬇️ Download PDF Report",
            data=pdf_output,
            file_name="FTZ_Savings_Report.pdf",
            mime="application/pdf",
        )

# ================== CHATBOT PANEL (FA Q + FUZZY MATCH) ==================
st.markdown("---")
st.subheader("💬 FTZ Chatbot Assistant")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---- Helpers for chatbot ----
def dollars(x):
    try:
        return f"${x:,.0f}" if x >= 0 else f"(${abs(x):,.0f})"
    except Exception:
        return str(x)

def normalize(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s\-\+\.%/]", " ", text)  # keep basic chars
    text = re.sub(r"\s+", " ", text).strip()
    return text

def tokens(text: str) -> set:
    return set(normalize(text).split())

def fuzzy_score(a: str, b: str) -> float:
    # Hybrid: token overlap + sequence ratio
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        overlap = 0.0
    else:
        overlap = len(ta & tb) / max(1, len(ta))
    ratio = SequenceMatcher(None, normalize(a), normalize(b)).ratio()
    # Weighted score: more weight to overlap (intent keywords), some to ratio
    return 0.65 * overlap + 0.35 * ratio

# Derived metrics for dynamic answers
roi = (net_savings_to_brand / ftz_operating_costs) if ftz_operating_costs else 0.0
payback_years = (1 / roi) if roi > 0 else None

# Base 20 FAQs with synonyms (patterns)
faqs = [
    {"patterns": ["net savings", "savings to brand", "how much will we save", "annual savings"],
     "answer": lambda: f"Your **Net Savings to Brand** is {dollars(net_savings_to_brand)} per year, comparing fully-loaded Non-FTZ ({dollars(total_cost_without_ftz_full)}) vs FTZ ({dollars(total_cost_with_ftz_full)})."},
    {"patterns": ["roi", "return on investment", "investment return"],
     "answer": lambda: f"Your estimated **ROI** is **{roi*100:.1f}%** based on FTZ program costs of {dollars(ftz_operating_costs)} and annual net savings of {dollars(net_savings_to_brand)}."},
    {"patterns": ["payback", "break even", "break-even", "breakeven"],
     "answer": lambda: ("With the current assumptions, **payback period** is "
                        + (f"~{payback_years:.2f} years." if payback_years else "not reached (net savings do not exceed annual FTZ program costs)."))},
    {"patterns": ["duty saved export", "exported goods duty", "export duty savings", "export savings"],
     "answer": lambda: f"Duty saved on **exported goods** is {dollars(duty_saved_export)} per year."},
    {"patterns": ["non-spec", "off-spec", "scrap duty", "off spec savings"],
     "answer": lambda: f"Duty saved on **non-spec/off-spec** goods is {dollars(duty_saved_offspec)} per year."},
    {"patterns": ["total duty without", "duty baseline", "total duty non ftz", "base duty"],
     "answer": lambda: f"**Total Duty** (baseline) is {dollars(total_duty)} at an average duty rate of {avg_duty_pct:.2f}%."},
    {"patterns": ["net duty without", "net duty non ftz", "without ftz net duty"],
     "answer": lambda: f"**Total Net Duty – Without FTZ** is {dollars(total_net_duty_no_ftz)}."},
    {"patterns": ["net duty with", "net duty ftz", "with ftz net duty"],
     "answer": lambda: f"**Total Net Duty – With FTZ** is {dollars(total_net_duty_with_ftz)}."},
    {"patterns": ["mpf without", "mpf non ftz", "without ftz mpf"],
     "answer": lambda: f"**Total MPF – Without FTZ** is {dollars(mpf_no_ftz)} using per-entry MPF with the $634.62 cap."},
    {"patterns": ["mpf with", "mpf ftz", "with ftz mpf"],
     "answer": lambda: f"**Total MPF – With FTZ** is {dollars(mpf_with_ftz)} using weekly consolidated entries and the $634.62 cap."},
    {"patterns": ["broker and hmf without", "hmf without", "broker without"],
     "answer": lambda: f"**Total Broker + HMF – Without FTZ** is {dollars(total_broker_hmf_no_ftz)}."},
    {"patterns": ["broker and hmf with", "hmf with", "broker with"],
     "answer": lambda: f"**Total Broker + HMF – With FTZ** is {dollars(total_broker_hmf_with_ftz)}."},
    {"patterns": ["totals without ftz", "grand total without", "without totals"],
     "answer": lambda: f"**Totals – Without FTZ (pre-op costs)**: {dollars(totals_without_ftz)}."},
    {"patterns": ["totals with ftz", "grand total with", "with totals"],
     "answer": lambda: f"**Totals – With FTZ (pre-op costs)**: {dollars(totals_with_ftz_pre_op)}."},
    {"patterns": ["operating costs with ftz", "ftz program cost", "ftz cost breakdown"],
     "answer": lambda: f"**FTZ Program Operating Costs** total {dollars(ftz_operating_costs)} (Consulting {dollars(ftz_consult)}, Management {dollars(ftz_mgmt)}, Software {dollars(ftz_software)}, Bond {dollars(ftz_bond)})."},
    {"patterns": ["operating costs without", "non ftz operating", "without operating costs"],
     "answer": lambda: f"**Non-FTZ Operating Costs** total {dollars(noftz_operating_costs)} (Consulting {dollars(noftz_consult)}, Management {dollars(noftz_mgmt)}, Software {dollars(noftz_software)}, Bond {dollars(noftz_bond)})."},
    {"patterns": ["entries per year", "how many entries", "shipments per week", "entries"],
     "answer": lambda: f"You have **{shipments_per_week} shipments/week**, i.e. **{entries_per_year} entries/year** without FTZ; with FTZ, **52** weekly consolidated entries."},
    {"patterns": ["average duty", "duty rate", "avg duty"],
     "answer": lambda: f"The **Average Duty %** used is **{avg_duty_pct:.2f}%**."},
    {"patterns": ["why negative", "why loss", "why not saving", "savings negative"],
     "answer": lambda: ("Savings can be negative when **FTZ program costs** and/or **broker/HMF/MPF impacts** outweigh duty savings. "
                        f"Currently: Net savings is {dollars(net_savings_to_brand)}. Review FTZ program costs ({dollars(ftz_operating_costs)}), "
                        f"export/off-spec rates, broker cost ({dollars(broker_cost)} per entry) and shipment frequency ({shipments_per_week}/week).")},
    {"patterns": ["how to export", "download", "excel", "pdf"],
     "answer": lambda: "Use **Export Results** on the right: “📊 Download Excel Summary” or “📄 Generate PDF Summary Report”."},
]

def answer_from_faq(user_q: str) -> str:
    q = (user_q or "").strip()
    if not q:
        return ""

    best = {"score": 0.0, "answer": None}
    for item in faqs:
        for pat in item["patterns"]:
            s = fuzzy_score(pat, q)
            if s > best["score"]:
                best["score"] = s
                best["answer"] = item["answer"]

    # Threshold tuned for natural phrasing; adjust if needed
    if best["score"] >= 0.58 and best["answer"]:
        return best["answer"]()

    # Fallback escalation (as requested)
    return ("Thank you for your question, we are directing your question to the Customer Success Lead at "
            "MAS US Holdings at FTZCustomerSuccessLead@masholdings.com.")

# ---- UI for chatbot ----
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_question = st.text_input("Ask a question about FTZ savings, duty, or this model:")

if st.button("Ask AI"):
    if user_question.strip():
        response = answer_from_faq(user_question)
        st.session_state.chat_history.append(("You", user_question))
        st.session_state.chat_history.append(("AI", response))

for speaker, text in st.session_state.chat_history:
    if speaker == "You":
        st.markdown(f"**🧑‍💼 You:** {text}")
    else:
        st.markdown(f"**🤖 AI:** {text}")
