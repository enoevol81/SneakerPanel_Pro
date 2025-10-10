#!/usr/bin/env python3
"""
Test script to verify the 3-day trial functionality works correctly.
Run this from Blender's Python console or as a script.
"""

import os
import sys
import tempfile

# Add the addon path to sys.path for testing
addon_path = r"c:\Dev\sneaker_panel_pro"
if addon_path not in sys.path:
    sys.path.insert(0, addon_path)

# Mock bpy.utils.user_resource for testing
class MockBpy:
    class utils:
        @staticmethod
        def user_resource(resource_type):
            return tempfile.gettempdir()

# Replace bpy with mock for testing
sys.modules['bpy'] = MockBpy()
sys.modules['bpy.utils'] = MockBpy.utils

# Now import and test the license manager
from utils import license_manager

def test_trial_functionality():
    """Test the 3-day trial system."""
    print("🧪 Testing Sneaker Panel Pro Trial Functionality")
    print("=" * 50)
    
    # Clean up any existing trial files
    trial_file = license_manager.TRIAL_FILE
    if os.path.exists(trial_file):
        os.remove(trial_file)
        print(f"🗑️ Cleaned up existing trial file: {trial_file}")
    
    # Test 1: First time check (should create trial and return True)
    print("\n1️⃣ Testing first-time trial activation...")
    trial_ok, message = license_manager.check_trial()
    print(f"   Result: {trial_ok}")
    print(f"   Message: {message}")
    assert trial_ok == True, "First trial check should return True"
    assert "3 days remaining" in message, "Should show 3 days remaining"
    
    # Test 2: Second check (should still be valid)
    print("\n2️⃣ Testing subsequent trial check...")
    trial_ok, message = license_manager.check_trial()
    print(f"   Result: {trial_ok}")
    print(f"   Message: {message}")
    assert trial_ok == True, "Second trial check should still return True"
    
    # Test 3: Check enforce_license function
    print("\n3️⃣ Testing enforce_license function...")
    license_ok = license_manager.enforce_license()
    print(f"   Result: {license_ok}")
    assert license_ok == True, "enforce_license should return True during trial"
    
    # Test 4: Check trial file was created
    print("\n4️⃣ Verifying trial file creation...")
    assert os.path.exists(trial_file), f"Trial file should exist at {trial_file}"
    print(f"   ✅ Trial file created: {trial_file}")
    
    # Test 5: Check cached license status
    print("\n5️⃣ Testing cached license status...")
    cached = license_manager.load_local_license()
    print(f"   Cached status: {cached}")
    assert "trial" in cached.get("status", "").lower(), "Should have trial status cached"
    
    print("\n" + "=" * 50)
    print("✅ ALL TESTS PASSED! Trial functionality is working correctly.")
    print(f"📁 Trial file location: {trial_file}")
    
    # Show trial file contents
    try:
        import json
        with open(trial_file, 'r') as f:
            trial_data = json.load(f)
        print(f"📄 Trial file contents: {trial_data}")
    except Exception as e:
        print(f"⚠️ Could not read trial file: {e}")

if __name__ == "__main__":
    test_trial_functionality()
