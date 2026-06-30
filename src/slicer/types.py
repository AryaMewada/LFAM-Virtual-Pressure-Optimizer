from dataclasses import dataclass, field
from typing import List
import numpy as np

@dataclass
class Polygon:
    """Represents a closed 2D loop."""
    points: np.ndarray  # Shape (N, 2)
    is_hole: bool = False

@dataclass
class SliceLayer:
    """Represents all polygons at a specific Z height."""
    z_height: float
    polygons: List[Polygon] = field(default_factory=list)
    perimeters: List[Polygon] = field(default_factory=list)

@dataclass
class SliceResult:
    """The full collection of sliced layers for a model."""
    layers: List[SliceLayer] = field(default_factory=list)
