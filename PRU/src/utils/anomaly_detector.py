"""
URP Anomaly Detector with Audit Trail (Paper §5.3.1, §7.3.2).

LISA Case Study: 66.6% compliance = 33.4% detection rate.

Key Insight: FOL violations are FEATURES, not bugs.
- Vector RAG: Fails silently (accepts red+green)
- URP: Fails loudly (flags violations for safety-critical systems)

Regulatory compliance: ISO 26262, DO-178C require explainable rejections.
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import json

from src.core.types import PRURelation

logger = logging.getLogger(__name__)


class URPAnomalyDetector:
    """
    Detects and logs FOL violations with full audit trail.

    Design Philosophy (Paper §7.3.2):
    - Strict rejection > permissive acceptance
    - Explicit violation flags > silent failures
    - Audit trail for regulatory compliance
    """

    def __init__(self, audit_log_path: Optional[str] = None):
        """
        Initialize anomaly detector.

        Args:
            audit_log_path: Path to store audit logs (default: ./urp_violations.jsonl)
        """
        self.audit_log_path = audit_log_path or "urp_violations.jsonl"
        self.violations: List[Dict] = []

        # Stats
        self.total_relations_checked = 0
        self.total_violations_detected = 0

        logger.info(f"URP Anomaly Detector initialized (audit_log={self.audit_log_path})")

    def detect_disjunction_violations(
        self,
        relations: List[PRURelation],
        context: str = "",
        tolerance_ms: float = 0.0
    ) -> List[Dict]:
        """
        Detect URP-5 (disjunction) violations: red+green both active.

        Paper Example (LISA traffic lights):
        - Expected: Exactly one light active (mutual exclusion)
        - Violation: red AND green simultaneously
        - Action: Flag as anomaly (DO NOT silently accept)

        Paper §5.3.1 Trade-off Analysis:
        - tolerance_ms=0: 87% precision, 87% recall (strict)
        - tolerance_ms=50: 97% precision, 97% recall (safety-critical)
        - tolerance_ms=100: 94% precision, 94% recall (balanced)

        Args:
            relations: List of URP-5 relations to check
            context: Context string (e.g., "Frame: daySequence1--01999.jpg")
            tolerance_ms: Temporal tolerance for brief overlaps (default: 0ms = strict)
                         Use 50ms for autonomous vehicles, 100ms for dataset cleaning

        Returns:
            List of violation dicts
        """
        violations = []

        # Group by disjunction set
        disjunction_sets = {}
        for rel in relations:
            # Accept both URP-5 and PRU-5 (paper uses URP, code uses PRU)
            if rel.pru_type in ["URP-5", "PRU-5"]:
                # rel.metadata should have "set_id"
                set_id = rel.metadata.get("set_id", "default")
                if set_id not in disjunction_sets:
                    disjunction_sets[set_id] = []
                disjunction_sets[set_id].append(rel)

        # Check each set for mutual exclusion
        for set_id, set_relations in disjunction_sets.items():
            active_entities = []
            active_timestamps = []

            for rel in set_relations:
                # Check if entity_a is active
                is_active_a = rel.metadata.get("active", False)
                if is_active_a:
                    active_entities.append(rel.entity_a_id)
                    # Store timestamp if available (for tolerance checking)
                    timestamp_a = rel.metadata.get("timestamp_a", None)
                    active_timestamps.append(timestamp_a)

                # Also check entity_b if it has different metadata
                is_active_b = rel.metadata.get("active_b", None)
                if is_active_b is True and rel.entity_b_id not in active_entities:
                    active_entities.append(rel.entity_b_id)
                    timestamp_b = rel.metadata.get("timestamp_b", None)
                    active_timestamps.append(timestamp_b)

            # Violation: More than one active
            if len(active_entities) > 1:
                # Check temporal tolerance (if timestamps available)
                is_within_tolerance = False
                if all(t is not None for t in active_timestamps) and len(active_timestamps) >= 2:
                    # Calculate time overlap
                    time_diff_ms = abs(active_timestamps[1] - active_timestamps[0])
                    if time_diff_ms <= tolerance_ms:
                        is_within_tolerance = True
                        logger.debug(
                            f"Overlap within tolerance: {time_diff_ms:.1f}ms <= {tolerance_ms}ms"
                        )

                # Only report violation if outside tolerance window
                if not is_within_tolerance:
                    violation = {
                        "type": "URP-5_DISJUNCTION_VIOLATION",
                        "context": context,
                        "set_id": set_id,
                        "active_entities": active_entities,
                        "expected": "Exactly 1 active",
                        "observed": f"{len(active_entities)} active",
                        "severity": "HIGH",  # Safety-critical
                        "timestamp": datetime.utcnow().isoformat(),
                        "recommendation": "HALT_AND_FLAG",  # Autonomous vehicle should stop
                        "tolerance_ms": tolerance_ms  # Record tolerance setting
                    }
                    violations.append(violation)
                    self.total_violations_detected += 1

                    logger.warning(
                        f"URP-5 VIOLATION: {context} | {len(active_entities)} entities active "
                        f"(expected 1): {active_entities} [tolerance={tolerance_ms}ms]"
                    )

        self.total_relations_checked += len(relations)
        self.violations.extend(violations)

        return violations

    def detect_acyclicity_violations(
        self,
        relations: List[PRURelation],
        context: str = ""
    ) -> List[Dict]:
        """
        Detect cycles in URP-2 (sequentiality) or URP-4 (containment).

        FOL Constraint: (x → y) → ¬(y → x)
        Violation: A → B → C → A (cycle)

        Args:
            relations: List of URP-2 or URP-4 relations
            context: Context string

        Returns:
            List of violation dicts
        """
        violations = []

        # Build graph
        graph = {}
        for rel in relations:
            if rel.pru_type in ["URP-2", "URP-4"]:
                if rel.entity_a_id not in graph:
                    graph[rel.entity_a_id] = []
                graph[rel.entity_a_id].append(rel.entity_b_id)

        # DFS cycle detection
        def has_cycle(node, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        visited = set()
        for node in graph:
            if node not in visited:
                if has_cycle(node, set(), set()):
                    violation = {
                        "type": "ACYCLICITY_VIOLATION",
                        "context": context,
                        "pru_type": "URP-2 or URP-4",
                        "cycle_detected": True,
                        "severity": "CRITICAL",
                        "timestamp": datetime.utcnow().isoformat(),
                        "recommendation": "REJECT_RELATION"
                    }
                    violations.append(violation)
                    self.total_violations_detected += 1

                    logger.error(f"CYCLE DETECTED: {context} | {rel.pru_type} relations form cycle")
                    break  # One cycle is enough

        self.violations.extend(violations)
        return violations

    def detect_temporal_consistency_violations(
        self,
        relations: List[PRURelation],
        context: str = ""
    ) -> List[Dict]:
        """
        Detect URP-3 (causality) violations: cause AFTER effect.

        FOL Constraint: (x ⇝ y) → time(x) < time(y)
        Violation: temp_at_t2 CAUSES failure_at_t1 (backwards causality)

        Args:
            relations: List of URP-3 relations
            context: Context string

        Returns:
            List of violation dicts
        """
        violations = []

        for rel in relations:
            # Accept both URP-3 and PRU-3
            if rel.pru_type in ["URP-3", "PRU-3"]:
                time_a = rel.metadata.get("time_a")
                time_b = rel.metadata.get("time_b")

                if time_a is not None and time_b is not None:
                    if time_a >= time_b:  # Cause AFTER effect
                        violation = {
                            "type": "TEMPORAL_CAUSALITY_VIOLATION",
                            "context": context,
                            "entity_a": rel.entity_a_id,
                            "entity_b": rel.entity_b_id,
                            "time_a": time_a,
                            "time_b": time_b,
                            "severity": "HIGH",
                            "timestamp": datetime.utcnow().isoformat(),
                            "recommendation": "REJECT_RELATION"
                        }
                        violations.append(violation)
                        self.total_violations_detected += 1

                        logger.warning(
                            f"TEMPORAL VIOLATION: {context} | "
                            f"{rel.entity_a_id} (t={time_a}) CAUSES {rel.entity_b_id} (t={time_b}) "
                            f"but time_a >= time_b"
                        )

        self.violations.extend(violations)
        return violations

    def save_audit_log(self):
        """
        Save violations to audit log (JSONL format).

        Regulatory compliance: ISO 26262 requires traceable rejection paths.
        """
        with open(self.audit_log_path, 'a') as f:
            for violation in self.violations:
                f.write(json.dumps(violation) + '\n')

        logger.info(f"Saved {len(self.violations)} violations to {self.audit_log_path}")
        self.violations = []  # Clear after save

    def get_stats(self) -> Dict:
        """
        Get anomaly detection statistics (Paper §5.3.1).

        Returns:
            {
                "total_checked": int,
                "total_violations": int,
                "detection_rate": str,
                "compliance_rate": str
            }
        """
        detection_rate = (self.total_violations_detected / self.total_relations_checked * 100) \
            if self.total_relations_checked > 0 else 0

        compliance_rate = ((self.total_relations_checked - self.total_violations_detected) /
                          self.total_relations_checked * 100) \
            if self.total_relations_checked > 0 else 0

        return {
            "total_checked": self.total_relations_checked,
            "total_violations": self.total_violations_detected,
            "detection_rate": f"{detection_rate:.1f}%",
            "compliance_rate": f"{compliance_rate:.1f}%",
            "audit_log": self.audit_log_path
        }


def example_lisa_anomaly_detection():
    """
    Example: LISA traffic lights (Paper §5.3.1).

    Expected behavior:
    - Clean frame: 100% compliance (one light active)
    - Violation frame: Flagged with audit log entry
    """
    detector = URPAnomalyDetector()

    # Simulate LISA frame with violation
    relations = [
        PRURelation(
            entity_a_id="e_red_light",
            entity_b_id="e_green_light",
            pru_type="URP-5",
            confidence=0.95,
            metadata={"set_id": "traffic_light", "active": True}
        ),
        PRURelation(
            entity_a_id="e_green_light",
            entity_b_id="e_yellow_light",
            pru_type="URP-5",
            confidence=0.95,
            metadata={"set_id": "traffic_light", "active": True}  # VIOLATION
        ),
    ]

    violations = detector.detect_disjunction_violations(
        relations,
        context="Frame: daySequence1--01999.jpg"
    )

    print(f"Detected {len(violations)} violations")
    print(f"Stats: {detector.get_stats()}")

    # Save to audit log
    detector.save_audit_log()

    # Key insight: Vector RAG would accept this silently
    # URP flags it for safety-critical review


if __name__ == "__main__":
    example_lisa_anomaly_detection()
