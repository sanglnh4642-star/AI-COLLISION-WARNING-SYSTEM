
import sys
import csv
import math
from pathlib import Path

# 1. XÁC ĐỊNH THƯ MỤC GỐC

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# 2. IMPORT CÁC MODULE

from simulation.scenarios import get_all_scenarios
from modules.collision_calculator import analyze
from modules.collision_engine import CollisionEngine


# Đường dẫn lưu dữ liệu mô phỏng
DATA_DIR = ROOT_DIR / "data"
CSV_FILE = DATA_DIR / "simulation_data.csv"

# 3. MÔ PHỎNG MỘT TÌNH HUỐNG
def simulate_scenario(scenario, engine):
    """
    Thực hiện mô phỏng một tình huống.

    Args:
        scenario: Dictionary chứa dữ liệu tình huống.
        engine: Đối tượng CollisionEngine.

    Returns:
        Dictionary chứa kết quả mô phỏng.
    """

    # Lấy dữ liệu đầu vào
    speed_kmh = float(scenario["speed"])
    distance_m = float(scenario["distance"])

    # Tính TTC và các thông số vật lý
    analysis = analyze(
        speed_kmh=speed_kmh,
        distance_m=distance_m
    )

    ttc = analysis["ttc_s"]

    # Chuyển đổi tốc độ từ km/h sang m/s
    # CollisionEngine sử dụng đơn vị m/s
    speed_ms = speed_kmh / 3.6

    # Chuyển TTC vô cực thành None
    engine_ttc = None if math.isinf(ttc) else ttc

    # Phân loại mức cảnh báo bằng CollisionEngine
    evaluation = engine.evaluate(
        speed=speed_ms,
        distance=distance_m,
        ttc=engine_ttc
    )

    # Tổng hợp kết quả mô phỏng
    result = {
        "scenario_id": scenario["id"],
        "scenario_name": scenario["name"],
        "description": scenario["description"],

        "speed_kmh": speed_kmh,
        "speed_ms": round(speed_ms, 2),
        "distance_m": distance_m,

        "ttc_s": "INF" if math.isinf(ttc) else round(ttc, 2),
        "ttc_display_s": analysis["ttc_display_s"],

        "closing_speed_kmh": analysis["closing_speed_kmh"],
        "braking_distance_m": analysis["braking_distance_m"],
        "stopping_distance_m": analysis["stopping_distance_m"],
        "can_stop_in_time": analysis["can_stop_in_time"],

        "alert_level": evaluation["level"],
        "rule_id": evaluation["rule_id"],
        "reason": evaluation["reason"]
    }

    return result

# 4. LƯU KẾT QUẢ VÀO FILE CSV

def save_results_to_csv(results, output_path=CSV_FILE):
    """
    Lưu danh sách kết quả mô phỏng vào file CSV.
    """

    if not results:
        print("\nKhông có dữ liệu để lưu.")
        return

    output_path = Path(output_path)

    # Tạo thư mục nếu chưa tồn tại
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Xác định các cột dữ liệu
    fieldnames = list(results[0].keys())

    # Ghi dữ liệu vào CSV
    with open(
        output_path,
        mode="w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(results)

    print("\nĐã lưu dữ liệu mô phỏng thành công!")
    print(f"Đường dẫn: {output_path}")
    print(f"Số bản ghi: {len(results)}")

# 5. CHẠY TOÀN BỘ CÁC TÌNH HUỐNG

def run_simulation(scenarios=None, output_path=CSV_FILE):
    """
    Chạy lần lượt các tình huống mô phỏng.

    Args:
        scenarios: Danh sách tình huống cần mô phỏng.
        output_path: Đường dẫn lưu file CSV.

    Returns:
        Danh sách kết quả mô phỏng.
    """

    # Nếu không truyền danh sách, lấy toàn bộ tình huống
    if scenarios is None:
        scenarios = get_all_scenarios()

    # Khởi tạo hệ thống suy luận
    engine = CollisionEngine()

    results = []

    print("\n" + "=" * 70)
    print("          HỆ THỐNG MÔ PHỎNG CẢNH BÁO VA CHẠM")
    print("=" * 70)

    # Thực hiện từng tình huống
    for scenario in scenarios:

        result = simulate_scenario(
            scenario=scenario,
            engine=engine
        )

        results.append(result)

        # Hiển thị kết quả
        print("\n" + "-" * 70)
        print(
            f"TÌNH HUỐNG {result['scenario_id']}: "
            f"{result['scenario_name']}"
        )
        print("-" * 70)

        print(f"Mô tả: {result['description']}")
        print(f"Tốc độ xe: {result['speed_kmh']} km/h")
        print(f"Tốc độ quy đổi: {result['speed_ms']} m/s")
        print(f"Khoảng cách vật cản: {result['distance_m']} m")
        print(f"TTC: {result['ttc_s']} giây")

        print(
            f"Quãng đường phanh: "
            f"{result['braking_distance_m']} m"
        )

        print(
            f"Quãng đường dừng: "
            f"{result['stopping_distance_m']} m"
        )

        print(
            f"Có thể dừng kịp: "
            f"{'Có' if result['can_stop_in_time'] else 'Không'}"
        )

        print(f"Mức cảnh báo: {result['alert_level']}")
        print(f"Luật suy luận: {result['rule_id']}")
        print(f"Lý do: {result['reason']}")

    # Lưu kết quả sau khi hoàn thành
    save_results_to_csv(
        results=results,
        output_path=output_path
    )

    # 6. THỐNG KÊ KẾT QUẢ
    print("\n" + "=" * 70)
    print("                    TỔNG KẾT MÔ PHỎNG")
    print("=" * 70)

    print(f"Tổng số tình huống: {len(results)}")

    for level in ("An toàn", "Cảnh báo", "Nguy hiểm"):

        count = sum(
            1 for item in results
            if item["alert_level"] == level
        )

        print(f"{level}: {count} tình huống")

    print("=" * 70)
    print("                 HOÀN THÀNH MÔ PHỎNG")
    print("=" * 70)

    return results

if __name__ == "__main__":
    run_simulation()
