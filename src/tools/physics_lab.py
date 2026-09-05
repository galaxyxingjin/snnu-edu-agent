"""虚拟物理实验模拟工具：力学与电学场景的定量计算。

支持场景：
- 力学：斜面运动（含重力加速度、摩擦阻力）、自由落体、弹簧
- 电学：串联电路、并联电路
原子物理场景以图解/讲解方式呈现（配合 generate_diagram），无需本工具计算。
"""
import json
import math
import logging

from langchain.tools import tool

logger = logging.getLogger(__name__)

G_DEFAULT = 9.8


def _num(v, default=None):
    """安全转数值"""
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _r(v, n=4):
    try:
        return round(float(v), n)
    except (TypeError, ValueError):
        return v


def _simulate_slope(p):
    mass = _num(p.get("mass"), 1.0)
    angle = _num(p.get("angle"), 30.0)
    friction = _num(p.get("friction"), 0.0)
    gravity = _num(p.get("gravity"), G_DEFAULT)
    v0 = _num(p.get("velocity0"), 0.0)
    length = _num(p.get("length"), 1.0)

    theta = math.radians(angle)
    a = gravity * (math.sin(theta) - friction * math.cos(theta))

    lines = [
        "【力学·斜面运动模拟】",
        f"质量 m = {_r(mass)} kg，倾角 θ = {_r(angle)}°，动摩擦因数 μ = {_r(friction)}，重力加速度 g = {_r(gravity)} m/s²",
        f"初速度 v₀ = {_r(v0)} m/s，斜面长度 L = {_r(length)} m",
    ]
    if a <= 1e-9:
        lines.append(f"加速度 a = g·(sinθ − μ·cosθ) = {_r(a)} m/s² ≤ 0，物体因摩擦力足够大而静止（或匀速），不会自然加速下滑。")
        return "\n".join(lines)

    lines.append(f"1. 沿斜面加速度 a = g·(sinθ − μ·cosθ) = {_r(a)} m/s²")
    v_end = math.sqrt(v0 * v0 + 2 * a * length)
    lines.append(f"2. 滑到底端末速度 v = √(v₀² + 2aL) = {_r(v_end)} m/s")
    t = (-v0 + math.sqrt(v0 * v0 + 2 * a * length)) / a
    lines.append(f"3. 下滑时间 t = (√(v₀² + 2aL) − v₀) / a = {_r(t)} s")
    lines.append(f"4. 沿斜面合力 F = m·a = {_r(mass * a)} N")
    return "\n".join(lines)


def _simulate_free_fall(p):
    height = _num(p.get("height"), 10.0)
    gravity = _num(p.get("gravity"), G_DEFAULT)
    v0 = _num(p.get("velocity0"), 0.0)
    mass = _num(p.get("mass"), 1.0)
    drag_k = _num(p.get("drag_coefficient"), 0.0)  # 平方阻力 F=k·v² 的系数

    lines = [
        "【力学·自由落体模拟】",
        f"高度 h = {_r(height)} m，重力加速度 g = {_r(gravity)} m/s²，初速度 v₀ = {_r(v0)} m/s",
    ]
    v_end = math.sqrt(v0 * v0 + 2 * gravity * height)
    lines.append(f"1. 无空气阻力时末速度 v = √(v₀² + 2gh) = {_r(v_end)} m/s")
    if v0 == 0:
        t = math.sqrt(2 * height / gravity)
    else:
        t = (-v0 + math.sqrt(v0 * v0 + 2 * gravity * height)) / gravity
    lines.append(f"2. 落地时间 t = {_r(t)} s")

    if drag_k > 0:
        # 平方阻力下终端速度 v_t = sqrt(mg/k)
        v_terminal = math.sqrt(mass * gravity / drag_k) if mass > 0 and drag_k > 0 else float("inf")
        lines.append(f"3. 考虑空气阻力（F = k·v²，k = {_r(drag_k)}）时，存在终端速度 v_t = √(mg/k) = {_r(v_terminal)} m/s；")
        lines.append("   物体速度不会超过终端速度，实际落地时间更长、末速度更小。")
    else:
        lines.append("3. 上述结果为忽略空气阻力的理想值。")
    return "\n".join(lines)


def _simulate_spring(p):
    mass = _num(p.get("mass"), 1.0)
    k = _num(p.get("spring_constant"), 100.0)
    displacement = _num(p.get("displacement"), 0.1)  # 形变量

    lines = [
        "【力学·弹簧模拟】",
        f"劲度系数 k = {_r(k)} N/m，形变量 x = {_r(displacement)} m，振子质量 m = {_r(mass)} kg",
    ]
    f = k * displacement
    lines.append(f"1. 弹力（胡克定律）F = k·x = {_r(f)} N")
    if mass > 0 and k > 0:
        t_period = 2 * math.pi * math.sqrt(mass / k)
        lines.append(f"2. 简谐振动周期 T = 2π·√(m/k) = {_r(t_period)} s")
        lines.append(f"3. 频率 f = 1/T = {_r(1 / t_period)} Hz")
    return "\n".join(lines)


def _simulate_series_circuit(p):
    emf = _num(p.get("emf"))
    internal_r = _num(p.get("internal_r"), 0.0)
    resistors = p.get("resistors")
    if emf is None:
        return "电学模拟失败：缺少电源电动势 emf 参数。"

    try:
        if isinstance(resistors, str):
            resistors = json.loads(resistors)
        resistors = [float(x) for x in resistors]
    except (TypeError, ValueError, json.JSONDecodeError):
        return "电学模拟失败：resistors 参数应为电阻值列表，例如 [5, 10, 20]。"

    if not resistors or any(r < 0 for r in resistors):
        return "电学模拟失败：resistors 应为非空的正电阻值列表。"

    r_outer = sum(resistors)
    r_total = r_outer + internal_r
    current = emf / r_total

    lines = [
        "【电学·串联电路模拟】",
        f"电源电动势 E = {_r(emf)} V，内阻 r = {_r(internal_r)} Ω，串联电阻 {resistors} Ω",
        f"1. 外电路总电阻 R = {_r(r_outer)} Ω，回路总电阻 = {_r(r_total)} Ω",
        f"2. 电路电流 I = E/(R+r) = {_r(current)} A",
        f"3. 路端电压 U = E − I·r = {_r(emf - current * internal_r)} V",
    ]
    for i, ri in enumerate(resistors, 1):
        lines.append(f"4.{i - 1}. 电阻 {_r(ri)} Ω 两端电压 U = I·R = {_r(current * ri)} V，功率 P = I²·R = {_r(current * current * ri)} W")
    lines.append(f"5. 电路总功率 P = E·I = {_r(emf * current)} W")
    return "\n".join(lines)


def _simulate_parallel_circuit(p):
    emf = _num(p.get("emf"))
    internal_r = _num(p.get("internal_r"), 0.0)
    resistors = p.get("resistors")
    if emf is None:
        return "电学模拟失败：缺少电源电动势 emf 参数。"

    try:
        if isinstance(resistors, str):
            resistors = json.loads(resistors)
        resistors = [float(x) for x in resistors]
    except (TypeError, ValueError, json.JSONDecodeError):
        return "电学模拟失败：resistors 参数应为电阻值列表，例如 [10, 20]。"

    if not resistors or any(r <= 0 for r in resistors):
        return "电学模拟失败：resistors 应为非空的正电阻值列表。"

    r_par = 1.0 / sum(1.0 / ri for ri in resistors)
    r_total = r_par + internal_r
    current = emf / r_total
    terminal_v = emf - current * internal_r

    lines = [
        "【电学·并联电路模拟】",
        f"电源电动势 E = {_r(emf)} V，内阻 r = {_r(internal_r)} Ω，并联电阻 {resistors} Ω",
        f"1. 并联等效电阻 1/R = Σ(1/Ri) → R = {_r(r_par)} Ω，回路总电阻 = {_r(r_total)} Ω",
        f"2. 干路电流 I = E/(R+r) = {_r(current)} A",
        f"3. 路端电压（各支路电压）U = {_r(terminal_v)} V",
    ]
    for i, ri in enumerate(resistors, 1):
        lines.append(f"4.{i - 1}. 支路电阻 {_r(ri)} Ω 电流 I = U/R = {_r(terminal_v / ri)} A，功率 P = {_r(terminal_v * terminal_v / ri)} W")
    lines.append(f"5. 电路总功率 P = E·I = {_r(emf * current)} W")
    return "\n".join(lines)


@tool
def physics_simulation(scenario: str, params_json: str) -> str:
    """虚拟物理实验的定量模拟计算，用于精确求解力学/电学实验问题。

    Args:
        scenario: 实验场景，可选值：
            - "slope": 斜面运动（木块/小车沿斜面滑动）
            - "free_fall": 自由落体（小球下落）
            - "spring": 弹簧（胡克定律与简谐振动）
            - "series_circuit": 串联电路
            - "parallel_circuit": 并联电路
        params_json: 参数 JSON 字符串。各场景参数如下：
            - slope: {"mass":质量kg, "angle":倾角度, "friction":动摩擦因数0-1, "gravity":重力加速度默认9.8, "velocity0":初速度m/s默认0, "length":斜面长m}
            - free_fall: {"height":高度m, "gravity":重力加速度默认9.8, "velocity0":初速度默认0, "mass":质量kg, "drag_coefficient":空气阻力系数k(F=k·v²)默认0表示忽略}
            - spring: {"spring_constant":劲度系数N/m, "displacement":形变量m, "mass":振子质量kg}
            - series_circuit / parallel_circuit: {"emf":电源电动势V, "internal_r":内阻Ω默认0, "resistors":[电阻Ω列表]}

    Returns:
        str: 各物理量的计算结果（含公式与数值）。
    """
    try:
        params = json.loads(params_json) if isinstance(params_json, str) else params_json
        if not isinstance(params, dict):
            return "物理模拟失败：params_json 必须是 JSON 对象。"
    except json.JSONDecodeError:
        return "物理模拟失败：params_json 不是合法的 JSON 字符串。"

    handlers = {
        "slope": _simulate_slope,
        "free_fall": _simulate_free_fall,
        "spring": _simulate_spring,
        "series_circuit": _simulate_series_circuit,
        "parallel_circuit": _simulate_parallel_circuit,
    }

    handler = handlers.get(scenario)
    if handler is None:
        return f"物理模拟失败：不支持的场景「{scenario}」，可选 {list(handlers.keys())}。"

    try:
        return handler(params)
    except Exception as e:
        logger.error("[physics_simulation] %s failed: %s", scenario, e)
        return f"物理模拟失败：{str(e)}。请检查参数是否完整且数值合理。"