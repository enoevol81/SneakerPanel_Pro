import bpy

def update_active_surface_resolution(scene_self, context):
    """
    Updates resolution of active NURBS surface when UI values change.
    Called by UI property update callbacks.
    """
    new_resolution_u = scene_self.spp_resolution_u
    new_resolution_v = scene_self.spp_resolution_v
    
    active_obj = context.active_object
    if not active_obj:
        return

    if active_obj and \
       (active_obj.type == 'CURVE' or active_obj.type == 'SURFACE') and \
       hasattr(active_obj.data, 'resolution_u'):
        curve_data = active_obj.data
        curve_data.resolution_u = new_resolution_u
        curve_data.resolution_v = new_resolution_v
        curve_data.update()

# --- Registration ---
def register():
    pass

def unregister():
    pass

if __name__ == "__main__":
    register()
