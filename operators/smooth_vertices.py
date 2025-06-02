import bpy
from ..utils.panel_utils import apply_surface_snap

class OBJECT_OT_SmoothVertices(bpy.types.Operator):
    bl_idname = "object.smooth_vertices"
    bl_label = "Apply Smoothing"

    def execute(self, context):
        # Add undo checkpoint
        bpy.ops.ed.undo_push(message="Smooth Vertices")
        
        if bpy.context.object.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        bpy.ops.mesh.select_all(action='SELECT')
        
        # Apply smoothing
        smooth_factor = context.scene.spp_smooth_factor
        bpy.ops.mesh.vertices_smooth(factor=smooth_factor)
        
        # Ensure vertices stay on surface
        apply_surface_snap()

        bpy.ops.object.mode_set(mode='OBJECT')
        self.report({'INFO'}, f"Vertices smoothed with factor {smooth_factor} and snapped to surface.")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(OBJECT_OT_SmoothVertices)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_SmoothVertices)
