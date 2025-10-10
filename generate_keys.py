import csv
import sys
import hashlib

OFFLINE_SALT = "enoevol2025"  # must match utils/license_manager.py


def generate_offline_key(email: str) -> str:
    digest = (
        hashlib.sha256(f"{email}-{OFFLINE_SALT}".encode("utf-8"))
        .hexdigest()[:12]
        .upper()
    )
    return f"SPP-{digest}"


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_keys.py buyer@example.com [issued_keys.csv]")
        return
    email = sys.argv[1].strip()
    csv_path = sys.argv[2] if len(sys.argv) > 2 else "issued_keys.csv"
    key = generate_offline_key(email)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([email, key])
    print(f"Generated key for {email}: {key}\nSaved to {csv_path}")


if __name__ == "__main__":
    main()
