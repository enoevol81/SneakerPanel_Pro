"""
Vertex reduction operator for SneakerPanel Pro.

This module provides an operator to reduce the vertex count of a mesh
while maintaining its overall shape. It uses a combination of limited dissolve
and Loop Tools Space operator to achieve clean results, followed by surface
snapping to ensure the reduced mesh still conforms to the target surface.
"""
import bpy
from ..utils.panel_utils import apply_surface_snap

class OBJECT_OT_ReduceVerts(bpy.types.Operator):
    """Reduce mesh vertices while maintaining shape.
    
    This operator reduces the number of vertices in a mesh using limited dissolve
    with progressively increasing angle limits until the target reduction is achieved.
    It then applies Loop Tools Space operator to distribute vertices evenly and
    finally applies surface snapping to maintain conformity with the target surface.
    
    Note:
        Requires the Loop Tools addon to be enabled for best results.
    """
    bl_idname = "object.reduce_verts"
    bl_label = "Reduce Verts"
    bl_description = "Reduce mesh vertices while maintaining shape"
    bl_options = {'REGISTER', 'UNDO'}

    factor: bpy.props.FloatProperty(
        name="Reduction Factor",
        description="Factor to reduce vertices by (0.0 to 1.0)",
        min=0.0,
        max=1.0,
        default=0.2
    )

    @classmethod
    def poll(cls, context):
        """Check if the operator can be executed.
        
        Args:
            context: Blender context
            
        Returns:
            bool: True if active object is a mesh
        """
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        # Add undo checkpoint
        bpy.ops.ed.undo_push(message="Reduce Vertices")
        
        try:
            obj = context.active_object
            if not obj or obj.type != 'MESH':
                self.report({'WARNING'}, "Active object is not a mesh")
                return {'CANCELLED'}

            # Store original mode and switch to object mode
            original_mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
            original_verts = len(obj.data.vertices)

            # Calculate target vertex count
            target_verts = int(original_verts * (1.0 - self.factor))
            
            if target_verts >= original_verts:
                self.report({'WARNING'}, "Reduction factor too small to make any changes")
                bpy.ops.object.mode_set(mode=original_mode)
                return {'CANCELLED'}

            # Go to Edit Mode and select all
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')

            # Try increasing dissolve angles until desired reduction
            current_verts = original_verts
            for angle in [0.01, 0.05, 0.1, 0.2, 0.4, 0.8]:
                bpy.ops.mesh.dissolve_limited(angle_limit=angle)
                bpy.ops.object.mode_set(mode='OBJECT')
                current_verts = len(obj.data.vertices)
                
                if current_verts <= target_verts:
                    break
                    
                if current_verts > target_verts:
                    bpy.ops.object.mode_set(mode='EDIT')

            # Ensure we're in edit mode for Loop Tools
            bpy.ops.object.mode_set(mode='EDIT')
            
            # Run Loop Tools Space operator
            try:
                bpy.ops.mesh.looptools_space()
            except Exception as e:
                self.report({'WARNING'}, f"Could not run Loop Tools Space operator: {str(e)}. Make sure Loop Tools is enabled.")

            # Apply surface snap
            try:
                apply_surface_snap()
            except Exception as e:
                self.report({'WARNING'}, f"Could not apply surface snap: {str(e)}")

            # Restore original mode
            bpy.ops.object.mode_set(mode=original_mode)

            reduction_percent = ((original_verts - current_verts) / original_verts) * 100
            self.report({'INFO'}, f"Reduced vertices from {original_verts} to {current_verts} ({reduction_percent:.1f}% reduction)")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error reducing vertices: {str(e)}")
            # Try to restore original mode
            try:
                bpy.ops.object.mode_set(mode=original_mode)
            except:
                pass
            return {'CANCELLED'}

# Registration
classes = [OBJECT_OT_ReduceVerts]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
