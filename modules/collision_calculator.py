
import math

DECEL = 6.0           # gia tốc phanh (m/s^2), đường khô
REACTION_TIME = 1.0   # thời gian phản ứng của tài xế (s)
TTC_MAX = 99.0        # TTC dùng để vẽ biểu đồ / lưu CSV khi TTC = vô cực


# ---------------------------------------------------------------- TÍNH TOÁN
def kmh_to_ms(v_kmh):
    return v_kmh / 3.6


def calculate_ttc(speed_kmh, distance_m, obstacle_speed_kmh=0.0):
    """TTC (giây).
    - Vật cản đứng yên: v_tiến_gần = v_xe
    - Không tiến gần (v_tiến_gần <= 0) -> math.inf
    - Khoảng cách = 0 -> 0 (đã va chạm)"""
    if speed_kmh < 0 or distance_m < 0:
        raise ValueError("Tốc độ và khoảng cách không được âm")
    if distance_m == 0:
        return 0.0
    closing = kmh_to_ms(speed_kmh - obstacle_speed_kmh)
    if closing <= 0:
        return math.inf
    return distance_m / closing


def braking_distance(speed_kmh, decel=DECEL):
    """Quãng đường phanh: s = v^2 / (2a)."""
    v = kmh_to_ms(speed_kmh)
    return v * v / (2 * decel)


def stopping_distance(speed_kmh, decel=DECEL, reaction=REACTION_TIME):
    """Quãng đường dừng = quãng đường phản ứng + quãng đường phanh."""
    return kmh_to_ms(speed_kmh) * reaction + braking_distance(speed_kmh, decel)


def analyze(speed_kmh, distance_m, obstacle_speed_kmh=0.0):
    """Phân tích đầy đủ -> dict (đầu vào cho collision_engine / knowledge_base)."""
    ttc = calculate_ttc(speed_kmh, distance_m, obstacle_speed_kmh)
    rel = max(speed_kmh - obstacle_speed_kmh, 0)
    stop = stopping_distance(rel)
    return {
        "speed_kmh": speed_kmh,
        "distance_m": distance_m,
        "ttc_s": ttc if math.isinf(ttc) else round(ttc, 2),
        "ttc_display_s": round(min(ttc, TTC_MAX), 2),   # luôn là số hữu hạn: dùng cho biểu đồ/CSV
        "closing_speed_kmh": round(max(speed_kmh - obstacle_speed_kmh, 0), 2),
        "braking_distance_m": round(braking_distance(rel), 2),
        "stopping_distance_m": round(stop, 2),
        "can_stop_in_time": distance_m >= stop,
    }


def analyze_reading(reading):
    """Nhận thẳng dict từ SensorSimulator.read()/step() -> dict phân tích + thời điểm t."""
    out = analyze(reading["speed_kmh"], reading["distance_m"],
                  reading.get("obstacle_speed_kmh", 0.0))
    out["t"] = reading.get("t", 0.0)
    return out


# ---------------------------------------------------------------- KIỂM THỬ
def run_tests():
    results = []

    def check(name, cond):
        results.append((name, bool(cond)))

    def raises(*args):
        try:
            calculate_ttc(*args)
        except ValueError:
            return True
        return False

    # 1. Giá trị biết trước
    check("72 km/h, 100 m -> 5 s", math.isclose(calculate_ttc(72, 100), 5.0))
    check("36 km/h, 10 m -> 1 s", math.isclose(calculate_ttc(36, 10), 1.0))
    check("90 km/h, 50 m -> 2 s", math.isclose(calculate_ttc(90, 50), 2.0))
    check("Vật cản chạy 54 km/h: (90-54)=10 m/s, 30 m -> 3 s",
          math.isclose(calculate_ttc(90, 30, 54), 3.0))

    # 2. Trường hợp biên
    check("Xe đứng yên -> inf", calculate_ttc(0, 50) == math.inf)
    check("Khoảng cách 0 -> 0 (va chạm)", calculate_ttc(50, 0) == 0.0)
    check("Vật cản nhanh hơn xe -> inf", calculate_ttc(50, 30, 60) == math.inf)
    check("Cùng tốc độ -> inf", calculate_ttc(50, 30, 50) == math.inf)
    check("Từ chối tốc độ âm", raises(-1, 10))
    check("Từ chối khoảng cách âm", raises(10, -1))

    # 3. Quy luật vật lý
    check("Tốc độ tăng -> TTC giảm", calculate_ttc(40, 50) > calculate_ttc(80, 50))
    check("Khoảng cách tăng -> TTC tăng", calculate_ttc(60, 100) > calculate_ttc(60, 30))
    check("Quãng đường phanh 72 km/h, a=6 -> 33.33 m",
          math.isclose(braking_distance(72, 6), 400 / 12))
    check("Quãng đường dừng 72 km/h = 20 + 33.33 m",
          math.isclose(stopping_distance(72, 6, 1.0), 20 + 400 / 12))
    check("Phanh kịp: 30 km/h, 100 m", analyze(30, 100)["can_stop_in_time"])
    check("Không phanh kịp: 120 km/h, 20 m", not analyze(120, 20)["can_stop_in_time"])

    # 3b. Tích hợp với dạng dữ liệu của cảm biến
    r = analyze_reading({"t": 1.5, "speed_kmh": 72, "distance_m": 100})
    check("analyze_reading nhận dict cảm biến, giữ thời điểm t", r["t"] == 1.5 and r["ttc_s"] == 5.0)
    check("TTC vô cực -> ttc_display_s = 99 (hữu hạn)", analyze(0, 50)["ttc_display_s"] == TTC_MAX)
    check("analyze có vật cản chạy 54 km/h", analyze(90, 30, 54)["ttc_s"] == 3.0)

    # 4. Lưới 7 tốc độ x 6 khoảng cách, đối chiếu công thức độc lập
    ok_grid = True
    for v in (0, 20, 40, 60, 80, 100, 120):
        for d in (5, 10, 20, 50, 100, 150):
            exp = math.inf if v == 0 else d / (v / 3.6)
            got = analyze(v, d)["ttc_s"]
            if not ((math.isinf(exp) and math.isinf(got)) or abs(got - exp) < 0.01):
                ok_grid = False
    check("Lưới 42 ca (7 tốc độ x 6 khoảng cách) khớp công thức", ok_grid)
    return results


if __name__ == "__main__":
    print("=== BẢNG TTC (giây) theo tốc độ và khoảng cách ===")
    dists = (10, 20, 50, 100, 150)
    print("v(km/h) | " + " ".join(f"{d:>6}m" for d in dists) + " | S.dừng(m)")
    for v in (20, 40, 60, 80, 100, 120):
        row = " ".join(f"{calculate_ttc(v, d):>7.2f}" for d in dists)
        print(f"{v:>7} | {row} | {stopping_distance(v):>8.1f}")

    print("\n=== KẾT QUẢ KIỂM THỬ ===")
    res = run_tests()
    for name, ok in res:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    print(f"\nTổng: {sum(ok for _, ok in res)}/{len(res)} đạt")
