import bpy

# This function should be defined globally in SneakerPanel_Pro/ui/bezier_panel.py
# before the register() function.
def live_update_active_surface_resolution(scene_self, context):
    """
    This function is called when spp_resolution_u or spp_resolution_v changes in the UI.
    'scene_self' will be bpy.context.scene.
    It directly modifies the properties of the active object's curve/surface data.
    """
    # print("--- live_update_active_surface_resolution CALLED ---") # DEBUG (keep commented out unless debugging)
    
    new_resolution_u = scene_self.spp_resolution_u
    new_resolution_v = scene_self.spp_resolution_v
    # print(f"Attempting to set: U={new_resolution_u}, V={new_resolution_v}") # DEBUG
    
    active_obj = context.active_object
    
    if not active_obj:
        # print("DEBUG: No active object found.") # DEBUG
        return

    # print(f"DEBUG: Active object is '{active_obj.name}', type is '{active_obj.type}'") # DEBUG

    if active_obj and \
       (active_obj.type == 'CURVE' or active_obj.type == 'SURFACE') and \
       hasattr(active_obj.data, 'resolution_u'):
        
        curve_data = active_obj.data
        # print(f"DEBUG: Modifying data for '{curve_data.name}' (object: '{active_obj.name}')") # DEBUG
        
        curve_data.resolution_u = new_resolution_u
        curve_data.resolution_v = new_resolution_v
        
        # print(f"DEBUG: Set {curve_data.name}.resolution_u to {curve_data.resolution_u}") # DEBUG
        # print(f"DEBUG: Set {curve_data.name}.resolution_v to {curve_data.resolution_v}") # DEBUG
        
        curve_data.update()
        # print("DEBUG: curve_data.update() called.") # DEBUG
    # else:
        # print(f"DEBUG: Active object '{active_obj.name}' (type: {active_obj.type}) "
        #       "is not a suitable CURVE/SURFACE with resolution properties.") # DEBUG


class OBJECT_PT_BezierToPanel(bpy.types.Panel):
    bl_label = "Bezier to Panel"
    bl_idname = "OBJECT_PT_bezier_to_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene # Get scene for easy access

        self.draw_grease_pencil_section(layout, scene)
        self.draw_conversion_section(layout, scene) # Pass scene to methods

    def draw_grease_pencil_section(self, layout, scene): # Added scene parameter
        box = layout.box()
        box.label(text="1. Draw Panel Using Grease Pencil", icon="GREASEPENCIL")

        box.operator("object.add_gp_draw", text="Add Grease Pencil Item", icon='OUTLINER_OB_GREASEPENCIL')
        box.prop(scene, "spp_use_stabilizer", text="Use Stabilizer")
        if scene.spp_use_stabilizer:
            box.prop(scene, "spp_stabilizer_radius", text="Stabilizer Radius")
            box.prop(scene, "spp_stabilizer_factor", text="Stabilizer Factor")

    def draw_conversion_section(self, layout, scene): # Added scene parameter
        box = layout.box()
        box.label(text="2.Grease Pencil to Bezier Curve", icon='OUTLINER_OB_CURVE')
        box.operator("object.gp_to_curve", text="Create Curve", icon='IPO_BEZIER')
        
        box.label(text="-- 2a. Optional - Decimate Curve --")
        box.prop(scene, "spp_decimate_ratio", text="Ratio")
        box.operator("object.decimate_curve", text="Decimate Curve", icon='MOD_DECIM')
        
        box = layout.box()
        box.label(text="3. Convert Bezier to Surface - Edit", icon='OUTLINER_OB_SURFACE')
        
        # Operator properties for the Bezier to Surface conversion
        # These are passed to the operator when it's invoked.
        op_bs = box.operator("spp.convert_bezier_to_surface", text="Convert Bezier to Surface", icon='SURFACE_DATA')
        op_bs.center = scene.spp_bezier_center 
        op_bs.Resolution_U = scene.spp_resolution_u # Operator uses these values at creation time
        op_bs.Resolution_V = scene.spp_resolution_v # Operator uses these values at creation time
        
        # --- Live Surface Editing Section ---
        # Use a sub-box for the live editing controls
        live_edit_box = box.box() 
        live_edit_box.label(text="Live Surface Editing:")
        
        # Add the checkbox to show/hide resolution controls
        live_edit_box.prop(scene, "spp_show_surface_resolution_controls", text="Advanced: Edit Resolution")

        # Conditionally draw the resolution controls
        if scene.spp_show_surface_resolution_controls:
            # Indent these controls slightly or put in another sub-box for clarity
            res_controls_box = live_edit_box.box() 
            row = res_controls_box.row(align=True)
            row.prop(scene, "spp_resolution_u", text="Resolution U")
            row.prop(scene, "spp_resolution_v", text="Resolution V")
        
        # Surface to Mesh conversion section
        box = layout.box()
        box.label(text="4. Convert Surface to Mesh", icon='MESH_DATA')
        
        box.prop(scene, "spp_preserve_surface", text="Preserve Surface")
        box.prop(scene, "spp_shade_smooth", text="Smooth Shading")
        
        box.operator("object.convert", text="Convert Surface to Mesh", icon='MESH_GRID').target = 'MESH'


# Registration
classes = [OBJECT_PT_BezierToPanel]

def register():
    # Register scene properties
    bpy.types.Scene.spp_bezier_center = bpy.props.BoolProperty(
        name="Center",
        description="Consider center points when creating the surface",
        default=False
    )
    
    bpy.types.Scene.spp_resolution_u = bpy.props.IntProperty(
        name="Resolution U",
        description="Live-edit surface resolution in the U direction. Also used as initial U-resolution for new surfaces.",
        default=4,
        min=1,
        soft_max=64,
        update=live_update_active_surface_resolution
    )
    
    bpy.types.Scene.spp_resolution_v = bpy.props.IntProperty(
        name="Resolution V",
        description="Live-edit surface resolution in the V direction. Also used as initial V-resolution for new surfaces.",
        default=4,
        min=1,
        soft_max=64,
        update=live_update_active_surface_resolution
    )
    
    # NEW BoolProperty to control visibility of resolution U/V controls
    bpy.types.Scene.spp_show_surface_resolution_controls = bpy.props.BoolProperty(
        name="Edit Surface Resolution", # This name is for the property itself, UI text is set in prop()
        description="Show controls to edit the resolution of the active NURBS surface",
        default=False 
    )
    
    bpy.types.Scene.spp_preserve_surface = bpy.props.BoolProperty(
        name="Preserve Surface",
        description="Keep the original NURBS surface after conversion",
        default=True
    )
    
    bpy.types.Scene.spp_shade_smooth = bpy.props.BoolProperty(
        name="Smooth Shading",
        description="Apply smooth shading to the resulting mesh",
        default=True
    )
    
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    # Unregister scene properties
    del bpy.types.Scene.spp_bezier_center
    del bpy.types.Scene.spp_resolution_u
    del bpy.types.Scene.spp_resolution_v
    del bpy.types.Scene.spp_show_surface_resolution_controls # Unregister the new property
    del bpy.types.Scene.spp_preserve_surface
    del bpy.types.Scene.spp_shade_smooth
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()