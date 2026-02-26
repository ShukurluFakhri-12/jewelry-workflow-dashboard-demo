# app_rick.py
# Rick Terry-specific Streamlit demo: CAD + Bench workflow + Repair intake
# Data is stored separately in ./data_rick to keep universal demo untouched.

from __future__ import annotations

import os
from datetime import date
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Rick Terry | Workflow Demo", layout="wide")

# -----------------------------
# Rick-specific config
# -----------------------------
DATA_DIR = "data_rick"
CUSTOM_FILE = os.path.join(DATA_DIR, "custom_jobs_rick.csv")
REPAIR_FILE = os.path.join(DATA_DIR, "repair_jobs_rick.csv")

CAD_TEAM = ["CAD-1", "CAD-2", "CAD-3"]
BENCH_TEAM = ["Bench-1", "Bench-2", "Bench-3", "Bench-4"]
FRONT_DESK = ["Front Desk"]
ALL_ASSIGNEES = CAD_TEAM + BENCH_TEAM + FRONT_DESK

CUSTOM_STATUSES = [
    "Consultation",
    "Design Sketch",
    "CAD Modeling",
    "3D Approval",
    "Casting",
    "Stone Setting",
    "Final Polish",
    "Ready for Pickup",
    "Completed",
]

REPAIR_STATUSES = [
    "Intake",
    "Waiting for Parts",
    "In Progress",
    "Quality Check",
    "Ready for Pickup",
    "Completed",
]

COMPLEXITY = ["S (Simple)", "M (Medium)", "L (Complex)"]

# -----------------------------
# Helpers
# -----------------------------
def ensure_data_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)

def today_iso() -> str:
    return date.today().isoformat()

def to_float(x) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0

def compute_remaining(total: float, deposit: float) -> float:
    rem = total - deposit
    return rem if rem >= 0 else 0.0

def parse_date(s: str):
    try:
        if isinstance(s, str) and s.strip():
            return pd.to_datetime(s).date()
    except Exception:
        return None
    return None

def is_overdue(due_str: str, status: str) -> str:
    if status == "Completed":
        return "No"
    d = parse_date(due_str)
    if d and d < date.today():
        return "Yes"
    return "No"

def money_fmt(x) -> str:
    try:
        return f"${float(x):,.2f}"
    except Exception:
        return "$0.00"

def load_or_init(path: str, kind: str) -> pd.DataFrame:
    ensure_data_dir()
    if os.path.exists(path):
        df = pd.read_csv(path)
        df.columns = [c.strip() for c in df.columns]
        return df

    if kind == "custom":
        df = pd.DataFrame(
            [
                {
                    "Job_ID": "C-RT-1001",
                    "Client": "Example Client",
                    "Item": "Custom engagement ring",
                    "Phase_Owner": "CAD-1",       # who currently owns the next step (CAD or Bench)
                    "Complexity": "M (Medium)",
                    "Status": "CAD Modeling",
                    "Intake_Date": today_iso(),
                    "Due_Date": (date.today()).isoformat(),
                    "Total_Price": 2500.0,
                    "Deposit_Paid": 500.0,
                    "Remaining_Balance": 2000.0,
                    "Paid": "No",
                    "Overdue": "No",
                    "Notes": "Demo record",
                }
            ]
        )
    else:
        df = pd.DataFrame(
            [
                {
                    "Job_ID": "R-RT-2001",
                    "Client": "Example Client",
                    "Item": "Ring",
                    "Repair_Type": "Resizing",
                    "Assigned_To": "Bench-1",
                    "Complexity": "S (Simple)",
                    "Status": "Intake",
                    "Intake_Date": today_iso(),
                    "Promised_Date": "",
                    "Total_Price": 150.0,
                    "Deposit_Paid": 0.0,
                    "Remaining_Balance": 150.0,
                    "Paid": "No",
                    "Overdue": "No",
                    "Notes": "Demo record",
                }
            ]
        )

    df.to_csv(path, index=False)
    return df

def save_df(df: pd.DataFrame, path: str) -> None:
    ensure_data_dir()
    df.to_csv(path, index=False)

# -----------------------------
# Load session state
# -----------------------------
if "custom_df_rick" not in st.session_state:
    st.session_state.custom_df_rick = load_or_init(CUSTOM_FILE, "custom")

if "repair_df_rick" not in st.session_state:
    st.session_state.repair_df_rick = load_or_init(REPAIR_FILE, "repair")

# -----------------------------
# Header
# -----------------------------
st.title("Rick Terry | CAD + Bench Workflow Demo")
st.caption("Custom + Repair visibility layer (does not replace POS). Designed for CAD-to-bench coordination + front desk clarity.")

tab1, tab2, tab3 = st.tabs(["Custom (CAD → Bench)", "Repair Intake", "Front Desk Views"])

# -----------------------------
# CUSTOM TAB
# -----------------------------
with tab1:
    st.subheader("Custom Jobs Pipeline")
    left, right = st.columns([1, 2])

    with left:
        st.markdown("### Add custom job")
        with st.form("add_custom_rick", clear_on_submit=True):
            job_id = st.text_input("Job ID", placeholder="C-RT-1002")
            client = st.text_input("Client", placeholder="Full name")
            item = st.text_input("Item", placeholder="e.g., engagement ring, pendant")
            complexity = st.selectbox("Complexity", COMPLEXITY, index=1)
            status = st.selectbox("Status", CUSTOM_STATUSES, index=2)
            phase_owner = st.selectbox("Phase owner (CAD/Bench)", ALL_ASSIGNEES, index=0)
            intake_date = st.date_input("Intake date", value=date.today())
            due_date = st.date_input("Target due date", value=None)
            total_price = st.number_input("Total price", min_value=0.0, step=50.0, value=0.0)
            deposit_paid = st.number_input("Deposit paid", min_value=0.0, step=50.0, value=0.0)
            notes = st.text_area("Notes", height=80)

            add = st.form_submit_button("Add")

        if add:
            if not job_id.strip() or not client.strip():
                st.error("Job ID and Client are required.")
            else:
                total = to_float(total_price)
                dep = to_float(deposit_paid)
                rem = compute_remaining(total, dep)
                paid = "Yes" if rem == 0 else "No"
                due_str = due_date.isoformat() if due_date else ""
                overdue = is_overdue(due_str, status)

                new_row = {
                    "Job_ID": job_id.strip(),
                    "Client": client.strip(),
                    "Item": item.strip(),
                    "Phase_Owner": phase_owner,
                    "Complexity": complexity,
                    "Status": status,
                    "Intake_Date": intake_date.isoformat(),
                    "Due_Date": due_str,
                    "Total_Price": total,
                    "Deposit_Paid": dep,
                    "Remaining_Balance": rem,
                    "Paid": paid,
                    "Overdue": overdue,
                    "Notes": notes.strip(),
                }

                df = st.session_state.custom_df_rick.copy()
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                # recompute to be safe
                df["Total_Price"] = pd.to_numeric(df["Total_Price"], errors="coerce").fillna(0.0)
                df["Deposit_Paid"] = pd.to_numeric(df["Deposit_Paid"], errors="coerce").fillna(0.0)
                df["Remaining_Balance"] = (df["Total_Price"] - df["Deposit_Paid"]).clip(lower=0.0)
                df["Paid"] = df["Remaining_Balance"].apply(lambda x: "Yes" if float(x) == 0 else "No")
                df["Overdue"] = df.apply(lambda r: is_overdue(str(r.get("Due_Date", "")), str(r.get("Status", ""))), axis=1)

                st.session_state.custom_df_rick = df
                save_df(df, CUSTOM_FILE)
                st.success("Custom job added.")

        st.markdown("---")
        st.markdown("### Filters")
        f_status = st.multiselect("Status", CUSTOM_STATUSES, default=CUSTOM_STATUSES)
        f_owner = st.multiselect("Phase owner", ALL_ASSIGNEES, default=ALL_ASSIGNEES)
        f_overdue = st.selectbox("Overdue", ["All", "Only overdue", "Not overdue"], index=0)
        f_search = st.text_input("Search (job/client/item)", placeholder="type to search")

    with right:
        df = st.session_state.custom_df_rick.copy()

        # numeric + recompute
        df["Total_Price"] = pd.to_numeric(df.get("Total_Price", 0), errors="coerce").fillna(0.0)
        df["Deposit_Paid"] = pd.to_numeric(df.get("Deposit_Paid", 0), errors="coerce").fillna(0.0)
        df["Remaining_Balance"] = (df["Total_Price"] - df["Deposit_Paid"]).clip(lower=0.0)
        df["Paid"] = df["Remaining_Balance"].apply(lambda x: "Yes" if float(x) == 0 else "No")
        df["Overdue"] = df.apply(lambda r: is_overdue(str(r.get("Due_Date", "")), str(r.get("Status", ""))), axis=1)

        # apply filters
        df_f = df[df["Status"].isin(f_status)]
        df_f = df_f[df_f["Phase_Owner"].isin(f_owner)]
        if f_overdue == "Only overdue":
            df_f = df_f[df_f["Overdue"] == "Yes"]
        elif f_overdue == "Not overdue":
            df_f = df_f[df_f["Overdue"] == "No"]

        if f_search.strip():
            q = f_search.strip().lower()
            mask = (
                df_f["Job_ID"].astype(str).str.lower().str.contains(q)
                | df_f["Client"].astype(str).str.lower().str.contains(q)
                | df_f["Item"].astype(str).str.lower().str.contains(q)
            )
            df_f = df_f[mask]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Open customs", int((df_f["Status"] != "Completed").sum()))
        c2.metric("Overdue", int((df_f["Overdue"] == "Yes").sum()))
        c3.metric("Listed revenue", money_fmt(df_f["Total_Price"].sum()))
        c4.metric("Outstanding", money_fmt(df_f["Remaining_Balance"].sum()))

        st.markdown("### Editable table")
        st.info("Edit status, owner, due dates, deposits. Remaining/Paid/Overdue auto-update.")

        cols = [
            "Job_ID", "Client", "Item",
            "Complexity", "Phase_Owner", "Status",
            "Intake_Date", "Due_Date",
            "Total_Price", "Deposit_Paid",
            "Remaining_Balance", "Paid", "Overdue",
            "Notes",
        ]
        for c in cols:
            if c not in df.columns:
                df[c] = ""

        edited = st.data_editor(
            df[cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Status": st.column_config.SelectboxColumn("Status", options=CUSTOM_STATUSES),
                "Phase_Owner": st.column_config.SelectboxColumn("Phase owner", options=ALL_ASSIGNEES),
                "Complexity": st.column_config.SelectboxColumn("Complexity", options=COMPLEXITY),
                "Total_Price": st.column_config.NumberColumn("Total", min_value=0.0, step=50.0),
                "Deposit_Paid": st.column_config.NumberColumn("Deposit", min_value=0.0, step=50.0),
                "Remaining_Balance": st.column_config.NumberColumn("Remaining", disabled=True),
                "Paid": st.column_config.TextColumn("Paid", disabled=True),
                "Overdue": st.column_config.TextColumn("Overdue", disabled=True),
            },
            key="custom_rick_editor",
        )

        if edited is not None:
            df2 = edited.copy()
            df2["Total_Price"] = pd.to_numeric(df2["Total_Price"], errors="coerce").fillna(0.0)
            df2["Deposit_Paid"] = pd.to_numeric(df2["Deposit_Paid"], errors="coerce").fillna(0.0)
            df2["Remaining_Balance"] = (df2["Total_Price"] - df2["Deposit_Paid"]).clip(lower=0.0)
            df2["Paid"] = df2["Remaining_Balance"].apply(lambda x: "Yes" if float(x) == 0 else "No")
            df2["Overdue"] = df2.apply(lambda r: is_overdue(str(r.get("Due_Date", "")), str(r.get("Status", ""))), axis=1)

            st.session_state.custom_df_rick = df2
            save_df(df2, CUSTOM_FILE)

        st.markdown("### Pipeline view")
        stage_counts = st.session_state.custom_df_rick["Status"].value_counts().reindex(CUSTOM_STATUSES, fill_value=0)
        st.bar_chart(stage_counts)

        with st.expander("Export / Reset"):
            st.download_button(
                "Download custom CSV",
                data=st.session_state.custom_df_rick.to_csv(index=False).encode("utf-8"),
                file_name="custom_jobs_rick.csv",
                mime="text/csv",
            )
            if st.button("Reset Rick custom demo data"):
                if os.path.exists(CUSTOM_FILE):
                    os.remove(CUSTOM_FILE)
                st.session_state.custom_df_rick = load_or_init(CUSTOM_FILE, "custom")
                st.success("Reset done.")

# -----------------------------
# REPAIR TAB
# -----------------------------
with tab2:
    st.subheader("Repair Intake + Load Distribution")
    left, right = st.columns([1, 2])

    with left:
        st.markdown("### Add repair job")
        with st.form("add_repair_rick", clear_on_submit=True):
            job_id = st.text_input("Job ID", placeholder="R-RT-2002")
            client = st.text_input("Client", placeholder="Full name")
            item = st.text_input("Item", placeholder="e.g., ring, chain, bracelet")
            repair_type = st.text_input("Repair type", placeholder="e.g., sizing, prong retip, solder")
            assigned = st.selectbox("Assigned to (bench)", BENCH_TEAM, index=0)
            complexity = st.selectbox("Complexity", COMPLEXITY, index=0, key="rep_complexity")
            status = st.selectbox("Status", REPAIR_STATUSES, index=0)
            intake_date = st.date_input("Intake date", value=date.today(), key="rep_intake")
            promised = st.date_input("Promised date (optional)", value=None, key="rep_promised")
            total_price = st.number_input("Total price", min_value=0.0, step=25.0, value=0.0, key="rep_total")
            deposit_paid = st.number_input("Deposit paid", min_value=0.0, step=25.0, value=0.0, key="rep_dep")
            notes = st.text_area("Notes", height=80, key="rep_notes")

            add = st.form_submit_button("Add")

        if add:
            if not job_id.strip() or not client.strip():
                st.error("Job ID and Client are required.")
            else:
                total = to_float(total_price)
                dep = to_float(deposit_paid)
                rem = compute_remaining(total, dep)
                paid = "Yes" if rem == 0 else "No"
                prom_str = promised.isoformat() if promised else ""
                overdue = is_overdue(prom_str, status)

                new_row = {
                    "Job_ID": job_id.strip(),
                    "Client": client.strip(),
                    "Item": item.strip(),
                    "Repair_Type": repair_type.strip(),
                    "Assigned_To": assigned,
                    "Complexity": complexity,
                    "Status": status,
                    "Intake_Date": intake_date.isoformat(),
                    "Promised_Date": prom_str,
                    "Total_Price": total,
                    "Deposit_Paid": dep,
                    "Remaining_Balance": rem,
                    "Paid": paid,
                    "Overdue": overdue,
                    "Notes": notes.strip(),
                }

                df = st.session_state.repair_df_rick.copy()
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

                df["Total_Price"] = pd.to_numeric(df["Total_Price"], errors="coerce").fillna(0.0)
                df["Deposit_Paid"] = pd.to_numeric(df["Deposit_Paid"], errors="coerce").fillna(0.0)
                df["Remaining_Balance"] = (df["Total_Price"] - df["Deposit_Paid"]).clip(lower=0.0)
                df["Paid"] = df["Remaining_Balance"].apply(lambda x: "Yes" if float(x) == 0 else "No")
                df["Overdue"] = df.apply(lambda r: is_overdue(str(r.get("Promised_Date", "")), str(r.get("Status", ""))), axis=1)

                st.session_state.repair_df_rick = df
                save_df(df, REPAIR_FILE)
                st.success("Repair job added.")

        st.markdown("---")
        st.markdown("### Filters")
        f_status = st.multiselect("Status", REPAIR_STATUSES, default=REPAIR_STATUSES, key="rep_status_f")
        f_bench = st.multiselect("Bench", BENCH_TEAM, default=BENCH_TEAM, key="rep_bench_f")
        f_overdue = st.selectbox("Overdue", ["All", "Only overdue", "Not overdue"], index=0, key="rep_over_f")
        f_search = st.text_input("Search (job/client/item/repair)", placeholder="type to search", key="rep_search_f")

    with right:
        df = st.session_state.repair_df_rick.copy()

        df["Total_Price"] = pd.to_numeric(df.get("Total_Price", 0), errors="coerce").fillna(0.0)
        df["Deposit_Paid"] = pd.to_numeric(df.get("Deposit_Paid", 0), errors="coerce").fillna(0.0)
        df["Remaining_Balance"] = (df["Total_Price"] - df["Deposit_Paid"]).clip(lower=0.0)
        df["Paid"] = df["Remaining_Balance"].apply(lambda x: "Yes" if float(x) == 0 else "No")
        df["Overdue"] = df.apply(lambda r: is_overdue(str(r.get("Promised_Date", "")), str(r.get("Status", ""))), axis=1)

        df_f = df[df["Status"].isin(f_status)]
        df_f = df_f[df_f["Assigned_To"].isin(f_bench)]

        if f_overdue == "Only overdue":
            df_f = df_f[df_f["Overdue"] == "Yes"]
        elif f_overdue == "Not overdue":
            df_f = df_f[df_f["Overdue"] == "No"]

        if f_search.strip():
            q = f_search.strip().lower()
            mask = (
                df_f["Job_ID"].astype(str).str.lower().str.contains(q)
                | df_f["Client"].astype(str).str.lower().str.contains(q)
                | df_f["Item"].astype(str).str.lower().str.contains(q)
                | df_f["Repair_Type"].astype(str).str.lower().str.contains(q)
            )
            df_f = df_f[mask]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Open repairs", int((df_f["Status"] != "Completed").sum()))
        c2.metric("Overdue", int((df_f["Overdue"] == "Yes").sum()))
        c3.metric("Listed revenue", money_fmt(df_f["Total_Price"].sum()))
        c4.metric("Outstanding", money_fmt(df_f["Remaining_Balance"].sum()))

        st.markdown("### Editable repair table")
        cols = [
            "Job_ID", "Client", "Item", "Repair_Type",
            "Assigned_To", "Complexity", "Status",
            "Intake_Date", "Promised_Date",
            "Total_Price", "Deposit_Paid",
            "Remaining_Balance", "Paid", "Overdue",
            "Notes",
        ]
        for c in cols:
            if c not in df.columns:
                df[c] = ""

        edited = st.data_editor(
            df[cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Assigned_To": st.column_config.SelectboxColumn("Assigned", options=BENCH_TEAM),
                "Status": st.column_config.SelectboxColumn("Status", options=REPAIR_STATUSES),
                "Complexity": st.column_config.SelectboxColumn("Complexity", options=COMPLEXITY),
                "Total_Price": st.column_config.NumberColumn("Total", min_value=0.0, step=25.0),
                "Deposit_Paid": st.column_config.NumberColumn("Deposit", min_value=0.0, step=25.0),
                "Remaining_Balance": st.column_config.NumberColumn("Remaining", disabled=True),
                "Paid": st.column_config.TextColumn("Paid", disabled=True),
                "Overdue": st.column_config.TextColumn("Overdue", disabled=True),
            },
            key="repair_rick_editor",
        )

        if edited is not None:
            df2 = edited.copy()
            df2["Total_Price"] = pd.to_numeric(df2["Total_Price"], errors="coerce").fillna(0.0)
            df2["Deposit_Paid"] = pd.to_numeric(df2["Deposit_Paid"], errors="coerce").fillna(0.0)
            df2["Remaining_Balance"] = (df2["Total_Price"] - df2["Deposit_Paid"]).clip(lower=0.0)
            df2["Paid"] = df2["Remaining_Balance"].apply(lambda x: "Yes" if float(x) == 0 else "No")
            df2["Overdue"] = df2.apply(lambda r: is_overdue(str(r.get("Promised_Date", "")), str(r.get("Status", ""))), axis=1)

            st.session_state.repair_df_rick = df2
            save_df(df2, REPAIR_FILE)

        st.markdown("### Repair load by bench")
        load = st.session_state.repair_df_rick.copy()
        load = load[load["Status"] != "Completed"]
        counts = load["Assigned_To"].value_counts().reindex(BENCH_TEAM, fill_value=0)
        st.bar_chart(counts)

        with st.expander("Export / Reset"):
            st.download_button(
                "Download repair CSV",
                data=st.session_state.repair_df_rick.to_csv(index=False).encode("utf-8"),
                file_name="repair_jobs_rick.csv",
                mime="text/csv",
            )
            if st.button("Reset Rick repair demo data"):
                if os.path.exists(REPAIR_FILE):
                    os.remove(REPAIR_FILE)
                st.session_state.repair_df_rick = load_or_init(REPAIR_FILE, "repair")
                st.success("Reset done.")

# -----------------------------
# FRONT DESK VIEWS TAB
# -----------------------------
with tab3:
    st.subheader("Front Desk Views (what matters daily)")

    custom = st.session_state.custom_df_rick.copy()
    repair = st.session_state.repair_df_rick.copy()

    for df in (custom, repair):
        df["Total_Price"] = pd.to_numeric(df.get("Total_Price", 0), errors="coerce").fillna(0.0)
        df["Deposit_Paid"] = pd.to_numeric(df.get("Deposit_Paid", 0), errors="coerce").fillna(0.0)
        df["Remaining_Balance"] = (df["Total_Price"] - df["Deposit_Paid"]).clip(lower=0.0)
        df["Paid"] = df["Remaining_Balance"].apply(lambda x: "Yes" if float(x) == 0 else "No")

    custom["Overdue"] = custom.apply(lambda r: is_overdue(str(r.get("Due_Date", "")), str(r.get("Status", ""))), axis=1)
    repair["Overdue"] = repair.apply(lambda r: is_overdue(str(r.get("Promised_Date", "")), str(r.get("Status", ""))), axis=1)

    col1, col2, col3 = st.columns(3)
    col1.metric("Pickup-ready customs (unpaid)", int(((custom["Status"] == "Ready for Pickup") & (custom["Paid"] == "No")).sum()))
    col2.metric("Overdue customs", int((custom["Overdue"] == "Yes").sum()))
    col3.metric("Overdue repairs", int((repair["Overdue"] == "Yes").sum()))

    st.markdown("---")
    st.markdown("### Pickup-ready but unpaid (Custom)")
    pickup_unpaid = custom[(custom["Status"] == "Ready for Pickup") & (custom["Paid"] == "No")].copy()
    if pickup_unpaid.empty:
        st.success("No pickup-ready unpaid custom jobs in demo data.")
    else:
        show_cols = ["Job_ID", "Client", "Item", "Phase_Owner", "Due_Date", "Total_Price", "Deposit_Paid", "Remaining_Balance"]
        st.dataframe(pickup_unpaid[show_cols], use_container_width=True, hide_index=True)

    st.markdown("### Repairs ready for pickup (unpaid)")
    rep_ready_unpaid = repair[(repair["Status"] == "Ready for Pickup") & (repair["Paid"] == "No")].copy()
    if rep_ready_unpaid.empty:
        st.info("No pickup-ready unpaid repair jobs in demo data.")
    else:
        show_cols = ["Job_ID", "Client", "Item", "Repair_Type", "Assigned_To", "Promised_Date", "Remaining_Balance"]
        st.dataframe(rep_ready_unpaid[show_cols], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### Overdue list (Custom + Repair)")
    custom_over = custom[custom["Overdue"] == "Yes"].copy()
    custom_over["Type"] = "Custom"
    repair_over = repair[repair["Overdue"] == "Yes"].copy()
    repair_over["Type"] = "Repair"
    over = pd.concat([custom_over, repair_over], ignore_index=True, sort=False)
    if over.empty:
        st.success("No overdue jobs in demo data.")
    else:
        cols = [c for c in ["Type", "Job_ID", "Client", "Item", "Status", "Phase_Owner", "Assigned_To", "Due_Date", "Promised_Date"] if c in over.columns]
        st.dataframe(over[cols], use_container_width=True, hide_index=True)
