
import sys
import argparse
import subprocess
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent

GUI_DIR = ROOT_DIR / "gui"
DASHBOARD_FILE = GUI_DIR / "dashboard.py"

TEST_DIR = ROOT_DIR / "test"
TEST_FILE = TEST_DIR / "test_scenarios.py"


# Them thu muc goc vao Python path
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def run_dashboard():
    """Khoi dong giao dien mo phong bang Streamlit."""

    print("=" * 60)
    print("          AI COLLISION WARNING SYSTEM")
    print("=" * 60)

    if not DASHBOARD_FILE.exists():
        print("[LOI] Khong tim thay file gui/dashboard.py")
        return 1

    print("[INFO] Dang khoi dong giao dien...")
    print("[INFO] Dia chi: http://localhost:8501")
    print("[INFO] Nhan Ctrl + C de dung he thong.")
    print("-" * 60)

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(DASHBOARD_FILE)
    ]

    try:
        return subprocess.call(command, cwd=ROOT_DIR)

    except KeyboardInterrupt:
        print("\n[INFO] Da dung he thong.")
        return 0

    except Exception as error:
        print(f"[LOI] Khong the khoi dong giao dien: {error}")
        return 1

def run_tests():
    """Chay cac kiem thu trong thu muc test."""

    print("=" * 60)
    print("             KIEM THU HE THONG")
    print("=" * 60)

    if not TEST_DIR.exists():
        print("[LOI] Khong tim thay thu muc test.")
        return 1

    if not TEST_FILE.exists():
        print("[LOI] Khong tim thay test_scenarios.py.")
        return 1

    print("[INFO] Dang chay test_scenarios.py...")
    print("-" * 60)

    command = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "test",
        "-p",
        "test_*.py",
        "-v"
    ]

    try:
        result = subprocess.call(command, cwd=ROOT_DIR)

        print("\n" + "=" * 60)

        if result == 0:
            print("[THANH CONG] Kiem thu hoan tat.")
        else:
            print("[THAT BAI] Kiem tra lai cac loi trong test.")

        print("=" * 60)

        return result

    except Exception as error:
        print(f"[LOI] Khong the chay kiem thu: {error}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="He thong mo phong canh bao nguy co va cham"
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Chay kiem thu tinh huong mo phong"
    )

    args = parser.parse_args()

    if args.test:
        return run_tests()

    return run_dashboard()


if __name__ == "__main__":
    sys.exit(main())
