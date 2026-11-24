
# Danh sách các tình huống mô phỏng
SCENARIOS = [
    {
        "id": 1,
        "name": "Tình huống an toàn",
        "description": "Xe di chuyển với tốc độ thấp, vật cản ở khoảng cách xa.",
        "speed": 30,
        "distance": 50
    },
    {
        "id": 2,
        "name": "Tình huống có nguy cơ va chạm",
        "description": "Xe di chuyển với tốc độ trung bình, khoảng cách đến vật cản giảm.",
        "speed": 60,
        "distance": 50
    },
    {
        "id": 3,
        "name": "Tình huống nguy hiểm",
        "description": "Xe di chuyển nhanh và vật cản ở khoảng cách gần.",
        "speed": 72,
        "distance": 30
    },
    {
        "id": 4,
        "name": "Tình huống nguy hiểm cao",
        "description": "Xe di chuyển với tốc độ cao, khoảng cách đến vật cản rất gần.",
        "speed": 90,
        "distance": 25
    }
]


def get_all_scenarios():
    """
    Lấy danh sách tất cả tình huống mô phỏng.
    """
    return [scenario.copy() for scenario in SCENARIOS]


def get_scenario_by_id(scenario_id):
    """
    Lấy tình huống theo mã ID.

    Args:
        scenario_id: Mã tình huống cần tìm.

    Returns:
        Một tình huống nếu tìm thấy.

    Raises:
        ValueError: Nếu không tìm thấy tình huống.
    """
    for scenario in SCENARIOS:
        if scenario["id"] == scenario_id:
            return scenario.copy()

    raise ValueError(
        f"Không tìm thấy tình huống có ID = {scenario_id}"
    )


def display_scenarios():
    """
    Hiển thị danh sách các tình huống mô phỏng.
    """
    print("\n========== DANH SÁCH TÌNH HUỐNG MÔ PHỎNG ==========")

    for scenario in SCENARIOS:
        print(f"\nMã tình huống: {scenario['id']}")
        print(f"Tên: {scenario['name']}")
        print(f"Mô tả: {scenario['description']}")
        print(f"Tốc độ xe: {scenario['speed']} km/h")
        print(f"Khoảng cách vật cản: {scenario['distance']} m")

    print("\n===================================================")


# Chạy thử file độc lập
if __name__ == "__main__":
    display_scenarios()
