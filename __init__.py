# ruff: noqa: E402

bl_info = {
    "name": "Sneaker Panel Pro",
    "author": "Enoevol Creative Solutions",
    "version": (1, 0, 0),
    "blender": (4, 5, 0),
    "location": "Sidebar > Sneaker Panel Pro",
    "description": "Professional Footwear Design Toolkit for Blender",
    "category": "Object",
    "warning": "Requires 'Grease Pencil To Curves', and 'Loop Tools' add-ons (enable in Preferences > Add-ons)",
}

import bpy

from . import prefs
from . import state
from . import operators, properties, ui
from .utils import icons
from .utils import audit_tooltips as _audit_tooltips
from .utils import license_manager as _license_manager

# List of all classes for registration
classes = []


def register():
    """Register all addon components."""
    try:
        # ------------------------------------------------------------------
        # 🧠 License Enforcement - CHECK FIRST
        # ------------------------------------------------------------------
        license_ok = _license_manager.is_license_valid()

        # --- Core module registration ---
        prefs.register()
        state.register()
        properties.register()
        operators.register()

        # Only register UI if license is valid
        if license_ok:
            ui.register()
            print("✅ Sneaker Panel Pro: License verified - Full UI enabled")
        else:
            print("⚠ Sneaker Panel Pro: License not verified - UI panels disabled")

            # Show warning popup for unlicensed users
            def warn_popup(self, context):
                self.layout.label(text="Sneaker Panel Pro license not verified.")
                self.layout.label(
                    text="Please enter your license key in Preferences → Add-ons → Sneaker Panel Pro."
                )

            try:
                bpy.context.window_manager.popup_menu(
                    warn_popup, title="License Required", icon="ERROR"
                )
            except Exception as e:
                print(f"⚠ Could not show license popup: {e}")

        # --- Custom assets and utilities ---
        icons.load_icons()
        _audit_tooltips.register()

        # Pre-load lace assets (optional)
        try:
            from .operators.spp_lace_loader import load_lace_assets

            load_lace_assets()
        except Exception as e:
            print(f"Note: Lace assets will be loaded on first use: {e}")

        # --- Register any local classes ---
        for cls in classes:
            bpy.utils.register_class(cls)

        print("✅ Sneaker Panel Pro: Successfully registered addon")

    except Exception as e:
        print(f"❌ Sneaker Panel Pro: Error during registration: {e}")
        raise


def unregister():
    """Unregister all addon components."""
    try:
        for cls in reversed(classes):
            bpy.utils.unregister_class(cls)

        # --- Utilities and modules ---
        icons.unload_icons()
        _audit_tooltips.unregister()
        ui.unregister()
        operators.unregister()
        properties.unregister()
        state.unregister()
        prefs.unregister()

        print("Sneaker Panel Pro: Successfully unregistered addon")
    except Exception as e:
        print(f"Sneaker Panel Pro: Error during unregistration: {e}")
        raise


# Allow running this script directly from Blender's text editor
if __name__ == "__main__":
    register()
