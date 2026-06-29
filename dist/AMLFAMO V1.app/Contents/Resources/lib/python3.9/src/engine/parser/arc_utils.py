from __future__ import annotations
import math
from typing import List
from src.engine.parser.move import Point2D, Point3D

def compute_arc_center(start: Point3D, end: Point3D, i_offset: float, j_offset: float) -> Point2D:
    """Computes the center of an arc given the start point and I, J offsets."""
    return Point2D(start.x + i_offset, start.y + j_offset)

def compute_arc_radius(center: Point2D, point: Point3D) -> float:
    """Computes the radius of an arc given its center and a point on the arc."""
    return math.hypot(point.x - center.x, point.y - center.y)

def compute_arc_angle(start: Point3D, end: Point3D, center: Point2D, clockwise: bool) -> float:
    """Computes the included angle of an arc in radians."""
    angle_start = math.atan2(start.y - center.y, start.x - center.x)
    angle_end = math.atan2(end.y - center.y, end.x - center.x)
    
    if clockwise:
        angle = angle_start - angle_end
    else:
        angle = angle_end - angle_start
        
    if angle <= 0:
        angle += 2 * math.pi
    elif math.isclose(angle, 0.0):
        # A full circle if start and end are the same
        angle = 2 * math.pi
        
    return angle

def compute_arc_length(radius: float, angle: float) -> float:
    """Computes the length of an arc given its radius and included angle."""
    return radius * angle

def interpolate_arc_point(center: Point2D, radius: float, start_angle: float, fraction: float, clockwise: bool, total_angle: float) -> Point2D:
    """Interpolates a point along an arc given a fraction (0.0 to 1.0)."""
    if clockwise:
        current_angle = start_angle - (total_angle * fraction)
    else:
        current_angle = start_angle + (total_angle * fraction)
        
    x = center.x + radius * math.cos(current_angle)
    y = center.y + radius * math.sin(current_angle)
    return Point2D(x, y)

def linearize_arc(start: Point3D, end: Point3D, center: Point2D, clockwise: bool, segments: int = 20) -> List[Point3D]:
    """Converts an arc into a series of linear segments (Point3D)."""
    radius = compute_arc_radius(center, start)
    total_angle = compute_arc_angle(start, end, center, clockwise)
    start_angle = math.atan2(start.y - center.y, start.x - center.x)
    
    points = [start]
    for i in range(1, segments):
        fraction = i / segments
        pt_2d = interpolate_arc_point(center, radius, start_angle, fraction, clockwise, total_angle)
        
        # Interpolate Z
        z = start.z + (end.z - start.z) * fraction
        
        points.append(Point3D(pt_2d.x, pt_2d.y, z))
        
    points.append(end)
    return points
