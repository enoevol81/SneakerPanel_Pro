def update_active_surface_resolution(scene_self, context):
    try:
        new_resolution_u = getattr(scene_self, "spp_resolution_u", 12)
        new_resolution_v = getattr(scene_self, "spp_resolution_v", 12)

        # Get the active object
        active_obj = context.active_object
        if not active_obj:
            return

        # Check if the active object is a curve or surface with resolution properties
        if active_obj.type in {"CURVE", "SURFACE"} and hasattr(
            active_obj.data, "resolution_u"
        ):
            # Update the resolution
            curve_data = active_obj.data
            curve_data.resolution_u = new_resolution_u
            curve_data.resolution_v = new_resolution_v
            curve_data.update()
    except Exception as e:
        print(f"Error updating surface resolution: {str(e)}")


# --- Registration ---
def register():
    pass


def unregister():
    pass


if __name__ == "__main__":
    register()
