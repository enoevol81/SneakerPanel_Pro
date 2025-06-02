import bpy
from ..utils.panel_utils import apply_surface_snap

class OBJECT_OT_ReduceVerts(bpy.types.Operator):
    bl_idname = "object.reduce_verts"
    bl_label = "Reduce Verts"
    bl_description = "Reduce mesh vertices while maintaining shape"

    factor: bpy.props.FloatProperty(
        name="Reduction Factor",
        description="Factor to reduce vertices by (0.0 to 1.0)",
        min=0.0,
        max=1.0,
        default=0.2
    )

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        # Add undo checkpoint
        bpy.ops.ed.undo_push(message="Reduce Vertices")
        
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

        # Go to Edit Mode and select all
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')

        # Try increasing dissolve angles until desired reduction
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
            self.report({'WARNING'}, "Could not run Loop Tools Space operator. Make sure Loop Tools is enabled.")

        # Apply surface snap
        apply_surface_snap()

        # Restore original mode
        bpy.ops.object.mode_set(mode=original_mode)

        reduction_percent = ((original_verts - current_verts) / original_verts) * 100
        self.report({'INFO'}, f"Reduced vertices from {original_verts} to {current_verts} ({reduction_percent:.1f}% reduction)")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(OBJECT_OT_ReduceVerts)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_ReduceVerts)
