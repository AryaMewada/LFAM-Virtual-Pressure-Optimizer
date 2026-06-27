import math

def flow_factor(flow_rate: float, max_flow_rate: float) -> float:
    """Computes a linear ratio [0, 1] for flow rate."""
    if max_flow_rate <= 0:
        return 0.0
    return max(0.0, min(1.0, flow_rate / max_flow_rate))

def speed_factor(feedrate: float, optimal_feedrate: float, max_feedrate: float) -> float:
    """Computes a normalized distance from optimal speed [0, 1]."""
    if max_feedrate <= 0:
        return 0.0
    diff = abs(feedrate - optimal_feedrate)
    return max(0.0, min(1.0, diff / max_feedrate))

def corner_factor(corner_angle_deg: float, sensitivity: float) -> float:
    """Computes an exponential factor based on corner deflection."""
    # Deflection angle (180 = full reversal, 0 = straight)
    # Actually, in geometry analyzer: 0 = straight, 180 = full reversal.
    # The prompt says: "angle is deflection (180 - corner_angle)" Wait! 
    # In my geometry_analyzer I did: "0 = straight, 180 = full reversal" which means it IS the deflection angle.
    # The prompt says: "where angle is deflection (180 - corner_angle)" implying corner_angle is the internal angle (180=straight).
    # If corner_angle is internal (180 straight), then deflection = 180 - corner_angle.
    # Let's assume corner_angle_deg here is the raw angle from geometry_analyzer.
    # If geometry analyzer returns 0 for straight and 180 for reversal, then angle = corner_angle_deg.
    # Let's re-read the prompt: "corner_angle: float – angle in degrees between this move direction and next move (0° = straight, 180° = full reversal)"
    # So corner_angle_deg IS the deflection.
    # Formula: 1 - exp(-sensitivity * angle / 90)
    angle = corner_angle_deg
    return 1.0 - math.exp(-sensitivity * angle / 90.0)

def curve_factor(curve_radius: float, min_radius: float, sensitivity: float) -> float:
    """Computes a factor [0, 1] based on tight curves."""
    if curve_radius == float('inf') or curve_radius <= 0:
        return 0.0
    val = sensitivity * min_radius / max(curve_radius, min_radius)
    return max(0.0, min(1.0, val))

def history_factor(previous_vpis: list[float], decay: float) -> float:
    """Computes an exponentially weighted moving average of previous VPIs [0, 1]."""
    if not previous_vpis:
        return 0.0
    ewma = 0.0
    weight_sum = 0.0
    for i, vpi in enumerate(reversed(previous_vpis)):
        w = (1.0 - decay) ** i
        ewma += vpi * w
        weight_sum += w
    if weight_sum > 0:
        return max(0.0, min(1.0, ewma / weight_sum))
    return 0.0

def acceleration_factor(flow_rate_change: float, max_flow_rate: float) -> float:
    """Computes a factor [0, 1] based on sudden flow rate changes."""
    if max_flow_rate <= 0:
        return 0.0
    val = abs(flow_rate_change) / max_flow_rate
    return max(0.0, min(1.0, val))

def start_stop_factor(is_path_start: bool, is_path_end: bool, distance_from_start: float, distance_from_end: float, ramp_length: float) -> float:
    """Computes a factor [0, 1] based on proximity to start or end of a path."""
    if ramp_length <= 0:
        return 0.0
    factor = 0.0
    if is_path_start or distance_from_start < ramp_length:
        factor = max(factor, 1.0 - (distance_from_start / ramp_length))
    if is_path_end or distance_from_end < ramp_length:
        factor = max(factor, 1.0 - (distance_from_end / ramp_length))
    return max(0.0, min(1.0, factor))

def segment_density_factor(segment_length: float, min_length: float, sensitivity: float) -> float:
    """Computes a factor [0, 1] based on segment density."""
    if segment_length <= 0:
        return min(1.0, sensitivity)
    if segment_length >= min_length:
        return 0.0
    val = sensitivity * (min_length - segment_length) / min_length
    return max(0.0, min(1.0, val))
