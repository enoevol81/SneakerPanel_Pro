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

    # Load the UV checker icon
    uv_checker_path = os.path.join(icons_dir, "uv_checker_32.png")
    if os.path.exists(uv_checker_path):
        pcoll.load("uv_checker", uv_checker_path, "IMAGE")
    else:
        print(f"Warning: Icon not found at {uv_checker_path}")

    # Load the Lime Logo icon
    spp_lime_32_path = os.path.join(icons_dir, "spp_lime_32.png")
    if os.path.exists(spp_lime_32_path):
        pcoll.load("spp_lime_32", spp_lime_32_path, "IMAGE")
    else:
        print(f"Warning: Icon not found at {spp_lime_32_path}")

    # Load the UV checker icon
    uv_workflow = os.path.join(icons_dir, "UI_Icons-01.png")
    if os.path.exists(uv_workflow):
        pcoll.load("uv_workflow", uv_workflow, "IMAGE")
    else:
        print(f"Warning: Icon not found at {uv_workflow}")

    # Load additional icons
    for filename in os.listdir(icons_dir):
        if filename.endswith(".png"):
            icon_name = filename.split('.')[0]
            icon_path = os.path.join(icons_dir, filename)
            if os.path.exists(icon_path):
                pcoll.load(icon_name, icon_path, "IMAGE")
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
