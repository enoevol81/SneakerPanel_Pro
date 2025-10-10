"""
Simple test to verify trial functionality works correctly.
This simulates what happens when the addon loads for the first time.
"""

import os
import json
import time
import tempfile

# Simulate the trial file path (using temp directory for testing)
TRIAL_DAYS = 3
TRIAL_FILE = os.path.join(tempfile.gettempdir(), "spp_trial_test.json")
LICENSE_FILE = os.path.join(tempfile.gettempdir(), "spp_license_test.json")

def save_local_license(data):
    """Cache license info to disk."""
    with open(LICENSE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

def load_local_license():
    """Load cached license info."""
    if os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def is_license_valid():
    """Check cached license status."""
    data = load_local_license()
    if not data:
        return False
    status = data.get("status", "").lower()
    return "verified" in status

def check_trial():
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

def enforce_license():
    """Verify at startup and return True if license OR trial is valid."""
    if is_license_valid():
        print("✅ Sneaker Panel Pro: License verified and active.")
        return True

    trial_ok, trial_msg = check_trial()
    if trial_ok:
        print(f"🕒 Sneaker Panel Pro: {trial_msg}")
        return True

    print("⚠ Sneaker Panel Pro: License not verified and trial expired.")
    return False

def test_trial_flow():
    """Test the complete trial flow."""
    print("🧪 Testing Sneaker Panel Pro Trial Flow")
    print("=" * 50)
    
    # Clean up any existing files
    for file_path in [TRIAL_FILE, LICENSE_FILE]:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ Cleaned up: {file_path}")
    
    print("\n1️⃣ First addon load (should start trial)...")
    result = enforce_license()
    print(f"   Result: {result}")
    assert result == True, "First load should activate trial"
    
    print("\n2️⃣ Second addon load (should continue trial)...")
    result = enforce_license()
    print(f"   Result: {result}")
    assert result == True, "Second load should continue trial"
    
    print("\n3️⃣ Check cached license status...")
    cached = load_local_license()
    print(f"   Cached status: {cached}")
    assert "trial" in cached.get("status", "").lower(), "Should have trial status"
    
    print("\n4️⃣ Verify trial file exists...")
    assert os.path.exists(TRIAL_FILE), f"Trial file should exist: {TRIAL_FILE}"
    print(f"   ✅ Trial file exists: {TRIAL_FILE}")
    
    # Show file contents
    with open(TRIAL_FILE, 'r') as f:
        trial_data = json.load(f)
    print(f"   📄 Trial data: {trial_data}")
    
    print("\n" + "=" * 50)
    print("✅ ALL TESTS PASSED! Trial will activate on first addon load.")
    print(f"📁 Test files created in: {tempfile.gettempdir()}")
    
    # Cleanup test files
    for file_path in [TRIAL_FILE, LICENSE_FILE]:
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    test_trial_flow()
