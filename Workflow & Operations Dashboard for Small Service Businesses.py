# Workflow & Operations Dashboard for Small Service Businesses

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

import pandas as pd
import streamlit as st

# Config
st.set_page_config(page_title="Service Workflow Dashboard", layout="wide")

DATA_DIR = "data"
CUSTOM_FILE = os.path.join(DATA_DIR, "custom_jobs.csv")
REPAIR_FILE = os.path.join(DATA_DIR, "repair_jobs.csv")

CUSTOM_STATUSES = [
    "Consultation",
    "CAD / Design",
    "Production",
    "Pickup",
    "Completed"
]

REPAIR_STATUSES = [
    "Received",
    "In Progress",
    "Ready",
    "Collected",
    "Completed"
]

# Helpers
def ensure_data_dir() :
    os.makedirs(DATA_DIR, exist_ok=True)


def today_str() -> str:
    return date.today().isoformat()


def safe_float(x) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0


def compute_remaining(total,deposit):
    rem = total - deposit
    if rem >= 0:
        return rem
    else:
        return 0.0


def load_or_init_csv(path,kind):
    ensure_data_dir()
    if os.path.exists(path):
        df = pd.read_csv(path)
        df.columns = [c.strip() for c in df.columns]
        return df
    else:
        cols = ["Order_ID", "Client", "Item", "Assigned_To", "Status", "Intake_Date", "Due_Date", "Total_Price", "Deposit_Paid", "Remaining_Balance", "Paid", "Notes"]
        df = pd.DataFrame(columns=cols)                

    if kind == "custom":
        df = pd.DataFrame(
            [
                {
                    "Order_ID": "C-1001",
                    "Client": "Example Client",
                    "Item" : "New Project",
                    "Status": "Consultation",
                    "Total_Price": 1200.0,
                    "Intake_Date" : today_str()
                                      
                    
                }
            ]
        )
    else:
        df = pd.DataFrame(
            [
                {
                    "Order_ID": "R-2001",
                    "Client": "Example Client",
                    "Status": "Received",
                    "Intake_Date": today_str(),
                    "Repair_Type" : "Repair",
                    "Total_Price": 120.0,
                    "Deposit_Paid": 0.0,
                    "Remaining_Balance": 120.0

                }
            ]
        )

    df.to_csv(path, index=False)
    return df

def save_csv(df,path):
    ensure_data_dir()
    df.to_csv(path, index=False)

def money_fmt(x):
    try:
        number = float(x)
        return f"${number:,.2f}"
    except:
        return "$0.00"

# UI Components

st.title("Service Workflow Dashboard")
st.caption("Custom Orders & Repair tracking system. Works for any service-based business.")

tab1, tab2, tab3 = st.tabs(["Custom Jobs", "Repair Jobs", "Analytics"])

# Load data into session

if "custom_df" not in st.session_state:
    st.session_state.custom_df = load_or_init_csv(CUSTOM_FILE, "custom")

if "repair_df" not in st.session_state:
    st.session_state.repair_df = load_or_init_csv(REPAIR_FILE, "repair")

# CUSTOM JOBS TAB
with tab1:
    st.subheader("Custom Jobs (Consultation → CAD → Production → Pickup)")
    left, right = st.columns([1, 2])

    with left:
        st.markdown("### Add new custom job")
        with st.form("add_custom_form", clear_on_submit=True):
            order_id = st.text_input("Order ID", placeholder="ORD-1001")
            client = st.text_input("Client", placeholder="Full name")
            item = st.text_input("Service/İtem", placeholder="e.g., Repair, Maintenance, Custom build")
            assigned = st.text_input("Assigned To", placeholder="e.g., Specialist name or department")
            status = st.selectbox("Status", CUSTOM_STATUSES, index=0)
            intake_date = st.date_input("Intake Date", value=date.today())
            due_date = st.date_input("Due Date")
            total_price = st.number_input("Total Price", min_value=0.0, step=10.0, value=0.0)
            deposit_paid = st.number_input("Deposit Paid", min_value=0.0, step=10.0, value=0.0)
            notes = st.text_area("Notes (optional)", height=80)

            submitted = st.form_submit_button("Add job")

        if submitted:
            if not order_id.strip():
                st.error("Order ID is required.")
            elif not client.strip():
                st.error("Client is required.")
            else:
                total = safe_float(total_price)
                dep = safe_float(deposit_paid)
                remaining = compute_remaining(total, dep)
                paid = "Yes" if remaining == 0 else "No"

                new_row = {
                    "Order_ID": order_id.strip(),
                    "Client": client.strip(),
                    "Item": item.strip(),
                    "Assigned_To": assigned.strip(),
                    "Status": status,
                    "Intake_Date": intake_date.isoformat(),
                    "Due_Date": due_date.isoformat() if due_date else "",
                    "Total_Price": total,
                    "Deposit_Paid": dep,
                    "Remaining_Balance": remaining,
                    "Paid": paid,
                    "Notes": notes.strip(),
                }

                df = st.session_state.custom_df.copy()
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                st.session_state.custom_df = df
                save_csv(df, CUSTOM_FILE)
                st.success("Custom job added.")

        st.markdown("---")
        st.markdown("### Filters")
        f_status = st.multiselect("Status filter", CUSTOM_STATUSES, default=CUSTOM_STATUSES)
        f_paid = st.selectbox("Paid filter", ["All", "Paid", "Unpaid"], index=0)
        f_search = st.text_input("Search (client / item / order id)", placeholder="type to search")

    with right:
        df = st.session_state.custom_df.copy()
        
        for col in ["Total_Price", "Deposit_Paid", "Remaining_Balance"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        # Recompute remaining + paid (to keep consistent)
        df["Remaining_Balance"] = (df["Total_Price"] - df["Deposit_Paid"]).clip(lower=0.0)
        df["Paid"] = df["Remaining_Balance"].apply(lambda x: "Yes" if float(x) == 0 else "No")

        # Apply filters
        df = df[df["Status"].isin(f_status)]
        if f_paid == "Paid":
            df = df[df["Paid"] == "Yes"]
        elif f_paid == "Unpaid":
            df = df[df["Paid"] == "No"]

        if f_search.strip():
            q = f_search.strip().lower()
            mask = (
                df["Order_ID"].astype(str).str.lower().str.contains(q)
                | df["Client"].astype(str).str.lower().str.contains(q)
                | df["Item"].astype(str).str.lower().str.contains(q)
            )
            df = df[mask]

        # Summary metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Open jobs", int((df["Status"] != "Completed").sum()))
        c2.metric("Completed", int((df["Status"] == "Completed").sum()))
        c3.metric("Total revenue (listed)", money_fmt(df["Total_Price"].sum()))
        c4.metric("Outstanding balance", money_fmt(df["Remaining_Balance"].sum()))

        st.markdown("### Job table (editable)")
        st.info("You can edit statuses, deposits, notes. Click outside a cell to apply changes.")

        editable_cols = [
            "Order_ID",
            "Client",
            "Item",
            "Assigned_To",
            "Status",
            "Intake_Date",
            "Due_Date",
            "Total_Price",
            "Deposit_Paid",
            "Remaining_Balance",
            "Paid",
            "Notes",
        ]

       
        for col in editable_cols:
            if col not in st.session_state.custom_df.columns:
                st.session_state.custom_df[col] = ""

        edited = st.data_editor(
            st.session_state.custom_df[editable_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Status": st.column_config.SelectboxColumn("Status", options=CUSTOM_STATUSES),
                "Total_Price": st.column_config.NumberColumn("Total Price", min_value=0.0, step=10.0),
                "Deposit_Paid": st.column_config.NumberColumn("Deposit Paid", min_value=0.0, step=10.0),
                "Remaining_Balance": st.column_config.NumberColumn("Remaining", disabled=True),
                "Paid": st.column_config.TextColumn("Paid", disabled=True),
            },
            key="custom_editor",
        )

        # Update session + save if changes
        if edited is not None:
            df_all = edited.copy()
            # Fix numeric
            df_all["Total_Price"] = pd.to_numeric(df_all["Total_Price"], errors="coerce").fillna(0.0)
            df_all["Deposit_Paid"] = pd.to_numeric(df_all["Deposit_Paid"], errors="coerce").fillna(0.0)
            df_all["Remaining_Balance"] = (df_all["Total_Price"] - df_all["Deposit_Paid"]).clip(lower=0.0)
            df_all["Paid"] = df_all["Remaining_Balance"].apply(lambda x: "Yes" if float(x) == 0 else "No")

            st.session_state.custom_df = df_all
            save_csv(df_all, CUSTOM_FILE)

        st.markdown("### Stage view (quick scan)")
        stage_counts = st.session_state.custom_df["Status"].value_counts().reindex(CUSTOM_STATUSES, fill_value=0)
        st.bar_chart(stage_counts)

        with st.expander("Export"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.download_button(
                    "Download Custom Jobs CSV",
                    data=st.session_state.custom_df.to_csv(index=False).encode("utf-8"),
                    file_name="custom_jobs.csv",
                    mime="text/csv",
                )
            with col_b:
                if st.button("Reset demo custom data"):
                    if os.path.exists(CUSTOM_FILE):
                        os.remove(CUSTOM_FILE)
                    st.session_state.custom_df = load_or_init_csv(CUSTOM_FILE, "custom")
                    st.success("Reset done (refresh if needed).")

# REPAIR JOBS TAB
with tab2:
    st.subheader("Repair Jobs (Intake → Bench → Pickup)")
    left, right = st.columns([1, 2])

    with left:
        st.markdown("### Add new repair job")
        with st.form("add_repair_form", clear_on_submit=True):
            order_id = st.text_input("Order ID", placeholder="R-2002")
            client = st.text_input("Client", placeholder="Full name")
            item = st.text_input("Item", placeholder="e.g., laptop, bracelet, Watch")
            repair_type = st.text_input("Repair Type", placeholder="e.g., Screen replacement, Battery change")
            assigned = st.text_input("Assigned To", placeholder="e.g., Repair Team")
            status = st.selectbox("Status", REPAIR_STATUSES, index=0)
            intake_date = st.date_input("Intake Date", value=date.today(), key="repair_intake_date")
            est_completion = st.date_input("Estimated Completion", key="repair_est")
            total_price = st.number_input("Total Price", min_value=0.0, step=10.0, value=0.0, key="repair_total")
            deposit_paid = st.number_input("Deposit Paid", min_value=0.0, step=10.0, value=0.0, key="repair_dep")
            notes = st.text_area("Notes (optional)", height=80, key="repair_notes")

            submitted = st.form_submit_button("Add repair order")

        if submitted:
            if not order_id.strip():
                st.error("Order ID is required.")
            elif not client.strip():
                st.error("Client is required.")
            else:
                total = safe_float(total_price)
                dep = safe_float(deposit_paid)
                remaining = compute_remaining(total, dep)
                paid = "Yes" if remaining == 0 else "No"

                new_row = {
                    "Order_ID": order_id.strip(),
                    "Client": client.strip(),
                    "Item": item.strip(),
                    "Repair_Type": repair_type.strip(),
                    "Assigned_To": assigned.strip(),
                    "Status": status,
                    "Intake_Date": intake_date.isoformat(),
                    "Est_Completion": est_completion.isoformat() if est_completion else "",
                    "Total_Price": total,
                    "Deposit_Paid": dep,
                    "Remaining_Balance": remaining,
                    "Paid": paid,
                    "Notes": notes.strip(),
                }

                df = st.session_state.repair_df.copy()
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                st.session_state.repair_df = df
                save_csv(df, REPAIR_FILE)
                st.success("Repair job added.")

        st.markdown("---")
        st.markdown("### Filters")
        f_status = st.multiselect("Status filter", REPAIR_STATUSES, default=REPAIR_STATUSES, key="repair_status_filter")
        f_paid = st.selectbox("Paid filter", ["All", "Paid", "Unpaid"], index=0, key="repair_paid_filter")
        f_search = st.text_input("Search (client / item / job id)", placeholder="type to search", key="repair_search")

    with right:
        df = st.session_state.repair_df.copy()

        for col in ["Total_Price", "Deposit_Paid", "Remaining_Balance"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        df["Remaining_Balance"] = (df["Total_Price"] - df["Deposit_Paid"]).clip(lower=0.0)
        df["Paid"] = df["Remaining_Balance"].apply(lambda x: "Yes" if float(x) == 0 else "No")

        df_f = df[df["Status"].isin(f_status)]
        if f_paid == "Paid":
            df_f = df_f[df_f["Paid"] == "Yes"]
        elif f_paid == "Unpaid":
            df_f = df_f[df_f["Paid"] == "No"]

        if f_search.strip():
            q = f_search.strip().lower()
            mask = (
                df_f["Order_ID"].astype(str).str.lower().str.contains(q)
                | df_f["Client"].astype(str).str.lower().str.contains(q)
                | df_f["Item"].astype(str).str.lower().str.contains(q)
                | df_f["Repair_Type"].astype(str).str.lower().str.contains(q)
            )
            df_f = df_f[mask]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Open repairs", int((df_f["Status"] != "Completed").sum()))
        c2.metric("Completed", int((df_f["Status"] == "Completed").sum()))
        c3.metric("Total revenue (listed)", money_fmt(df_f["Total_Price"].sum()))
        c4.metric("Outstanding balance", money_fmt(df_f["Remaining_Balance"].sum()))

        st.markdown("### Repair table (editable)")
        st.info("Edit status, deposits, notes. Remaining/Paid auto-update.")

        editable_cols = [
            "Order_ID",
            "Client",
            "Item",
            "Repair_Type",
            "Assigned_To",
            "Status",
            "Intake_Date",
            "Est_Completion",
            "Total_Price",
            "Deposit_Paid",
            "Remaining_Balance",
            "Paid",
            "Notes",
        ]
        for col in editable_cols:
            if col not in st.session_state.repair_df.columns:
                st.session_state.repair_df[col] = ""

        edited = st.data_editor(
            st.session_state.repair_df[editable_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Status": st.column_config.SelectboxColumn("Status", options=REPAIR_STATUSES),
                "Total_Price": st.column_config.NumberColumn("Total Price", min_value=0.0, step=10.0),
                "Deposit_Paid": st.column_config.NumberColumn("Deposit Paid", min_value=0.0, step=10.0),
                "Remaining_Balance": st.column_config.NumberColumn("Remaining", disabled=True),
                "Paid": st.column_config.TextColumn("Paid", disabled=True),
            },
            key="repair_editor",
        )

        if edited is not None:
            df_all = edited.copy()
            df_all["Total_Price"] = pd.to_numeric(df_all["Total_Price"], errors="coerce").fillna(0.0)
            df_all["Deposit_Paid"] = pd.to_numeric(df_all["Deposit_Paid"], errors="coerce").fillna(0.0)
            df_all["Remaining_Balance"] = (df_all["Total_Price"] - df_all["Deposit_Paid"]).clip(lower=0.0)
            df_all["Paid"] = df_all["Remaining_Balance"].apply(lambda x: "Yes" if float(x) == 0 else "No")

            st.session_state.repair_df = df_all
            save_csv(df_all, REPAIR_FILE)

        st.markdown("### Stage view")
        stage_counts = st.session_state.repair_df["Status"].value_counts().reindex(REPAIR_STATUSES, fill_value=0)
        st.bar_chart(stage_counts)

        with st.expander("Export"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.download_button(
                    "Download Repair Jobs CSV",
                    data=st.session_state.repair_df.to_csv(index=False).encode("utf-8"),
                    file_name="repair_jobs.csv",
                    mime="text/csv",
                )
            with col_b:
                if st.button("Reset demo repair data"):
                    if os.path.exists(REPAIR_FILE):
                        os.remove(REPAIR_FILE)
                    st.session_state.repair_df = load_or_init_csv(REPAIR_FILE, "repair")
                    st.success("Reset done (refresh if needed).")

# ANALYTICS TAB

with tab3:
    st.subheader("Analytics (revenue + pipeline)")
    custom = st.session_state.custom_df.copy()
    repair = st.session_state.repair_df.copy()

    # Numeric cleanup
    for df in (custom, repair):
        for col in ["Total_Price", "Deposit_Paid", "Remaining_Balance"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    custom["Remaining_Balance"] = (custom["Total_Price"] - custom["Deposit_Paid"]).clip(lower=0.0)
    repair["Remaining_Balance"] = (repair["Total_Price"] - repair["Deposit_Paid"]).clip(lower=0.0)

    col1, col2, col3 = st.columns(3)
    col1.metric("Custom revenue (listed)", money_fmt(custom["Total_Price"].sum()))
    col2.metric("Repair revenue (listed)", money_fmt(repair["Total_Price"].sum()))
    col3.metric("Total outstanding", money_fmt(custom["Remaining_Balance"].sum() + repair["Remaining_Balance"].sum()))

    st.markdown("---")

    st.markdown("### Pipeline snapshot")
    c_stage = custom["Status"].value_counts().reindex(CUSTOM_STATUSES, fill_value=0)
    r_stage = repair["Status"].value_counts().reindex(REPAIR_STATUSES, fill_value=0)

    left, right = st.columns(2)
    with left:
        st.markdown("**Custom pipeline**")
        st.bar_chart(c_stage)
    with right:
        st.markdown("**Repair pipeline**")
        st.bar_chart(r_stage)

    st.markdown("---")
    st.markdown("### Outstanding balance list (who owes money)")
    owed_custom = custom[custom["Remaining_Balance"] > 0].copy()
    owed_custom["Type"] = "Custom"
    owed_repair = repair[repair["Remaining_Balance"] > 0].copy()
    owed_repair["Type"] = "Repair"

    owed = pd.concat([owed_custom, owed_repair], ignore_index=True, sort=False)
    show_cols = [c for c in ["Type", "Order_ID", "Client", "Item", "Status", "Total_Price", "Deposit_Paid", "Remaining_Balance"] if c in owed.columns]
    if owed.empty:
        st.success("No outstanding balances in the demo data.")
    else:
        st.dataframe(owed[show_cols].sort_values("Remaining_Balance", ascending=False), use_container_width=True)

    st.markdown("---")
    st.caption("Tip: This demo can be extended to Google Sheets, Airtable, or a small database when a shop wants it production-ready.")
