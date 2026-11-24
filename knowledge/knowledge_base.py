ALERT_SAFE = "An toàn"
ALERT_WARNING = "Cảnh báo"
ALERT_DANGER = "Nguy hiểm"

THRESHOLDS = {
    "ttc_danger": 1.5,
    "ttc_warning": 3.5,
    "distance_danger": 10.0,
    "distance_warning": 25.0,
    "speed_high": 20.0,
    "speed_medium": 10.0,
}

RULES = [
    {
        "id": "R1",
        "priority": 1,
        "level": ALERT_DANGER,
        "description": "TTC rất thấp hoặc khoảng cách cực gần khi xe đang di chuyển",
        "condition": lambda s, d, ttc: s > 0 and (
            (ttc is not None and ttc <= THRESHOLDS["ttc_danger"])
            or d <= THRESHOLDS["distance_danger"]
        ),
    },
    {
        "id": "R2",
        "priority": 2,
        "level": ALERT_DANGER,
        "description": "Tốc độ cao kết hợp khoảng cách ngắn và TTC trong vùng cảnh báo",
        "condition": lambda s, d, ttc: (
            s >= THRESHOLDS["speed_high"]
            and d <= THRESHOLDS["distance_warning"]
            and ttc is not None
            and ttc <= THRESHOLDS["ttc_warning"]
        ),
    },
    {
        "id": "R3",
        "priority": 3,
        "level": ALERT_WARNING,
        "description": "TTC trong vùng cảnh báo hoặc khoảng cách ngắn ở tốc độ trung bình/cao",
        "condition": lambda s, d, ttc: s > 0 and (
            (ttc is not None and ttc <= THRESHOLDS["ttc_warning"])
            or (d <= THRESHOLDS["distance_warning"] and s >= THRESHOLDS["speed_medium"])
        ),
    },
    {
        "id": "R4",
        "priority": 4,
        "level": ALERT_WARNING,
        "description": "Xe chạy tốc độ cao với khoảng cách chưa đủ an toàn",
        "condition": lambda s, d, ttc: (
            s >= THRESHOLDS["speed_high"]
            and d <= THRESHOLDS["distance_warning"] * 1.5
        ),
    },
    {
        "id": "R5",
        "priority": 5,
        "level": ALERT_SAFE,
        "description": "Tốc độ, khoảng cách và TTC đều nằm trong giới hạn an toàn hoặc xe dừng",
        "condition": lambda s, d, ttc: True,
    },
]