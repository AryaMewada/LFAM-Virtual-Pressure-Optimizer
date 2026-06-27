from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Dict, Any
import math

class MoveType(Enum):
    """Enumeration of G-code move types."""
    G0 = auto()
    G1 = auto()
    G2 = auto()
    G3 = auto()
    TRAVEL = auto()
    RETRACT = auto()
    COMMENT = auto()
    OTHER = auto()
    RAW = auto()

@dataclass
class Point2D:
    """Represents a 2D point (X, Y)."""
    x: float
    y: float

@dataclass
class Point3D:
    """Represents a 3D point (X, Y, Z)."""
    x: float
    y: float
    z: float

@dataclass
class Move:
    """Represents a single G-code movement."""
    id: int
    type: MoveType
    start: Point3D
    end: Point3D
    feedrate: float
    extrusion: float
    extrusion_mode: str
    layer: int
    line_number: int
    arc_center: Optional[Point2D] = None
    arc_radius: Optional[float] = None
    arc_direction: Optional[str] = None
    original_line: str = ""
    is_travel: bool = False
    is_print: bool = False
    is_arc: bool = False
    comment: str = ""
    raw_params: Dict[str, Any] = field(default_factory=dict)

    @property
    def length(self) -> float:
        """Computes the 3D Euclidean distance or arc length for arcs."""
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        dz = self.end.z - self.start.z
        
        if self.is_arc and self.arc_radius is not None and self.arc_center is not None and self.arc_radius > 0:
            e2d = math.hypot(dx, dy)
            if e2d <= 2 * self.arc_radius:
                angle = 2 * math.asin(e2d / (2 * self.arc_radius))
                arc_len = self.arc_radius * angle
                return math.hypot(arc_len, dz)
        
        return math.hypot(math.hypot(dx, dy), dz)

    @property
    def duration(self) -> float:
        """Computes the duration of the move in minutes."""
        if self.feedrate and self.feedrate > 0:
            return self.length / self.feedrate
        return 0.0

    @property
    def flow_rate(self) -> float:
        """Computes the flow rate (extrusion / duration)."""
        d = self.duration
        if d > 0:
            return self.extrusion / d
        return 0.0

    @property
    def xy_length(self) -> float:
        """Computes the 2D (XY) distance or arc length."""
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        
        if self.is_arc and self.arc_radius is not None and self.arc_center is not None and self.arc_radius > 0:
            e2d = math.hypot(dx, dy)
            if e2d <= 2 * self.arc_radius:
                angle = 2 * math.asin(e2d / (2 * self.arc_radius))
                return self.arc_radius * angle
                
        return math.hypot(dx, dy)
