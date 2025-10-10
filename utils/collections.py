import bpy


def get_sneaker_panels_collection():
    # Check if collection already exists
    if "Sneaker Panels" in bpy.data.collections:
        main_collection = bpy.data.collections["Sneaker Panels"]
        # Ensure it has the correct color
        main_collection.color_tag = "COLOR_05"
        return main_collection

    # Create new collection
    main_collection = bpy.data.collections.new("Sneaker Panels")
    main_collection.color_tag = "COLOR_05"
    bpy.context.scene.collection.children.link(main_collection)
    return main_collection


def _get_panel_color_tag(panel_number):
    # Available colors: default (NONE) + COLOR_01 through COLOR_08 = 9 total
    color_options = [
        "NONE",  # Default/white
        "COLOR_01",  # Red
        "COLOR_02",  # Orange
        "COLOR_03",  # Yellow
        "COLOR_04",  # Green
        "COLOR_06",  # Blue (skipping COLOR_05 as it's used for main collection)
        "COLOR_07",  # Purple
        "COLOR_08",  # Pink
        "COLOR_01",  # Extra red to make 9 total
    ]

    # Use modulo to cycle through colors for panels beyond 9
    color_index = (panel_number - 1) % len(color_options)
    return color_options[color_index]


def get_panel_collection(panel_number, panel_name=None):
    # Get main collection
    main_collection = get_sneaker_panels_collection()

    # Determine collection name
    if panel_name and panel_name.strip():
        # Use descriptive name with number suffix for uniqueness
        panel_collection_name = f"{panel_name}_{panel_number}"
    else:
        # Fallback to just number if no name provided
        panel_collection_name = f"Panel_{panel_number}"

    # Check if panel collection already exists
    if panel_collection_name in bpy.data.collections:
        panel_collection = bpy.data.collections[panel_collection_name]
        # Ensure it has a color assigned
        if not panel_collection.color_tag or panel_collection.color_tag == "COLOR_05":
            panel_collection.color_tag = _get_panel_color_tag(panel_number)
        return panel_collection

    # Create new panel collection
    panel_collection = bpy.data.collections.new(panel_collection_name)
    panel_collection.color_tag = _get_panel_color_tag(panel_number)
    main_collection.children.link(panel_collection)
    return panel_collection


def add_object_to_panel_collection(obj, panel_number, panel_name=None):
    # Get panel collection
    panel_collection = get_panel_collection(panel_number, panel_name)

    # Remove from current collections
    for col in obj.users_collection:
        col.objects.unlink(obj)

    # Add to panel collection
    panel_collection.objects.link(obj)
