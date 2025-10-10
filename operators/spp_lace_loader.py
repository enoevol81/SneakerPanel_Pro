"""
Asset loader utility for SPP Lace Generator
Loads geometry node groups and materials from the asset blend file
"""

import bpy
from pathlib import Path


def get_addon_directory():
    """Get the addon directory path"""
    return Path(__file__).parent.parent


def load_lace_assets():
    """
    Load lace geometry node groups and materials from the asset file.
    This is idempotent - safe to call multiple times.
    """
    addon_dir = get_addon_directory()
    asset_path = addon_dir / "assets" / "spp_lace_assets.blend"

    if not asset_path.exists():
        print(f"ERROR: Asset file not found at {asset_path}")
        print("Please ensure spp_lace_assets.blend exists in the assets folder")
        return False

    print(f"Loading lace assets from: {asset_path}")

    # Define the assets to load
    node_groups_to_load = [
        "spp_lace_round",
        "spp_lace_oval",
        "spp_lace_flat",
        "spp_lace_custom",
    ]

    materials_to_load = ["spp_lace_material"]

    # Load node groups
    try:
        with bpy.data.libraries.load(str(asset_path), link=False) as (
            data_from,
            data_to,
        ):
            print(f"Available node groups in asset file: {data_from.node_groups}")
            print(f"Available materials in asset file: {data_from.materials}")

            # Check which node groups need to be loaded
            for node_group_name in node_groups_to_load:
                if node_group_name not in bpy.data.node_groups:
                    if node_group_name in data_from.node_groups:
                        data_to.node_groups.append(node_group_name)
                        print(f"Queuing node group for loading: {node_group_name}")
                    else:
                        print(
                            f"WARNING: Node group '{node_group_name}' not found in asset file"
                        )

            # Check which materials need to be loaded
            for material_name in materials_to_load:
                if material_name not in bpy.data.materials:
                    if material_name in data_from.materials:
                        data_to.materials.append(material_name)
                        print(f"Queuing material for loading: {material_name}")
                    else:
                        print(
                            f"WARNING: Material '{material_name}' not found in asset file"
                        )
    except Exception as e:
        print(f"ERROR loading assets: {e}")
        return False

    # Set fake user on loaded assets to ensure persistence
    loaded_groups = []
    for node_group_name in node_groups_to_load:
        if node_group_name in bpy.data.node_groups:
            bpy.data.node_groups[node_group_name].use_fake_user = True
            loaded_groups.append(node_group_name)

    loaded_materials = []
    for material_name in materials_to_load:
        if material_name in bpy.data.materials:
            bpy.data.materials[material_name].use_fake_user = True
            loaded_materials.append(material_name)

    print(f"Successfully loaded node groups: {loaded_groups}")
    print(f"Successfully loaded materials: {loaded_materials}")
    return True


def ensure_lace_assets():
    """
    Ensure lace assets are loaded. Call this before using any lace functionality.
    Returns True if assets are available, False otherwise.
    """
    # Check if assets are already loaded
    required_groups = [
        "spp_lace_round",
        "spp_lace_oval",
        "spp_lace_flat",
        "spp_lace_custom",
    ]
    required_materials = ["spp_lace_material"]

    all_loaded = True
    for group_name in required_groups:
        if group_name not in bpy.data.node_groups:
            all_loaded = False
            break

    if all_loaded:
        for mat_name in required_materials:
            if mat_name not in bpy.data.materials:
                all_loaded = False
                break

    # If not all loaded, try to load them
    if not all_loaded:
        return load_lace_assets()

    return True
