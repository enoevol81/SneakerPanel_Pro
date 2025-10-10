import bpy
import json
import hashlib
import requests
import os
import time

# -------------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------------
PRODUCT_NAME = "Sneaker Panel Pro"
PRODUCT_PERMALINK = "sneaker-panel-pro"  # Gumroad product permalink
OFFLINE_SALT = "enoevol2025"  # Used for generating offline keys

TRIAL_DAYS = 3
TRIAL_FILE = os.path.join(bpy.utils.user_resource("CONFIG"), "spp_trial.json")


# -------------------------------------------------------------------------
# LICENSE HANDLING
# -------------------------------------------------------------------------
def get_prefs():
    """Get the add-on preferences."""
    return bpy.context.preferences.addons[__package__].preferences


def generate_offline_key(email: str) -> str:
    """Create a simple offline checksum key based on the buyer's email."""
    data = f"{email}-{OFFLINE_SALT}".encode("utf-8")
    digest = hashlib.sha256(data).hexdigest()[:12].upper()
    return f"SPP-{digest}"


def verify_offline_key(key: str, email: str) -> bool:
    """Validate a locally generated key."""
    expected = generate_offline_key(email)
    return key.strip().upper() == expected


def verify_gumroad_license(license_key: str) -> (bool, str):
    """Validate a Gumroad license key via the Gumroad API."""
    url = "https://api.gumroad.com/v2/licenses/verify"
    payload = {"product_permalink": PRODUCT_PERMALINK, "license_key": license_key}

    try:
        response = requests.post(url, data=payload, timeout=10)
        data = response.json()
        purchase = data.get("purchase", {})

        if purchase.get("refunded") or purchase.get("chargebacked"):
            return False, "License refunded or revoked."
        if data.get("success"):
            return True, f"License verified for {purchase.get('email', 'unknown')}"
        return False, data.get("message", "Invalid or expired license key.")
    except Exception as e:
        return False, f"Network error: {e}"


def local_license_path() -> str:
    """Return path to local license cache file."""
    return os.path.join(bpy.utils.user_resource("CONFIG"), "spp_license.json")


def save_local_license(data: dict):
    """Cache license info to disk."""
    path = local_license_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def load_local_license() -> dict:
    """Load cached license info."""
    path = local_license_path()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def clear_local_license():
    """Delete cached license data."""
    path = local_license_path()
    if os.path.exists(path):
        os.remove(path)
        print("🗑️ License data cleared.")
    if os.path.exists(TRIAL_FILE):
        os.remove(TRIAL_FILE)
        print("🗑️ Trial data cleared.")


def validate_license(license_key: str, email: str = None):
    """Try online Gumroad validation, fallback to offline check."""
    # 1️⃣ Try Gumroad validation
    success, message = verify_gumroad_license(license_key)
    if success:
        save_local_license({"license": license_key, "status": "verified"})
        return True, message

    # 2️⃣ Fallback: offline validation (for Blender Market / manual keys)
    if email and verify_offline_key(license_key, email):
        save_local_license({"license": license_key, "status": "offline-verified"})
        return True, "Offline license accepted."
    else:
        return False, message


# -------------------------------------------------------------------------
# TRIAL MODE
# -------------------------------------------------------------------------
def check_trial() -> (bool, str):
    """Simple 3-day trial system."""
    now = int(time.time())
    if not os.path.exists(TRIAL_FILE):
        with open(TRIAL_FILE, "w") as f:
            json.dump({"first_use": now}, f)
        msg = f"Trial active ({TRIAL_DAYS} days remaining)"
        save_local_license({"status": msg})
        return True, msg

    try:
        with open(TRIAL_FILE, "r") as f:
            data = json.load(f)

        elapsed_days = (now - data["first_use"]) / 86400
        remaining = max(0, TRIAL_DAYS - int(elapsed_days))

        if remaining > 0:
            msg = f"Trial active ({remaining} days remaining)"
            save_local_license({"status": msg})
            return True, msg
        else:
            save_local_license({"status": "trial expired"})
            return False, "Trial expired"
    except Exception as e:
        return False, f"Trial check failed: {e}"


# -------------------------------------------------------------------------
# LICENSE ENFORCEMENT
# -------------------------------------------------------------------------
def is_license_valid() -> bool:
    """Check cached license status at startup."""
    data = load_local_license()
    if not data:
        return False
    status = data.get("status", "").lower()
    return "verified" in status


def enforce_license():
    """Verify at startup and disable UI if license invalid or trial expired."""
    if is_license_valid():
        print("✅ Sneaker Panel Pro: License verified and active.")
        return True

    trial_ok, trial_msg = check_trial()
    if trial_ok:
        print(f"🕒 Sneaker Panel Pro: {trial_msg}")
        return True

    print("⚠ Sneaker Panel Pro: License not verified and trial expired.")
    return False


def enable_ui_after_license():
    """Re-enable UI panels after successful license verification."""
    try:
        from .. import ui

        ui.register()
        print("✅ Sneaker Panel Pro: UI panels enabled after license verification.")
        return True
    except Exception as e:
        print(f"❌ Error enabling UI after license verification: {e}")
        return False
