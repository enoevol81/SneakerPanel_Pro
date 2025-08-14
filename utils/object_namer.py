import bpy

# -------------------------------------------------------------------------
# Collections Auto Naming Helper Functions
# ------------------------------------------------------------------------
def get_unique_name(base_name, panel_number):
    return f"{base_name}_{panel_number}"


def rename_object(obj, base_name, panel_number):
    new_name = get_unique_name(base_name, panel_number)
    obj.name = new_name
    if obj.data:
        obj.data.name = new_name
    return new_name
