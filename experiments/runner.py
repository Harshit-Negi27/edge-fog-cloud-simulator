"""
Automated Experiment Runner for Edge-Fog-Cloud Computing Simulator.
Executes the 4 mandatory assignment experiments, computes QoS metrics,
and automatically exports publication-ready PNG charts and CSV/JSON tables.
"""

import os
import json
import matplotlib.pyplot as plt
import pandas as pd

from core.simulator import Simulator
from core.models import ComputeNode
from core.placement import LatencyFirstPolicy, CapacityAwarePolicy
from core.security import SecurityGateway, UserSession, Role, AccessDeniedError
from experiments.default_tasks import get_default_workload, get_overload_workload


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS_DIR = os.path.join(BASE_DIR, "outputs", "charts")
TABLES_DIR = os.path.join(BASE_DIR, "outputs", "tables")


def ensure_directories():
    os.makedirs(CHARTS_DIR, exist_ok=True)
    os.makedirs(TABLES_DIR, exist_ok=True)


def run_experiment_1():
    """
    Experiment 1: Policy Comparison
    Compares Latency-First (Greedy) vs. Capacity-Aware (Balanced)
    on the exact same workload of 12 tasks.
    """
    print("\n" + "=" * 60)
    print("RUNNING EXPERIMENT 1: Policy Comparison")
    print("=" * 60)

    workload = get_default_workload()
    sim = Simulator()

    # 1. Run Latency-First
    tasks_lf = sim.run_workload(workload, LatencyFirstPolicy())
    metrics_lf = sim.get_qos_metrics()
    nodes_lf_df = sim.get_nodes_df()
    tasks_lf_df = sim.get_tasks_df()

    # 2. Run Capacity-Aware
    sim.reset()
    tasks_ca = sim.run_workload(workload, CapacityAwarePolicy())
    metrics_ca = sim.get_qos_metrics()
    nodes_ca_df = sim.get_nodes_df()
    tasks_ca_df = sim.get_tasks_df()

    # Save CSVs
    tasks_lf_df.to_csv(os.path.join(TABLES_DIR, "exp1_latency_first_tasks.csv"), index=False)
    tasks_ca_df.to_csv(os.path.join(TABLES_DIR, "exp1_capacity_aware_tasks.csv"), index=False)

    summary_df = pd.DataFrame([
        {
            "Policy": "Latency-First",
            "Avg_Latency_ms": metrics_lf["Avg_Latency_ms"],
            "Success_Rate_%": metrics_lf["Success_Rate_%"],
            "Edge_Util_%": nodes_lf_df.loc[nodes_lf_df["Tier"] == "Edge", "Overall_Util_%"].values[0],
            "Fog_Util_%": nodes_lf_df.loc[nodes_lf_df["Tier"] == "Fog", "Overall_Util_%"].values[0],
            "Cloud_Util_%": nodes_lf_df.loc[nodes_lf_df["Tier"] == "Cloud", "Overall_Util_%"].values[0],
        },
        {
            "Policy": "Capacity-Aware",
            "Avg_Latency_ms": metrics_ca["Avg_Latency_ms"],
            "Success_Rate_%": metrics_ca["Success_Rate_%"],
            "Edge_Util_%": nodes_ca_df.loc[nodes_ca_df["Tier"] == "Edge", "Overall_Util_%"].values[0],
            "Fog_Util_%": nodes_ca_df.loc[nodes_ca_df["Tier"] == "Fog", "Overall_Util_%"].values[0],
            "Cloud_Util_%": nodes_ca_df.loc[nodes_ca_df["Tier"] == "Cloud", "Overall_Util_%"].values[0],
        },
    ])
    summary_df.to_csv(os.path.join(TABLES_DIR, "exp1_summary_comparison.csv"), index=False)

    # Plot Chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Subplot 1: Average Latency
    policies = ["Latency-First", "Capacity-Aware"]
    latencies = [metrics_lf["Avg_Latency_ms"], metrics_ca["Avg_Latency_ms"]]
    bars = ax1.bar(policies, latencies, color=["#3b82f6", "#10b981"], width=0.45)
    ax1.set_ylabel("Average Latency (ms)", fontsize=11, fontweight="bold")
    ax1.set_title("Average Task Latency by Policy", fontsize=12, fontweight="bold")
    for bar in bars:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2.0, yval + 1.5, f"{yval:.1f} ms", ha="center", va="bottom", fontweight="bold")

    # Subplot 2: Utilization per Node Tier
    tiers = ["Edge", "Fog", "Cloud"]
    x = range(len(tiers))
    width = 0.35
    util_lf = [
        nodes_lf_df.loc[nodes_lf_df["Tier"] == t, "Overall_Util_%"].values[0] for t in tiers
    ]
    util_ca = [
        nodes_ca_df.loc[nodes_ca_df["Tier"] == t, "Overall_Util_%"].values[0] for t in tiers
    ]

    ax2.bar([p - width / 2 for p in x], util_lf, width=width, label="Latency-First", color="#3b82f6")
    ax2.bar([p + width / 2 for p in x], util_ca, width=width, label="Capacity-Aware", color="#10b981")
    ax2.set_xticks(list(x))
    ax2.set_xticklabels(tiers, fontweight="bold")
    ax2.set_ylabel("Utilization (%)", fontsize=11, fontweight="bold")
    ax2.set_title("Node Resource Utilization by Tier", fontsize=12, fontweight="bold")
    ax2.legend()

    plt.tight_layout()
    chart_path = os.path.join(CHARTS_DIR, "exp1_policy_comparison.png")
    plt.savefig(chart_path, dpi=300)
    plt.close()

    print(f"-> Experiment 1 complete. Chart saved: {chart_path}")
    return {
        "setup": "12 diverse tasks evaluated under Latency-First vs Capacity-Aware policies.",
        "expected": "Latency-First achieves lower average latency by aggressively placing sensitive tasks on Edge; Capacity-Aware distributes load more evenly across Fog and Cloud.",
        "actual": f"Latency-First avg latency: {metrics_lf['Avg_Latency_ms']} ms vs Capacity-Aware: {metrics_ca['Avg_Latency_ms']} ms. Load balanced across nodes.",
        "evidence": chart_path,
    }


def run_experiment_2():
    """
    Experiment 2: Overload & Fallback / Rejection Scenario
    Floods the cluster beyond maximum capacity to observe task spillovers and rejections.
    """
    print("\n" + "=" * 60)
    print("RUNNING EXPERIMENT 2: Overload & Rejection Scenario")
    print("=" * 60)

    workload = get_overload_workload()
    sim = Simulator()
    sim.run_workload(workload, LatencyFirstPolicy())

    metrics = sim.get_qos_metrics()
    tasks_df = sim.get_tasks_df()
    nodes_df = sim.get_nodes_df()

    tasks_df.to_csv(os.path.join(TABLES_DIR, "exp2_overload_tasks.csv"), index=False)

    # Plot Chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Subplot 1: Task Execution Status (Placed vs Rejected)
    status_counts = tasks_df["Status"].value_counts()
    colors = ["#10b981" if s == "RUNNING" else "#ef4444" for s in status_counts.index]
    ax1.pie(status_counts, labels=status_counts.index, autopct="%1.1f%%", colors=colors, startangle=140, textprops={"fontweight": "bold"})
    ax1.set_title(f"Task Outcomes Under Cluster Overload (Total: {metrics['Total_Tasks']})", fontsize=12, fontweight="bold")

    # Subplot 2: Node CPU Saturation
    bars = ax2.bar(nodes_df["Tier"], nodes_df["CPU_Util_%"], color="#6366f1", width=0.45)
    ax2.set_ylabel("CPU Utilization (%)", fontsize=11, fontweight="bold")
    ax2.set_title("Node CPU Saturation Under Heavy Load", fontsize=12, fontweight="bold")
    ax2.set_ylim(0, 110)
    for bar in bars:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2.0, yval + 2, f"{yval:.1f}%", ha="center", va="bottom", fontweight="bold")

    plt.tight_layout()
    chart_path = os.path.join(CHARTS_DIR, "exp2_overload_analysis.png")
    plt.savefig(chart_path, dpi=300)
    plt.close()

    print(f"-> Experiment 2 complete. Chart saved: {chart_path}")
    return {
        "setup": f"{len(workload)} tasks submitted, requesting 130+ CPU cores against a cluster capacity of 84 cores.",
        "expected": "Edge and Fog saturate first, tasks spill over to Cloud, and remaining tasks are rejected gracefully.",
        "actual": f"{metrics['Successful_Tasks']} tasks admitted ({metrics['Success_Rate_%']}%), {metrics['Rejected_Tasks']} rejected due to insufficient capacity.",
        "evidence": chart_path,
    }


def run_experiment_3():
    """
    Experiment 3: Security & Multi-Tenant Access Control Demonstration
    Simulates authorized and unauthorized cross-tenant data requests.
    """
    print("\n" + "=" * 60)
    print("RUNNING EXPERIMENT 3: Unauthorized Access Demonstration")
    print("=" * 60)

    workload = get_default_workload()
    sim = Simulator()
    sim.run_workload(workload, LatencyFirstPolicy())

    gateway = SecurityGateway()
    tenant_traffic_session = UserSession(username="alice", tenant_id="tenant_traffic", role=Role.TENANT)
    tenant_health_session = UserSession(username="bob", tenant_id="tenant_health", role=Role.TENANT)
    admin_session = UserSession(username="root", tenant_id="admin_cluster", role=Role.ADMIN)

    # 1. Authorized access (Alice views Alice's tasks)
    alice_tasks = gateway.get_tasks_for_tenant(tenant_traffic_session, sim.tasks)

    # 2. Unauthorized access attempt (Alice attempts to view Bob's healthcare tasks)
    access_blocked = False
    rejection_msg = ""
    try:
        gateway.get_tasks_for_tenant(tenant_traffic_session, sim.tasks, requested_tenant_id="tenant_health")
    except AccessDeniedError as e:
        access_blocked = True
        rejection_msg = str(e)

    # 3. Admin access (Can view all)
    all_admin_tasks = gateway.get_tasks_for_tenant(admin_session, sim.tasks)

    # Export audit logs
    audit_df = pd.DataFrame([l.to_dict() for l in gateway.audit_logs])
    audit_df.to_csv(os.path.join(TABLES_DIR, "exp3_security_audit_log.csv"), index=False)

    print(f"-> Experiment 3 complete. Security audit log saved to tables folder.")
    return {
        "setup": "Tenant 'tenant_traffic' logged in and attempted to query tasks belonging to 'tenant_health'.",
        "expected": "Security gateway denies request with 403 Forbidden and logs security audit trail.",
        "actual": f"Access blocked successfully: {access_blocked}. Error: '{rejection_msg}'.",
        "evidence": os.path.join(TABLES_DIR, "exp3_security_audit_log.csv"),
    }


def run_experiment_4():
    """
    Experiment 4: Node Sensitivity & Parameter Tuning
    Compares cluster performance before and after scaling Edge capacity and latency.
    """
    print("\n" + "=" * 60)
    print("RUNNING EXPERIMENT 4: Parameter Tuning / Sensitivity")
    print("=" * 60)

    workload = get_default_workload()

    # Scenario A: Baseline Edge (4 CPU, 8 GB RAM, 10ms)
    sim_a = Simulator()
    sim_a.run_workload(workload, LatencyFirstPolicy())
    metrics_a = sim_a.get_qos_metrics()
    nodes_a_df = sim_a.get_nodes_df()

    # Scenario B: Upgraded Edge (8 CPU, 16 GB RAM, 5ms latency - e.g. 5G MEC Upgrade)
    upgraded_nodes = [
        ComputeNode(node_id="node_edge_01", name="Edge Node 1 (Upgraded)", tier="Edge", total_cpu=8.0, total_ram=16.0, base_latency_ms=5.0),
        ComputeNode(node_id="node_fog_01", name="Fog Node 1", tier="Fog", total_cpu=16.0, total_ram=32.0, base_latency_ms=45.0),
        ComputeNode(node_id="node_cloud_01", name="Cloud Data Center", tier="Cloud", total_cpu=64.0, total_ram=128.0, base_latency_ms=150.0),
    ]
    sim_b = Simulator(nodes=upgraded_nodes)
    sim_b.run_workload(workload, LatencyFirstPolicy())
    metrics_b = sim_b.get_qos_metrics()
    nodes_b_df = sim_b.get_nodes_df()

    # Summary table
    comparison_df = pd.DataFrame([
        {
            "Configuration": "Baseline (4 CPU, 8GB RAM, 10ms Edge)",
            "Avg_Latency_ms": metrics_a["Avg_Latency_ms"],
            "Edge_Util_%": nodes_a_df.loc[nodes_a_df["Tier"] == "Edge", "Overall_Util_%"].values[0],
            "Fog_Util_%": nodes_a_df.loc[nodes_a_df["Tier"] == "Fog", "Overall_Util_%"].values[0],
            "Cloud_Util_%": nodes_a_df.loc[nodes_a_df["Tier"] == "Cloud", "Overall_Util_%"].values[0],
        },
        {
            "Configuration": "Upgraded Edge (8 CPU, 16GB RAM, 5ms Edge)",
            "Avg_Latency_ms": metrics_b["Avg_Latency_ms"],
            "Edge_Util_%": nodes_b_df.loc[nodes_b_df["Tier"] == "Edge", "Overall_Util_%"].values[0],
            "Fog_Util_%": nodes_b_df.loc[nodes_b_df["Tier"] == "Fog", "Overall_Util_%"].values[0],
            "Cloud_Util_%": nodes_b_df.loc[nodes_b_df["Tier"] == "Cloud", "Overall_Util_%"].values[0],
        },
    ])
    comparison_df.to_csv(os.path.join(TABLES_DIR, "exp4_sensitivity_comparison.csv"), index=False)

    # Plot Chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Latency Reduction
    configs = ["Baseline Edge", "Upgraded 5G Edge"]
    lats = [metrics_a["Avg_Latency_ms"], metrics_b["Avg_Latency_ms"]]
    bars = ax1.bar(configs, lats, color=["#f59e0b", "#06b6d4"], width=0.45)
    ax1.set_ylabel("Average Latency (ms)", fontsize=11, fontweight="bold")
    ax1.set_title("Cluster Latency Reduction via Edge Scaling", fontsize=12, fontweight="bold")
    for bar in bars:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2.0, yval + 1.5, f"{yval:.1f} ms", ha="center", va="bottom", fontweight="bold")

    # Edge Task Intake
    edge_vms_a = nodes_a_df.loc[nodes_a_df["Tier"] == "Edge", "Active_VM_Count"].values[0]
    edge_vms_b = nodes_b_df.loc[nodes_b_df["Tier"] == "Edge", "Active_VM_Count"].values[0]
    bars2 = ax2.bar(configs, [edge_vms_a, edge_vms_b], color=["#f59e0b", "#06b6d4"], width=0.45)
    ax2.set_ylabel("Active Tasks / VMs on Edge", fontsize=11, fontweight="bold")
    ax2.set_title("Edge Capacity & Task Intake Increase", fontsize=12, fontweight="bold")
    for bar in bars2:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.1, f"{int(yval)} VMs", ha="center", va="bottom", fontweight="bold")

    plt.tight_layout()
    chart_path = os.path.join(CHARTS_DIR, "exp4_node_scaling_comparison.png")
    plt.savefig(chart_path, dpi=300)
    plt.close()

    print(f"-> Experiment 4 complete. Chart saved: {chart_path}")
    return {
        "setup": "Edge node upgraded from 4 CPU / 8GB / 10ms to 8 CPU / 16GB / 5ms.",
        "expected": "Upgraded Edge accommodates more latency-critical tasks, dropping cluster-wide average latency.",
        "actual": f"Average latency dropped from {metrics_a['Avg_Latency_ms']} ms to {metrics_b['Avg_Latency_ms']} ms; Edge VM count increased from {edge_vms_a} to {edge_vms_b}.",
        "evidence": chart_path,
    }


def run_all_experiments():
    ensure_directories()
    results = {
        "Experiment_1_Policy_Comparison": run_experiment_1(),
        "Experiment_2_Overload_Scenario": run_experiment_2(),
        "Experiment_3_Unauthorized_Access": run_experiment_3(),
        "Experiment_4_Sensitivity_Tuning": run_experiment_4(),
    }

    summary_file = os.path.join(TABLES_DIR, "all_experiments_summary.json")
    with open(summary_file, "w") as f:
        json.dump(results, f, indent=4)

    print("\n" + "=" * 60)
    print(f"ALL 4 EXPERIMENTS COMPLETED SUCCESSFULLY!")
    print(f"Artifacts saved in:")
    print(f" - Charts: {CHARTS_DIR}")
    print(f" - Tables: {TABLES_DIR}")
    print(f" - Summary: {summary_file}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_all_experiments()
