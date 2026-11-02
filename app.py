"""
Streamlit Web Dashboard for Edge-Fog-Cloud Computing Simulator.
Subject: ARM 305 - Cloud, Dev, Edge and Fog Computing Mini Project.
Provides interactive simulation, node scaling, multi-tenant security verification,
and live QoS visualization.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

from core.simulator import Simulator
from core.models import ComputeNode, Task, LatencySensitivity
from core.placement import LatencyFirstPolicy, CapacityAwarePolicy
from core.security import SecurityGateway, UserSession, Role, AccessDeniedError
from experiments.default_tasks import get_default_workload, get_overload_workload
from experiments.runner import run_all_experiments, CHARTS_DIR, TABLES_DIR

# Page configuration
st.set_page_config(
    page_title="ARM 305: Edge-Fog-Cloud Simulator",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for clean UI styling
st.markdown(
    """
    <style>
    .metric-card {
        background-color: #f8fafc;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #3b82f6;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stAlert {
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State
if "tasks_workload" not in st.session_state:
    st.session_state.tasks_workload = get_default_workload()
if "security_gateway" not in st.session_state:
    st.session_state.security_gateway = SecurityGateway()
if "sim_results" not in st.session_state:
    st.session_state.sim_results = None

st.title("☁️ Edge-Fog-Cloud Computing Simulator")
st.caption("ARM 305 Mini Project | Rule-Based Task Scheduling, Virtualization & Multi-Tenancy")

# ==========================================
# SIDEBAR CONFIGURATION
# ==========================================
st.sidebar.header("⚙️ Simulation Settings")

policy_choice = st.sidebar.selectbox(
    "Placement Policy",
    ["Latency-First (Greedy)", "Capacity-Aware (Balanced)"],
    index=0,
    help="Select the scheduling policy for assigning tasks to Edge, Fog, or Cloud.",
)

st.sidebar.subheader("🖥️ Cluster Hardware Specs")
with st.sidebar.expander("Configure Node Capacities", expanded=False):
    edge_cpu = st.slider("Edge CPU (Cores)", 1, 16, 4)
    edge_ram = st.slider("Edge RAM (GB)", 2, 32, 8)
    edge_lat = st.slider("Edge Latency (ms)", 1, 30, 10)

    fog_cpu = st.slider("Fog CPU (Cores)", 4, 32, 16)
    fog_ram = st.slider("Fog RAM (GB)", 8, 64, 32)
    fog_lat = st.slider("Fog Latency (ms)", 20, 80, 45)

    cloud_cpu = st.slider("Cloud CPU (Cores)", 32, 128, 64)
    cloud_ram = st.slider("Cloud RAM (GB)", 64, 256, 128)
    cloud_lat = st.slider("Cloud Latency (ms)", 80, 300, 150)

st.sidebar.subheader("📋 Workload Selection")
workload_preset = st.sidebar.radio(
    "Choose Workload",
    ["Default Benchmark (12 Tasks)", "Overload Stress Test (19 Tasks)"],
    index=0,
)

if st.sidebar.button("Load Selected Workload", use_container_width=True):
    if "Default" in workload_preset:
        st.session_state.tasks_workload = get_default_workload()
        st.sidebar.success("Loaded 12 heterogeneous benchmark tasks!")
    else:
        st.session_state.tasks_workload = get_overload_workload()
        st.sidebar.warning("Loaded 19 high-stress overload tasks!")

# Dynamic Task Generator
with st.sidebar.expander("➕ Add Custom Task", expanded=False):
    with st.form("custom_task_form"):
        c_id = st.text_input("Task ID", value=f"TASK-{len(st.session_state.tasks_workload)+1:02d}")
        c_tenant = st.selectbox("Tenant", ["tenant_traffic", "tenant_health", "tenant_analytics", "tenant_custom"])
        c_cpu = st.number_input("CPU Required", min_value=0.5, max_value=32.0, value=2.0, step=0.5)
        c_ram = st.number_input("RAM Required (GB)", min_value=1.0, max_value=64.0, value=4.0, step=1.0)
        c_sens = st.selectbox("Latency Sensitivity", ["high", "medium", "low"])
        submitted = st.form_submit_button("Add Task")
        if submitted:
            new_task = Task(
                task_id=c_id,
                tenant_id=c_tenant,
                cpu_req=c_cpu,
                ram_req=c_ram,
                latency_sensitivity=LatencySensitivity(c_sens),
            )
            st.session_state.tasks_workload.append(new_task)
            st.success(f"Added {c_id} to workload queue!")

# Run Simulation Trigger
if st.sidebar.button("🚀 Run Simulation", type="primary", use_container_width=True):
    custom_nodes = [
        ComputeNode("node_edge_01", "Edge Node 1", "Edge", edge_cpu, edge_ram, edge_lat),
        ComputeNode("node_fog_01", "Fog Node 1", "Fog", fog_cpu, fog_ram, fog_lat),
        ComputeNode("node_cloud_01", "Cloud Data Center", "Cloud", cloud_cpu, cloud_ram, cloud_lat),
    ]
    sim = Simulator(nodes=custom_nodes)
    policy = LatencyFirstPolicy() if "Latency-First" in policy_choice else CapacityAwarePolicy()
    sim.run_workload(st.session_state.tasks_workload, policy)
    st.session_state.sim_results = sim
    st.sidebar.success("Simulation Executed Successfully!")

# ==========================================
# MAIN DASHBOARD TABS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 QoS Dashboard & Placement",
    "🖥️ Virtual Machines (VMs)",
    "🔒 Security & Multi-Tenancy",
    "📈 Export Experiments & Charts",
])

# If no simulation run yet, run default once
if st.session_state.sim_results is None:
    init_sim = Simulator()
    init_sim.run_workload(st.session_state.tasks_workload, LatencyFirstPolicy())
    st.session_state.sim_results = init_sim

sim = st.session_state.sim_results
metrics = sim.get_qos_metrics()
nodes_df = sim.get_nodes_df()
tasks_df = sim.get_tasks_df()
vms_df = sim.get_vms_df()

# ------------------------------------------
# TAB 1: QoS DASHBOARD
# ------------------------------------------
with tab1:
    st.subheader("Key Performance Indicators (QoS)")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Tasks", metrics["Total_Tasks"])
    col2.metric("Admitted / Running", metrics["Successful_Tasks"], delta=f"{metrics['Success_Rate_%']}% Admitted")
    col3.metric("Rejected (Overload)", metrics["Rejected_Tasks"], delta=f"-{metrics['Rejected_Tasks']}", delta_color="inverse")
    col4.metric("Avg Latency", f"{metrics['Avg_Latency_ms']} ms")
    col5.metric("Cluster Allocated", f"{metrics['Total_Allocated_CPU']} Cores", f"{metrics['Total_Allocated_RAM_GB']} GB RAM")

    st.markdown("---")
    st.subheader("Compute Nodes Live Status & Utilization")
    ncols = st.columns(3)
    for i, (_, node_row) in enumerate(nodes_df.iterrows()):
        with ncols[i]:
            st.markdown(f"**{node_row['Name']}** (`{node_row['Tier']}`)")
            st.write(f"Latency: `{node_row['Base_Latency_ms']} ms` | Active VMs: `{node_row['Active_VM_Count']}`")
            st.progress(float(node_row["CPU_Util_%"]) / 100.0, text=f"CPU: {node_row['Used_CPU']} / {node_row['Total_CPU']} cores ({node_row['CPU_Util_%']}%)")
            st.progress(float(node_row["RAM_Util_%"]) / 100.0, text=f"RAM: {node_row['Used_RAM_GB']} / {node_row['Total_RAM_GB']} GB ({node_row['RAM_Util_%']}%)")

    st.markdown("---")
    st.subheader("Task Placement Decisions")
    st.dataframe(
        tasks_df,
        column_config={
            "Status": st.column_config.TextColumn(
                "Status",
                help="Placement status",
            ),
            "Observed_Latency_ms": st.column_config.NumberColumn(
                "Observed Latency (ms)",
                format="%.1f ms",
            ),
        },
        use_container_width=True,
    )

# ------------------------------------------
# TAB 2: VIRTUAL MACHINES
# ------------------------------------------
with tab2:
    st.subheader("Simulated Virtual Machine (VM) Records")
    st.markdown(
        "Demonstrates the **Virtualization Concept**: Every admitted task is hosted inside a simulated "
        "Virtual Machine record with assigned CPU, RAM, and host node binding without requiring a physical hypervisor."
    )

    if not vms_df.empty:
        st.dataframe(vms_df, use_container_width=True)
        
        st.markdown("#### Manage Simulated VM Lifecycle")
        col_vm, col_btn = st.columns([3, 1])
        with col_vm:
            vm_to_stop = st.selectbox("Select VM to Stop / Deallocate", vms_df["VM_ID"].tolist())
        with col_btn:
            st.write("")
            st.write("")
            if st.button("🛑 Stop & Deallocate VM"):
                success = sim.stop_vm(vm_to_stop)
                if success:
                    st.success(f"Successfully stopped {vm_to_stop} and released node resources!")
                    st.rerun()
    else:
        st.info("No active VMs currently running.")

# ------------------------------------------
# TAB 3: SECURITY & MULTI-TENANCY
# ------------------------------------------
with tab3:
    st.subheader("Tenant Isolation & Access Control Check")
    st.markdown(
        "Fulfills **Basic Security & Experiment 3**: Each tenant operates in an isolated context. "
        "Attempting to query another tenant's tasks triggers an Access Denied error (HTTP 403 equivalent)."
    )

    scol1, scol2 = st.columns([1, 2])
    with scol1:
        logged_in_user = st.selectbox(
            "Log in as Tenant / Role:",
            [
                ("tenant_traffic", Role.TENANT),
                ("tenant_health", Role.TENANT),
                ("tenant_analytics", Role.TENANT),
                ("admin", Role.ADMIN),
            ],
            format_func=lambda x: f"{x[0]} ({x[1].value})",
        )
        current_session = UserSession(username=logged_in_user[0], tenant_id=logged_in_user[0], role=logged_in_user[1])

        st.markdown("#### Cross-Tenant Breach Test")
        target_tenant = st.selectbox(
            "Attempt to inspect private records of:",
            ["tenant_traffic", "tenant_health", "tenant_analytics"],
        )
        test_breach_btn = st.button("🚨 Attempt Cross-Tenant Access")

    with scol2:
        gateway: SecurityGateway = st.session_state.security_gateway

        if test_breach_btn:
            try:
                forbidden_tasks = gateway.get_tasks_for_tenant(
                    session=current_session,
                    all_tasks=sim.tasks,
                    requested_tenant_id=target_tenant,
                )
                st.success(f"Access Granted! Showing {len(forbidden_tasks)} records for {target_tenant} (Admin privilege).")
            except AccessDeniedError as err:
                st.error(f"🛑 {err}")

        # Authorized view for active session
        try:
            authorized_tasks = gateway.get_tasks_for_tenant(
                session=current_session,
                all_tasks=sim.tasks,
                requested_tenant_id=current_session.tenant_id if current_session.role != Role.ADMIN else None,
            )
            st.write(f"**Authorized Records for `{current_session.tenant_id}`:**")
            if authorized_tasks:
                st.dataframe(pd.DataFrame([t.to_dict() for t in authorized_tasks]), use_container_width=True)
            else:
                st.info("No task records for this tenant.")
        except AccessDeniedError:
            pass

    st.markdown("---")
    st.subheader("Security Audit Trail")
    if gateway.audit_logs:
        audit_df = pd.DataFrame([l.to_dict() for l in gateway.audit_logs])
        st.dataframe(audit_df, use_container_width=True)

# ------------------------------------------
# TAB 4: EXPERIMENTS EXPORT & CHARTS
# ------------------------------------------
with tab4:
    st.subheader("Automated Experiment Evidence & Deliverables")
    st.markdown(
        "Click below to automatically re-run all 4 required experiments and update all publication-ready "
        "`.png` charts and `.csv` tables for your partner's report."
    )

    if st.button("🔄 Run All 4 Experiments & Generate Artifacts", type="primary"):
        with st.spinner("Executing benchmark suites..."):
            run_all_experiments()
            st.success("All 4 experiments completed and saved to /outputs folder!")

    st.markdown("#### Generated Charts Preview")
    c_img1, c_img2 = st.columns(2)
    chart1_path = os.path.join(CHARTS_DIR, "exp1_policy_comparison.png")
    chart2_path = os.path.join(CHARTS_DIR, "exp2_overload_analysis.png")
    chart4_path = os.path.join(CHARTS_DIR, "exp4_node_scaling_comparison.png")

    if os.path.exists(chart1_path):
        with c_img1:
            st.image(chart1_path, caption="Experiment 1: Policy Comparison (Latency-First vs Capacity-Aware)")
    if os.path.exists(chart2_path):
        with c_img2:
            st.image(chart2_path, caption="Experiment 2: Overload & Rejection Analysis")
    if os.path.exists(chart4_path):
        st.image(chart4_path, caption="Experiment 4: Node Scaling & Latency Reduction")
