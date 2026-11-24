import base64
import html
import math
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Cảnh báo nguy cơ va chạm", layout="wide")

# ----------------------------------------------------------------------
# 0. Nạp module của nhóm
# ----------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
for _p in (HERE, HERE.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


_SAMPLE_THRESHOLDS = {"ttc_danger": 1.5, "ttc_warning": 3.5, "distance_danger": 10.0,
                      "distance_warning": 25.0, "speed_high": 20.0, "speed_medium": 10.0}
_SAMPLE_SCENARIOS = [
    {"id": 1, "name": "Tình huống an toàn",
     "description": "Xe di chuyển với tốc độ thấp, vật cản ở khoảng cách xa.",
     "speed": 30, "distance": 50},
    {"id": 2, "name": "Tình huống có nguy cơ va chạm",
     "description": "Xe di chuyển với tốc độ trung bình, khoảng cách đến vật cản giảm.",
     "speed": 60, "distance": 50},
    {"id": 3, "name": "Tình huống nguy hiểm",
     "description": "Xe di chuyển nhanh và vật cản ở khoảng cách gần.",
     "speed": 72, "distance": 30},
    {"id": 4, "name": "Tình huống nguy hiểm cao",
     "description": "Xe di chuyển với tốc độ cao, khoảng cách đến vật cản rất gần.",
     "speed": 90, "distance": 25},
]


def _sample_get_all_scenarios():
    return [dict(x) for x in _SAMPLE_SCENARIOS]


def _sample_analyze(speed_kmh, distance_m, obstacle_speed_kmh=0.0):
    if speed_kmh < 0 or distance_m < 0:
        raise ValueError("Tốc độ và khoảng cách không được âm")
    closing = (speed_kmh - obstacle_speed_kmh) / 3.6
    if distance_m == 0:
        ttc = 0.0
    elif closing <= 0:
        ttc = math.inf
    else:
        ttc = distance_m / closing
    rel = max(speed_kmh - obstacle_speed_kmh, 0)
    v = rel / 3.6
    braking = v * v / (2 * 6.0)          # DECEL = 6 m/s²
    stop = v * 1.0 + braking             # REACTION_TIME = 1 s
    return {
        "ttc_s": ttc if math.isinf(ttc) else round(ttc, 2),
        "braking_distance_m": round(braking, 2),
        "stopping_distance_m": round(stop, 2),
        "can_stop_in_time": distance_m >= stop,
    }


class _SampleEngine:
    """Luật R1..R5 giống knowledge_base.py / collision_engine.py."""

    def evaluate(self, speed, distance, ttc=None):
        t = _SAMPLE_THRESHOLDS
        s, d = speed, distance
        if s > 0 and ((ttc is not None and ttc <= t["ttc_danger"]) or d <= t["distance_danger"]):
            level, rid, note = "Nguy hiểm", "R1", "TTC rất thấp hoặc vật cản quá gần, cần phanh gấp."
        elif (s >= t["speed_high"] and d <= t["distance_warning"]
              and ttc is not None and ttc <= t["ttc_warning"]):
            level, rid, note = "Nguy hiểm", "R2", "Tốc độ cao, khoảng cách ngắn và TTC trong vùng cảnh báo."
        elif s > 0 and ((ttc is not None and ttc <= t["ttc_warning"])
                        or (d <= t["distance_warning"] and s >= t["speed_medium"])):
            level, rid, note = "Cảnh báo", "R3", "Cần giảm tốc độ và chú ý quan sát."
        elif s >= t["speed_high"] and d <= t["distance_warning"] * 1.5:
            level, rid, note = "Cảnh báo", "R4", "Tốc độ cao, khoảng cách chưa đủ an toàn."
        else:
            level, rid, note = "An toàn", "R5", "Khoảng cách và thời gian phản ứng nằm trong ngưỡng an toàn."
        ttc_s = f"{ttc:.2f}s" if ttc is not None else "không có nguy cơ va chạm trực tiếp"
        reason = f"[{rid}] Tốc độ={s:.1f}m/s, Khoảng cách={d:.1f}m, TTC={ttc_s}. {note}"
        return {"level": level, "rule_id": rid, "reason": reason,
                "speed": s, "distance": d, "ttc": ttc}


try:
    from modules.collision_calculator import analyze, DECEL, REACTION_TIME
    from modules.sensor_simulator import SPEED_MAX, DIST_MAX
    from modules.collision_engine import CollisionEngine
    from knowledge.knowledge_base import THRESHOLDS
    from simulation.scenarios import get_all_scenarios
    STANDALONE, STANDALONE_REASON = False, ""
except Exception as e:      # thiếu module của nhóm -> chạy độc lập với dữ liệu mẫu
    analyze, DECEL, REACTION_TIME = _sample_analyze, 6.0, 1.0
    SPEED_MAX, DIST_MAX = 200.0, 200.0
    CollisionEngine, THRESHOLDS = _SampleEngine, _SAMPLE_THRESHOLDS
    get_all_scenarios = _sample_get_all_scenarios
    STANDALONE, STANDALONE_REASON = True, f"{type(e).__name__}: {e}"

ENGINE = CollisionEngine()


try:
    import charts
    CHARTS_ERROR = None
except Exception as e:          # không có file, hoặc file lỗi khi import
    charts = None
    CHARTS_ERROR = f"{type(e).__name__}: {e}"


def draw_charts(df: pd.DataFrame) -> None:
    fn = getattr(charts, "render_all", None) if charts else None
    if fn is None:
        if charts is None and "No module named 'charts'" in (CHARTS_ERROR or ""):
            st.info("Chưa có biểu đồ: đặt file charts.py (Người 4) vào thư mục gui/ để hiển thị.")
        elif charts is None:
            st.warning(f"Không nạp được charts.py ({CHARTS_ERROR}).")
        else:
            st.info("charts.py chưa có hàm render_all(df) nên chưa hiển thị biểu đồ.")
        return
    try:
        fn(df)
    except Exception as e:
        st.warning(f"charts.render_all bị lỗi ({type(e).__name__}: {e}).")


def draw_comparison(rows: list) -> None:
    fn = getattr(charts, "scenario_comparison_chart", None) if charts else None
    if fn is None:
        st.caption("(Biểu đồ so sánh sẽ hiện khi charts.py có hàm scenario_comparison_chart.)")
        return
    try:
        fn(rows)
    except Exception as e:
        st.warning(f"charts.scenario_comparison_chart bị lỗi ({type(e).__name__}: {e}).")


MESSAGES = {
    "NGUY HIỂM": "Phát hiện nguy cơ va chạm! Cần phanh khẩn cấp.",
    "CẢNH BÁO": "Khoảng cách không an toàn, cần giảm tốc độ.",
    "AN TOÀN": "Khoảng cách hiện tại nằm trong vùng an toàn.",
}
UI_COLORS = {  # (nền, chữ)
    "AN TOÀN": ("#2ecc71", "#ffffff"),
    "CẢNH BÁO": ("#f1c40f", "#1b1b1b"),
    "NGUY HIỂM": ("#e74c3c", "#ffffff"),
}


# ----------------------------------------------------------------------
# 1. Đánh giá một trạng thái = Người 1 (analyze) + Người 2 (CollisionEngine)
# ----------------------------------------------------------------------
def evaluate(speed_kmh: float, distance: float) -> dict:
    sp = max(float(speed_kmh), 0.0)
    d = max(float(distance), 0.0)

    a = analyze(speed_kmh=sp, distance_m=d)              # Người 1
    ttc = a["ttc_s"]                                     # số giây hoặc math.inf
    res = ENGINE.evaluate(                               # Người 2 (đơn vị m/s)
        speed=sp / 3.6,
        distance=d,
        ttc=None if math.isinf(ttc) else ttc,
    )
    level = res["level"].upper()                         # "Cảnh báo" -> "CẢNH BÁO"
    return {
        "level": level,
        "rule_id": res["rule_id"],
        "reason": res["reason"],
        "message": MESSAGES[level],
        "ttc": ttc,
        "d_stop": a["stopping_distance_m"],
        "d_brake": a["braking_distance_m"],
        "can_stop": a["can_stop_in_time"],
        # Khoảng cách tương ứng ngưỡng TTC cảnh báo (TTC = d / v  =>  d = v * TTC)
        "d_warning": (sp / 3.6) * THRESHOLDS["ttc_warning"],
    }


def banner_html(r: dict) -> str:
    """Khung màu hiển thị mức cảnh báo + thông báo + luật suy luận của Người 2."""
    bg, fg = UI_COLORS[r["level"]]
    return (
        f'<div style="background:{bg};color:{fg};padding:14px 20px;border-radius:10px;">'
        f'<span style="font-size:28px;font-weight:700;">{r["level"]}</span><br>'
        f'<span style="font-size:16px;">{r["message"]}</span><br>'
        f'<span style="font-size:13px;opacity:.85;">{html.escape(r["reason"])}</span></div>'
    )


def svg_img(svg: str) -> str:
    """Nhúng SVG dưới dạng <img> base64 để Streamlit chắc chắn hiển thị được."""
    b64 = base64.b64encode(svg.encode("utf-8")).decode()
    return f'<img src="data:image/svg+xml;base64,{b64}" style="width:100%;max-height:230px"/>'


# ----------------------------------------------------------------------
# 2. Các tình huống mô phỏng (lấy từ simulation/scenarios.py của Người 3)
# ----------------------------------------------------------------------
def build_scenarios() -> dict:
    sc = {}
    for s in get_all_scenarios():
        label = f"TH{s['id']} - {s['name']} ({s['speed']} km/h, {s['distance']} m)"
        sc[label] = (int(round(s["speed"])), int(round(s["distance"])))
    sc["Tùy chỉnh"] = None
    return sc


SCENARIOS = build_scenarios()
TICK = 0.25     # chu kỳ cập nhật giao diện (s thực)
SUB_DT = 0.05   # bước tính toán nhỏ bên trong mỗi chu kỳ (s mô phỏng)
V_MAX = float(SPEED_MAX)
DRIVE_MODES = ["Giữ tốc độ", "Tăng tốc", "Giảm tốc"]


# ----------------------------------------------------------------------
# 3. Quản lý trạng thái mô phỏng
#    speed     : tốc độ ban đầu do người dùng chọn (slider)
#    cur_speed : tốc độ hiện tại của xe (thay đổi khi tăng/giảm tốc/phanh)
# ----------------------------------------------------------------------
def reset_sim() -> None:
    ss = st.session_state
    ss.running = False
    ss.collided = False
    ss.stopped = False
    ss.braking = False
    ss.warn_t = None        # thời điểm bắt đầu nhận cảnh báo
    ss.impact_speed = 0.0
    ss.t = 0.0
    ss.d0 = float(ss.dist0)
    ss.distance = float(ss.dist0)
    ss.cur_speed = float(ss.speed)
    ss.history = []


def on_scenario_change() -> None:
    preset = SCENARIOS[st.session_state.scenario]
    if preset is not None:
        st.session_state.speed, st.session_state.dist0 = preset
    reset_sim()


def on_speed_change() -> None:
    if not st.session_state.braking:
        st.session_state.cur_speed = float(st.session_state.speed)


def on_start() -> None:
    ss = st.session_state
    if ss.collided or ss.stopped or ss.distance <= 0:
        reset_sim()
    ss.running = True


def on_pause() -> None:
    st.session_state.running = False


def clear_runs() -> None:
    st.session_state.runs = []


def log_run(auto_brake: bool, drive: str) -> None:
    """Ghi kết quả một lần mô phỏng đã kết thúc để so sánh (yêu cầu 1.3.3 trong báo cáo)."""
    ss = st.session_state
    order = ["AN TOÀN", "CẢNH BÁO", "NGUY HIỂM"]
    worst = max((h["level"] for h in ss.history), key=order.index)
    outcome = (f"Va chạm ({ss.impact_speed:.1f} km/h)" if ss.collided
               else f"Dừng, còn {ss.distance:.1f} m")
    ss.runs.append({
        "Tình huống": ss.scenario.split(" - ")[0],
        "Tốc độ đầu (km/h)": ss.speed,
        "Khoảng cách đầu (m)": ss.dist0,
        "Chế độ lái": drive,
        "Tự phanh": "Có" if auto_brake else "Không",
        "Mức cao nhất": worst,
        "Kết quả": outcome,
        "Thời gian (s)": round(ss.t, 2),
    })


def init_state() -> None:
    if "runs" not in st.session_state:
        st.session_state.runs = []
    if "scenario" not in st.session_state:
        st.session_state.scenario = list(SCENARIOS)[0]
        st.session_state.speed, st.session_state.dist0 = SCENARIOS[st.session_state.scenario]
        reset_sim()


def sim_step(multiplier: float, auto_brake: bool, delay: float,
             drive: str = "Giữ tốc độ", accel: float = 2.0) -> None:
    """
    Tiến mô phỏng một chu kỳ (chia thành nhiều bước nhỏ SUB_DT cho chính xác).
    - Giữ tốc độ: xe chạy tốc độ không đổi tiến về vật cản đứng yên.
    - Tăng/Giảm tốc: người dùng điều khiển với gia tốc `accel` (m/s²).
    - Tài xế phanh: sau khi CollisionEngine báo CẢNH BÁO/NGUY HIỂM và chờ `delay` giây
      phản ứng, xe phanh với gia tốc DECEL (của Người 1) cho đến khi dừng.
      Phanh tự động được ưu tiên hơn điều khiển thủ công.
    """
    ss = st.session_state
    n = max(1, round(TICK * multiplier / SUB_DT))
    for _ in range(n):
        v_old = ss.cur_speed / 3.6

        if auto_brake and not ss.braking:
            if evaluate(ss.cur_speed, ss.distance)["level"] != "AN TOÀN":
                if ss.warn_t is None:
                    ss.warn_t = ss.t
                if ss.t - ss.warn_t >= delay - 1e-9:
                    ss.braking = True
            else:
                ss.warn_t = None

        if ss.braking:
            v_new = max(v_old - DECEL * SUB_DT, 0.0)
        elif drive == "Tăng tốc":
            v_new = min(v_old + accel * SUB_DT, V_MAX / 3.6)
        elif drive == "Giảm tốc":
            v_new = max(v_old - accel * SUB_DT, 0.0)
        else:
            v_new = v_old

        ss.distance -= (v_old + v_new) / 2 * SUB_DT
        ss.cur_speed = v_new * 3.6
        ss.t += SUB_DT

        if ss.distance <= 0:                 # va chạm
            ss.distance = 0.0
            ss.collided = True
            ss.impact_speed = ss.cur_speed
            ss.running = False
            break
        if v_new <= 0:                       # xe đã dừng trước vật cản
            ss.stopped = True
            ss.running = False
            break

    r = evaluate(ss.cur_speed, ss.distance)
    ss.history.append({
        "t": round(ss.t, 2), "speed": round(ss.cur_speed, 2),
        "distance": round(ss.distance, 2),
        "d_stop": r["d_stop"], "d_warning": round(r["d_warning"], 2),
        "ttc": r["ttc"], "level": r["level"], "rule_id": r["rule_id"],
        "braking": ss.braking,
    })
    if ss.collided or ss.stopped:
        log_run(auto_brake, drive)


# ----------------------------------------------------------------------
# 4. Hình ảnh xe và vật cản (SVG)
# ----------------------------------------------------------------------
def road_svg(distance: float, d0: float, level: str, speed: float) -> str:
    color = UI_COLORS[level][0]
    x_start, car_w, x_obs = 30, 100, 700
    progress = 0.0 if d0 <= 0 else min(max(1 - distance / d0, 0.0), 1.0)
    car_x = x_start + progress * (x_obs - x_start - car_w)
    front = car_x + car_w
    mid = (front + x_obs) / 2
    gap_label = f"{distance:.1f} m"
    dashes = "".join(f'<rect x="{x}" y="128" width="30" height="4" fill="#ecf0f1"/>'
                     for x in range(20, 780, 70))
    return f"""
<svg viewBox="0 0 800 190" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-height:230px">
  <rect x="0" y="95" width="800" height="70" fill="#4a4f55"/>
  {dashes}
  <line x1="{front}" y1="70" x2="{x_obs}" y2="70" stroke="{color}" stroke-width="4"/>
  <line x1="{front}" y1="62" x2="{front}" y2="78" stroke="{color}" stroke-width="4"/>
  <line x1="{x_obs}" y1="62" x2="{x_obs}" y2="78" stroke="{color}" stroke-width="4"/>
  <text x="{mid}" y="55" text-anchor="middle" font-size="22" font-weight="bold" fill="{color}">{gap_label}</text>
  <rect x="{car_x + 15}" y="82" width="60" height="22" rx="6" fill="{color}" stroke="#222" stroke-width="2"/>
  <rect x="{car_x}" y="98" width="{car_w}" height="30" rx="8" fill="{color}" stroke="#222" stroke-width="2"/>
  <circle cx="{car_x + 22}" cy="130" r="10" fill="#222"/>
  <circle cx="{car_x + car_w - 22}" cy="130" r="10" fill="#222"/>
  <text x="{car_x + car_w / 2}" y="118" text-anchor="middle" font-size="13" font-weight="bold" fill="#fff">{speed:.0f} km/h</text>
  <rect x="{x_obs}" y="85" width="40" height="55" fill="#7f8c8d" stroke="#222" stroke-width="2"/>
  <rect x="{x_obs}" y="85" width="40" height="14" fill="#e74c3c"/>
  <rect x="{x_obs}" y="113" width="40" height="14" fill="#e74c3c"/>
  <text x="{x_obs + 20}" y="170" text-anchor="middle" font-size="13" fill="#888">Vật cản</text>
</svg>"""


# ----------------------------------------------------------------------
# 5. Giao diện
# ----------------------------------------------------------------------
init_state()
ss = st.session_state

st.title("Mô phỏng hệ thống cảnh báo nguy cơ va chạm")

with st.sidebar:
    st.header("Điều khiển mô phỏng")
    st.selectbox("Tình huống mô phỏng", list(SCENARIOS), key="scenario",
                 on_change=on_scenario_change)
    st.slider("Tốc độ ban đầu (km/h)", 0, int(SPEED_MAX), key="speed",
              on_change=on_speed_change)
    st.slider("Khoảng cách ban đầu (m)", 1, int(DIST_MAX), key="dist0",
              on_change=reset_sim)
    multiplier = st.slider("Tốc độ phát mô phỏng (x)", 0.5, 5.0, 1.0, 0.5)

    st.divider()
    st.subheader("Điều khiển tốc độ")
    drive = st.radio("Chế độ lái", DRIVE_MODES, horizontal=True,
                     help=f"Đổi được cả khi đang chạy. Tăng tốc tối đa {int(SPEED_MAX)} km/h; "
                          "giảm tốc về 0 thì xe dừng.")
    accel = st.slider("Gia tốc (m/s²)", 0.5, 5.0, 2.0, 0.5, disabled=(drive == "Giữ tốc độ"))
    auto_brake = st.checkbox("Tài xế phanh khi nhận cảnh báo", value=False,
                             help="Tắt: xe không tự phanh. Bật: sau khi hệ thống cảnh báo và hết "
                                  "độ trễ phản ứng, xe phanh cho đến khi dừng.")
    delay = st.slider("Độ trễ phản ứng của tài xế (s)", 0.0, 3.0, float(REACTION_TIME), 0.1,
                      disabled=not auto_brake)

    b1, b2, b3 = st.columns(3)
    b1.button("Bắt đầu", on_click=on_start, width="stretch", type="primary")
    b2.button("Tạm dừng", on_click=on_pause, width="stretch")
    b3.button("Đặt lại", on_click=reset_sim, width="stretch")

    st.caption(
        f"Tham số nhóm: phanh a = {DECEL} m/s², phản ứng = {REACTION_TIME} s. "
        f"TTC: nguy hiểm ≤ {THRESHOLDS['ttc_danger']} s, cảnh báo ≤ {THRESHOLDS['ttc_warning']} s. "
        f"Khoảng cách: nguy hiểm ≤ {THRESHOLDS['distance_danger']} m, "
        f"cảnh báo ≤ {THRESHOLDS['distance_warning']} m."
    )


# Chỉ tự làm mới khi đang mô phỏng
@st.fragment(run_every=TICK if ss.running else None)
def live_view() -> None:
    if ss.running:
        sim_step(multiplier, auto_brake, delay, drive, accel)
        if not ss.running:      # vừa kết thúc -> rerun để tắt run_every
            st.rerun()

    r = evaluate(ss.cur_speed, ss.distance)

    # Ba mức cảnh báo + thông báo + luật suy luận của Người 2
    st.markdown(banner_html(r), unsafe_allow_html=True)

    # Trạng thái hệ thống
    if ss.collided:
        status = "Đã va chạm"
    elif ss.stopped:
        status = "Xe đã dừng"
    elif ss.running:
        status = "Đang mô phỏng"
    elif ss.history:
        status = "Tạm dừng"
    else:
        status = "Sẵn sàng"
    st.caption(f"Trạng thái hệ thống: **{status}**")

    # Trạng thái tài xế / kết quả
    if ss.collided:
        st.error(f"Xe đã va chạm vật cản ở tốc độ {ss.impact_speed:.1f} km/h. "
                 "Nhấn 'Đặt lại' để chạy lại.")
    elif ss.stopped:
        st.success(f"Xe đã dừng, cách vật cản {ss.distance:.1f} m. "
                   "Nhấn 'Đặt lại' để chạy lại.")
    elif ss.running and ss.braking:
        st.info(f"Tài xế đang phanh (giảm tốc {DECEL:.0f} m/s²).")
    elif ss.running and ss.warn_t is not None:
        left = max(delay - (ss.t - ss.warn_t), 0.0)
        st.info(f"Tài xế đã nhận cảnh báo, đang phản ứng... còn {left:.1f} s.")
    elif ss.running and drive == "Tăng tốc":
        st.info(f"Đang tăng tốc +{accel:.1f} m/s².")
    elif ss.running and drive == "Giảm tốc":
        st.info(f"Đang giảm tốc −{accel:.1f} m/s².")

    # Tốc độ, khoảng cách, TTC, quãng đường dừng
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Tốc độ", f"{ss.cur_speed:.1f} km/h")
    m2.metric("Khoảng cách", f"{ss.distance:.1f} m")
    m3.metric("TTC", "∞" if math.isinf(r["ttc"]) else f"{r['ttc']:.2f} s")
    m4.metric("Quãng đường dừng", f"{r['d_stop']:.1f} m")
    m5.metric("Ngưỡng cảnh báo", f"{r['d_warning']:.1f} m",
              help=f"Khoảng cách ứng với TTC = {THRESHOLDS['ttc_warning']} s (d = v × TTC)")
    m6.metric("Dừng kịp?", "Có" if r["can_stop"] else "Không")

    # Mô phỏng trực quan
    st.markdown(svg_img(road_svg(ss.distance, ss.d0, r["level"], ss.cur_speed)),
                unsafe_allow_html=True)

    # Biểu đồ theo thời gian
    draw_charts(pd.DataFrame(ss.history))


live_view()

# ----------------------------------------------------------------------
# 6. So sánh các tình huống
# ----------------------------------------------------------------------
with st.expander("So sánh các tình huống mô phỏng"):
    rows = []
    for name, preset in SCENARIOS.items():
        if preset is None:
            continue
        sp, di = preset
        e = evaluate(sp, di)
        rows.append({
            "name": name.split(" - ")[0], "speed": sp, "distance": di,
            "d_stop": e["d_stop"], "d_warning": round(e["d_warning"], 2),
            "ttc": None if math.isinf(e["ttc"]) else e["ttc"],
            "can_stop": e["can_stop"], "level": e["level"], "rule_id": e["rule_id"],
        })
    draw_comparison(rows)
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

with st.expander("Kết quả các lần mô phỏng (để so sánh)"):
    if ss.runs:
        st.dataframe(pd.DataFrame(ss.runs), width="stretch", hide_index=True)
        st.button("Xóa lịch sử các lần chạy", on_click=clear_runs)
    else:
        st.caption("Chưa có lần mô phỏng nào kết thúc (xe va chạm hoặc dừng).")

with st.expander("Nhập dữ liệu cảm biến thủ công (kiểm tra nhanh)"):
    c1, c2 = st.columns(2)
    man_speed = c1.number_input("Tốc độ (km/h)", 0.0, float(SPEED_MAX), 50.0, 1.0)
    man_dist = c2.number_input("Khoảng cách đến vật cản (m)", 0.0, float(DIST_MAX), 40.0, 1.0)
    if st.button("Kiểm tra"):
        res = evaluate(man_speed, man_dist)
        st.markdown(banner_html(res), unsafe_allow_html=True)
        st.write(
            f"TTC: **{'∞' if math.isinf(res['ttc']) else format(res['ttc'], '.2f') + ' s'}** | "
            f"Quãng đường dừng: **{res['d_stop']:.1f} m** | "
            f"Ngưỡng cảnh báo: **{res['d_warning']:.1f} m** | "
            f"Dừng kịp: **{'Có' if res['can_stop'] else 'Không'}** | "
            f"Luật: **{res['rule_id']}**"
        )

with st.expander("Dữ liệu mô phỏng đã ghi"):
    if ss.history:
        hist_df = pd.DataFrame(ss.history)
        st.dataframe(hist_df, width="stretch", hide_index=True)
        st.download_button("Tải CSV", hist_df.to_csv(index=False).encode("utf-8-sig"),
                           file_name="simulation_history.csv", mime="text/csv")
    else:
        st.caption("Chưa có dữ liệu.")