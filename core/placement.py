"""
Placement algorithms for the Edge-Fog-Cloud Computing Simulator.
Implements two distinct policies:
1. Latency-First (Greedy based on sensitivity)
2. Capacity-Aware (Balanced load distribution with sensitivity weighting)
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from core.models import ComputeNode, Task, LatencySensitivity


class BasePlacementPolicy(ABC):
    """Abstract base class for placement algorithms."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def select_node(self, task: Task, nodes: List[ComputeNode]) -> Optional[ComputeNode]:
        """
        Selects the most suitable node for the task based on policy rules.
        Returns None if no node can host the task (overload scenario).
        """
        pass


class LatencyFirstPolicy(BasePlacementPolicy):
    """
    Policy 1: Latency-First (Greedy)
    Prioritizes nodes with minimal latency matching the task's latency sensitivity.
    - HIGH sensitivity: Prefers Edge (lowest latency) -> Fog -> Cloud
    - MEDIUM sensitivity: Prefers Fog -> Edge -> Cloud
    - LOW sensitivity: Prefers Cloud (saves edge resources) -> Fog -> Edge
    Falls back to next tier if the preferred node has insufficient CPU/RAM.
    """

    @property
    def name(self) -> str:
        return "Latency-First (Greedy)"

    def select_node(self, task: Task, nodes: List[ComputeNode]) -> Optional[ComputeNode]:
        tier_preferences = {
            LatencySensitivity.HIGH: ["Edge", "Fog", "Cloud"],
            LatencySensitivity.MEDIUM: ["Fog", "Edge", "Cloud"],
            LatencySensitivity.LOW: ["Cloud", "Fog", "Edge"],
        }

        preferred_tiers = tier_preferences.get(
            task.latency_sensitivity, ["Edge", "Fog", "Cloud"]
        )

        node_by_tier = {node.tier: node for node in nodes}

        # Check nodes in order of preference
        for tier in preferred_tiers:
            candidate = node_by_tier.get(tier)
            if candidate and candidate.can_host(task.cpu_req, task.ram_req):
                return candidate

        return None


class CapacityAwarePolicy(BasePlacementPolicy):
    """
    Policy 2: Capacity-Aware (Balanced)
    Balances cluster load by selecting the node that provides the best combination of
    available resource headroom and acceptable latency.
    Helps avoid edge node bottlenecking and distributes workloads sustainably.
    """

    @property
    def name(self) -> str:
        return "Capacity-Aware (Balanced)"

    def select_node(self, task: Task, nodes: List[ComputeNode]) -> Optional[ComputeNode]:
        eligible_nodes = [
            n for n in nodes if n.can_host(task.cpu_req, task.ram_req)
        ]

        if not eligible_nodes:
            return None

        # Sensitivity penalties for latency (higher weight = latency matters more)
        sensitivity_weight = {
            LatencySensitivity.HIGH: 0.6,
            LatencySensitivity.MEDIUM: 0.3,
            LatencySensitivity.LOW: 0.1,
        }.get(task.latency_sensitivity, 0.3)

        best_node = None
        best_score = -float("inf")

        for node in eligible_nodes:
            # Capacity headroom score (0.0 to 1.0, higher is better)
            cpu_headroom = (node.total_cpu - node.used_cpu) / node.total_cpu
            ram_headroom = (node.total_ram - node.used_ram) / node.total_ram
            headroom_score = (cpu_headroom + ram_headroom) / 2.0

            # Latency penalty normalized roughly against max latency (Cloud ~150ms)
            norm_latency = min(1.0, node.base_latency_ms / 150.0)

            # Combined score: headroom penalized by latency sensitivity
            # Score favors nodes with lots of free capacity while respecting latency needs
            score = ((1.0 - sensitivity_weight) * headroom_score) - (sensitivity_weight * norm_latency)

            if score > best_score:
                best_score = score
                best_node = node

        return best_node
