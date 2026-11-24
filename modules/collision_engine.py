import sys
from pathlib import Path
from typing import Optional, Dict, Any

try:
    ROOT_DIR = Path(__file__).resolve().parent.parent
except NameError:
    ROOT_DIR = Path.cwd().resolve()

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from knowledge.knowledge_base import (
    ALERT_SAFE,
    ALERT_WARNING,
    ALERT_DANGER,
    THRESHOLDS,
    RULES,
)


class CollisionEngine:
    def __init__(self, rules=RULES, thresholds=THRESHOLDS):
        self.rules = sorted(rules, key=lambda r: r["priority"])
        self.thresholds = thresholds

    def _build_reason(
        self,
        rule_id: str,
        level: str,
        speed: float,
        distance: float,
        ttc: Optional[float],
    ) -> str:
        ttc_str = (
            f"{ttc:.2f}s"
            if ttc is not None
            else "không có nguy cơ va chạm trực tiếp (v=0 hoặc khoảng cách không thu hẹp)"
        )
        base = f"[{rule_id}] Tốc độ={speed:.1f}m/s, Khoảng cách={distance:.1f}m, TTC={ttc_str}."

        if rule_id == "R1":
            if ttc is not None and ttc <= self.thresholds["ttc_danger"]:
                return (
                    f"{base} Nguy hiểm: TTC <= {self.thresholds['ttc_danger']}s, "
                    "nguy cơ va chạm rất cao, cần phanh gấp."
                )
            return (
                f"{base} Nguy hiểm: Khoảng cách <= {self.thresholds['distance_danger']}m, "
                "vật cản quá gần."
            )

        if rule_id == "R2":
            return (
                f"{base} Nguy hiểm: Tốc độ >= {self.thresholds['speed_high']}m/s, "
                f"khoảng cách <= {self.thresholds['distance_warning']}m và TTC <= {self.thresholds['ttc_warning']}s."
            )

        if rule_id == "R3":
            if ttc is not None and ttc <= self.thresholds["ttc_warning"]:
                return (
                    f"{base} Cảnh báo: TTC <= {self.thresholds['ttc_warning']}s, "
                    "cần giảm tốc độ và chú ý quan sát."
                )
            return (
                f"{base} Cảnh báo: Tốc độ >= {self.thresholds['speed_medium']}m/s và "
                f"khoảng cách <= {self.thresholds['distance_warning']}m."
            )

        if rule_id == "R4":
            max_warn_dist = self.thresholds["distance_warning"] * 1.5
            return (
                f"{base} Cảnh báo: Tốc độ >= {self.thresholds['speed_high']}m/s và "
                f"khoảng cách <= {max_warn_dist:.1f}m, nên chủ động giảm tốc."
            )

        return f"{base} An toàn: Khoảng cách và thời gian phản ứng nằm trong ngưỡng an toàn."

    def evaluate(
        self,
        speed: float,
        distance: float,
        ttc: Optional[float] = None,
    ) -> Dict[str, Any]:
        for rule in self.rules:
            if rule["condition"](speed, distance, ttc):
                level = rule["level"]
                return {
                    "level": level,
                    "rule_id": rule["id"],
                    "reason": self._build_reason(rule["id"], level, speed, distance, ttc),
                    "speed": speed,
                    "distance": distance,
                    "ttc": ttc,
                }

        return {
            "level": ALERT_SAFE,
            "rule_id": "R5",
            "reason": self._build_reason("R5", ALERT_SAFE, speed, distance, ttc),
            "speed": speed,
            "distance": distance,
            "ttc": ttc,
        }

    def evaluate_from_ttc(
        self,
        ttc: Optional[float],
        speed: float = 15.0,
        distance: Optional[float] = None,
    ) -> Dict[str, Any]:
        if distance is None:
            distance = (speed * ttc) if (ttc is not None and ttc >= 0) else 100.0
        return self.evaluate(speed=speed, distance=distance, ttc=ttc)


def run_tests() -> None:
    engine = CollisionEngine()

    test_cases = [
        {"name": "Case 1 - Nguy hiểm (TTC thấp)", "speed": 22.0, "distance": 25.0, "ttc": 1.1},
        {"name": "Case 2 - Nguy hiểm (Khoảng cách sát)", "speed": 10.0, "distance": 8.0, "ttc": 0.8},
        {
            "name": "Case 3 - Nguy hiểm (Tốc độ cao + khoảng cách ngắn + TTC cảnh báo)",
            "speed": 21.0,
            "distance": 24.0,
            "ttc": 3.0,
        },
        {"name": "Case 4 - Cảnh báo (TTC vùng cảnh báo)", "speed": 14.0, "distance": 40.0, "ttc": 2.8},
        {
            "name": "Case 5 - Cảnh báo (Tốc độ cao + khoảng cách 32m, không thu hẹp)",
            "speed": 22.0,
            "distance": 32.0,
            "ttc": None,
        },
        {"name": "Case 6 - An toàn (Khoảng cách xa, TTC cao)", "speed": 12.0, "distance": 80.0, "ttc": 6.7},
        {"name": "Case 7 - An toàn (Xe đứng yên)", "speed": 0.0, "distance": 5.0, "ttc": None},
    ]

    for case in test_cases:
        res = engine.evaluate(case["speed"], case["distance"], case["ttc"])
        print(f"{case['name']} -> {res['level']} | {res['reason']}")

    direct_res = engine.evaluate_from_ttc(ttc=1.2)
    print(f"Direct TTC -> {direct_res['level']} | {direct_res['reason']}")


if __name__ == "__main__":
    run_tests()