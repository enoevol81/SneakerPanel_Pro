import os

import bpy
import bpy.utils.previews

# Global variable to store icon previews
preview_collections = {}


# -------------------------------------------------------------------------
# Icons
# ------------------------------------------------------------------------
def load_icons():
    """Load custom icons for the addon."""
    # Create a new preview collection
    pcoll = bpy.utils.previews.new()

    # Use relative path for icons directory
    icons_dir = os.path.join(os.path.dirname(__file__), "..", "ui", "icons")

    # Auto-discover and load all PNG icons in the directory
    if os.path.exists(icons_dir):
        try:
            # Get all PNG files in the icons directory
            png_files = [f for f in os.listdir(icons_dir) if f.lower().endswith(".png")]

            if png_files:
                print(f"Loading {len(png_files)} icon(s) from {icons_dir}")

                for icon_file in png_files:
                    icon_path = os.path.join(icons_dir, icon_file)
                    icon_name = os.path.splitext(icon_file)[0]  # Remove .png extension

                    try:
                        pcoll.load(icon_name, icon_path, "IMAGE")
                        print(f"  ✓ Loaded icon: {icon_name}")
                    except Exception as e:
                        print(f"  ✗ Failed to load {icon_file}: {e}")
            else:
                print(f"No PNG icons found in {icons_dir}")

        except Exception as e:
            print(f"Error accessing icons directory {icons_dir}: {e}")
    else:
        print(f"Icons directory not found: {icons_dir}")

    # Store the preview collection
    preview_collections["main"] = pcoll


def get_icon(icon_name):
    pcoll = preview_collections.get("main")
    if pcoll and icon_name in pcoll:
        return pcoll[icon_name].icon_id
    return 0


def unload_icons():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
