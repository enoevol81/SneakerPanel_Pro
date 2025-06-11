"""
Converts Grease Pencil objects to Bezier curves.

This operator takes a Grease Pencil object and converts it to a cyclic Bezier curve,
sets the handles to automatic, enables snapping, and adds the curve to the
appropriate collection based on the panel count.
"""
import bpy
from ..utils.collections import add_object_to_panel_collection

class OBJECT_OT_GPToCurve(bpy.types.Operator):
    """Convert Grease Pencil to Bezier curve.
    
    Takes a Grease Pencil object and converts it to a cyclic Bezier curve.
    The curve is automatically set to have automatic handles for smooth editing,
    and is organized into the appropriate panel collection.
    
    This is typically used after drawing an outline with the Grease Pencil tool
    to create a curve that can be further refined before panel generation.
    """
    bl_idname = "object.gp_to_curve"
    bl_label = "GP to Curve"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        """Check if the active object is a Grease Pencil object."""
        obj = context.active_object
        return obj and obj.type == 'GPENCIL'
    
    def execute(self, context):
        # Add undo checkpoint
        bpy.ops.ed.undo_push(message="Convert GP to Curve")
        
        # Get the active Grease Pencil object
        gp_obj = context.active_object
        
        if not gp_obj or gp_obj.type != 'GPENCIL':
            self.report({'ERROR'}, "Active object is not a Grease Pencil object")
            return {'CANCELLED'}
        
        # Convert Grease Pencil to curve
        bpy.ops.object.convert(target='CURVE')
        curve_obj = context.active_object
        
        # Get panel count and name for naming
        panel_count = context.scene.spp_panel_count if hasattr(context.scene, "spp_panel_count") else 1
        panel_name = context.scene.spp_panel_name if hasattr(context.scene, "spp_panel_name") else "Panel"
        
        # Use descriptive name if provided, otherwise use default naming
        if panel_name and panel_name.strip():
            curve_obj.name = f"{panel_name}_Curve_{panel_count}"
        else:
            curve_obj.name = f"Curve_{panel_count}"
        
        # Add to proper collection
        add_object_to_panel_collection(curve_obj, panel_count, panel_name)
        
        # Set curve properties
        curve_obj.data.dimensions = '3D'
        
        # Make the curve cyclic
        for spline in curve_obj.data.splines:
            spline.use_cyclic_u = True
        
        # Set handles to automatic
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.select_all(action='SELECT')
        bpy.ops.curve.handle_type_set(type='AUTOMATIC')
        
        # Enable snapping
        context.scene.tool_settings.use_snap = True
        context.scene.tool_settings.snap_elements = {'FACE'}
        
        # Return to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        self.report({'INFO'}, f"Grease Pencil converted to curve: {curve_obj.name}")
        return {'FINISHED'}

# Registration
classes = [OBJECT_OT_GPToCurve]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
