"""
Core data types for PRU system.
No simulation, just data structures.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import uuid


@dataclass
class Entity:
    """
    Universal entity representation (amodal).
    Can come from text, image, video, table, etc.
    """
    id: str
    semantic_signature: Optional[str] = None  # Text representation
    visual_signature: Optional[str] = None     # Image embedding hash
    sources: List[Dict] = field(default_factory=list)  # [{modality, signature, embedding}]
    properties: Dict = field(default_factory=dict)     # Domain-specific properties
    created_at: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)

    @classmethod
    def create_new(cls, modality: str, signature: str) -> "Entity":
        """Factory method for new entity."""
        import hashlib
        # Deterministic ID based on signature (same signature → same ID)
        sig_hash = hashlib.md5(f"{modality}:{signature}".encode()).hexdigest()[:12]
        entity_id = f"e_{sig_hash}"

        entity = cls(id=entity_id)
        if modality == "text":
            entity.semantic_signature = signature
        elif modality in ["image", "video"]:
            entity.visual_signature = signature

        entity.sources.append({
            "modality": modality,
            "signature": signature,
            "embedding": None  # Will be set by resolver
        })

        return entity


@dataclass
class PRURelation:
    """
    Relational primitive between two entities.
    One of 7 PRU types.
    """
    entity_a_id: str
    entity_b_id: str
    pru_type: str  # PRU-1 through PRU-7
    confidence: float  # [0, 1]
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    # Validation
    VALID_PRU_TYPES = [
        "PRU-1",  # Co-presence
        "PRU-2",  # Sequentiality
        "PRU-3",  # Modulation
        "PRU-4",  # Containment
        "PRU-5",  # Disjunction
        "PRU-6",  # Perspective
        "PRU-7",  # Temporal
    ]

    def __post_init__(self):
        if self.pru_type not in self.VALID_PRU_TYPES:
            raise ValueError(f"Invalid PRU type: {self.pru_type}")

        if not 0 <= self.confidence <= 1:
            raise ValueError(f"Confidence must be in [0,1], got {self.confidence}")


@dataclass
class BoundingBox:
    """Bounding box for visual entities."""
    x1: float
    y1: float
    x2: float
    y2: float

    def area(self) -> float:
        return (self.x2 - self.x1) * (self.y2 - self.y1)

    def centroid(self) -> Tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)

    def iou(self, other: "BoundingBox") -> float:
        """Calculate Intersection over Union with another box."""
        x1_i = max(self.x1, other.x1)
        y1_i = max(self.y1, other.y1)
        x2_i = min(self.x2, other.x2)
        y2_i = min(self.y2, other.y2)

        if x2_i < x1_i or y2_i < y1_i:
            return 0.0

        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        union = self.area() + other.area() - intersection

        return intersection / union if union > 0 else 0.0
