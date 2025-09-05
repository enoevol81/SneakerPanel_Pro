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
    icons_dir = os.path.join(os.path.dirname(__file__), "..", "operators", "icons")

    # Load additional icons
    ui_icons = [
        "2d.png",
        "3d.png",
        "auto_uv.png",
        "laces.png",
        "logo.png",
        "spp_tile_32.png",
        "spp_tile_64.png",
        "tools.png",
        "mesh.png",
        "ref_image.png",
        "profile.png",
        "edit.png"
        


    ]

    for icon_name in ui_icons:
        icon_path = os.path.join(icons_dir, icon_name)
        if os.path.exists(icon_path):
            pcoll.load(icon_name.split('.')[0], icon_path, "IMAGE")
        else:
            print(f"Warning: Icon not found at {icon_path}")

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
