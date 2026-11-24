
import random

SPEED_MIN, SPEED_MAX = 0.0, 200.0      # km/h
DIST_MIN, DIST_MAX = 0.5, 200.0        # m


# ---------------------------------------------------------------- CHUẨN HÓA
def normalize_data(speed, distance):
    """Chuẩn hóa dữ liệu thô -> (speed_kmh, distance_m).
    - Ép về số thực, báo lỗi nếu không phải số / NaN / âm
    - Kẹp trong giới hạn cảm biến, làm tròn 2 chữ số"""
    try:
        speed, distance = float(speed), float(distance)
    except (TypeError, ValueError):
        raise ValueError("Tốc độ và khoảng cách phải là số")
    if speed != speed or distance != distance:
        raise ValueError("Dữ liệu cảm biến lỗi (NaN)")
    if speed < 0 or distance < 0:
        raise ValueError("Tốc độ và khoảng cách không được âm")
    speed = min(max(speed, SPEED_MIN), SPEED_MAX)
    distance = min(max(distance, DIST_MIN), DIST_MAX)
    return round(speed, 2), round(distance, 2)


# ---------------------------------------------------------------- CẢM BIẾN
class SensorSimulator:
    """Sinh dữ liệu cảm biến theo từng bước thời gian dt (giây).

    mode:
      "approach" : xe giữ nguyên tốc độ, lao dần tới vật cản đứng yên
      "braking"  : xe phanh với gia tốc decel (m/s^2)
      "constant" : xe chạy, khoảng cách không đổi (vật cản chạy cùng tốc độ)
      "random"   : mỗi lần đọc sinh tốc độ / khoảng cách ngẫu nhiên
    """

    def __init__(self, speed_kmh=60, distance_m=100, mode="approach",
                 dt=0.5, decel=6.0, noise=0.0, seed=None, obstacle_speed_kmh=0.0):
        self.mode, self.dt, self.decel, self.noise = mode, dt, decel, noise
        self.obstacle_speed = max(0.0, float(obstacle_speed_kmh))   # 0 = vật cản đứng yên
        self.rng = random.Random(seed)
        self.speed, self.distance = normalize_data(speed_kmh, distance_m)
        self._start = (self.speed, self.distance)
        self.t = 0.0

    def reset(self):
        self.speed, self.distance = self._start
        self.t = 0.0

    def _noisy(self, x):
        return x * (1 + self.rng.gauss(0, self.noise)) if self.noise > 0 else x

    def read(self):
        """Đọc cảm biến hiện tại -> dict đã chuẩn hóa."""
        if self.mode == "random":
            s, d = self.rng.uniform(0, 120), self.rng.uniform(1, 150)
        else:
            s, d = self._noisy(self.speed), self._noisy(self.distance)
        s, d = normalize_data(s, d)
        return {"t": round(self.t, 2), "speed_kmh": s, "distance_m": d,
                "obstacle_speed_kmh": self.obstacle_speed}

    def step(self):
        """Cập nhật trạng thái thật sau dt giây và trả về dữ liệu đọc mới."""
        v = self.speed / 3.6                                   # m/s
        if self.mode == "braking":
            v = max(0.0, v - self.decel * self.dt)
        if self.mode != "constant":
            closing = v - self.obstacle_speed / 3.6            # tốc độ tiến gần (m/s)
            self.distance = max(0.0, self.distance - closing * self.dt)
        self.speed = v * 3.6
        self.t += self.dt
        return self.read()

    def generate_series(self, n=20):
        """Sinh chuỗi n lần đọc (dừng sớm nếu đã va chạm: khoảng cách = 0)."""
        data = [self.read()]
        while len(data) < n and self.distance > 0:
            data.append(self.step())
        return data


# ---------------------------------------------------------------- KIỂM THỬ
def run_tests():
    results = []

    def check(name, cond):
        results.append((name, bool(cond)))

    def raises(*args):
        try:
            normalize_data(*args)
        except ValueError:
            return True
        return False

    # 1. Chuẩn hóa
    check("Giá trị hợp lệ giữ nguyên", normalize_data(60, 100) == (60.0, 100.0))
    check("Ép kiểu chuỗi số + làm tròn", normalize_data("50", "30.456") == (50.0, 30.46))
    check("Kẹp trên (250, 500) -> (200, 200)", normalize_data(250, 500) == (200.0, 200.0))
    check("Kẹp dưới khoảng cách 0 -> 0.5", normalize_data(10, 0) == (10.0, 0.5))
    check("Từ chối tốc độ âm", raises(-5, 10))
    check("Từ chối khoảng cách âm", raises(10, -1))
    check("Từ chối chữ 'abc'", raises("abc", 10))
    check("Từ chối NaN", raises(float("nan"), 10))
    check("Từ chối None", raises(None, 10))

    # 2. Sinh dữ liệu
    d = SensorSimulator(72, 80, "approach", dt=1, seed=0).generate_series(5)
    check("approach: khoảng cách giảm dần", all(a["distance_m"] > b["distance_m"] for a, b in zip(d, d[1:])))
    check("approach: tốc độ không đổi", all(x["speed_kmh"] == 72.0 for x in d))
    check("approach: 80 m, 20 m/s -> sau 1 s còn 60 m", d[1]["distance_m"] == 60.0)

    d = SensorSimulator(60, 100, "braking", dt=1, decel=6, seed=0).generate_series(4)
    check("braking: tốc độ giảm dần", all(a["speed_kmh"] > b["speed_kmh"] for a, b in zip(d, d[1:])))

    d = SensorSimulator(36, 50, "constant", dt=1).generate_series(4)
    check("constant: khoảng cách không đổi", all(x["distance_m"] == 50.0 for x in d))

    d = SensorSimulator(72, 100, "approach", dt=1, obstacle_speed_kmh=36).generate_series(3)
    check("Vật cản chạy 36 km/h: tiến gần 10 m/s -> 100, 90, 80 m",
          [x["distance_m"] for x in d] == [100.0, 90.0, 80.0])
    d = SensorSimulator(36, 50, "approach", dt=1, obstacle_speed_kmh=72).generate_series(3)
    check("Vật cản nhanh hơn xe -> khoảng cách tăng", d[2]["distance_m"] > d[0]["distance_m"])
    check("Dữ liệu đọc có khóa obstacle_speed_kmh", "obstacle_speed_kmh" in d[0])

    d = SensorSimulator(mode="random", seed=3).generate_series(10)
    check("random: dữ liệu luôn trong giới hạn",
          all(SPEED_MIN <= x["speed_kmh"] <= SPEED_MAX and DIST_MIN <= x["distance_m"] <= DIST_MAX for x in d))

    a = SensorSimulator(50, 50, noise=0.05, seed=7).generate_series(5)
    b = SensorSimulator(50, 50, noise=0.05, seed=7).generate_series(5)
    check("Cùng seed -> cùng kết quả", a == b)

    s = SensorSimulator(100, 30, "approach", dt=1)
    check("Dừng khi va chạm (distance = 0)", len(s.generate_series(50)) < 50)

    s = SensorSimulator(60, 100, dt=1); s.step(); s.reset()
    check("reset() trả về trạng thái ban đầu", s.read()["distance_m"] == 100.0)

    return results


if __name__ == "__main__":
    print("=== DEMO: xe 72 km/h, vật cản cách 80 m, nhiễu 2% ===")
    for r in SensorSimulator(72, 80, "approach", noise=0.02, seed=1).generate_series(8):
        print(r)

    print("\n=== KẾT QUẢ KIỂM THỬ ===")
    res = run_tests()
    for name, ok in res:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    print(f"\nTổng: {sum(ok for _, ok in res)}/{len(res)} đạt")
