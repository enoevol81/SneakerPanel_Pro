"""
Converts curves to meshes with surface snapping and proper collection management.

This operator takes a curve object and converts it to a mesh, applies surface
snapping, and adds it to the appropriate collection based on the panel count.
"""
import bpy
from ..utils.panel_utils import apply_surface_snap
from ..utils.collections import add_object_to_panel_collection

class OBJECT_OT_ConvertToMesh(bpy.types.Operator):
    """Convert selected curve to mesh and apply surface snapping.
    
    Converts the active curve object to a mesh, applies surface snapping,
    and organizes it into the appropriate panel collection.
    """
    bl_idname = "object.convert_to_mesh"
    bl_label = "Convert to Mesh"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        """Check if the active object is valid for this operator."""
        return context.active_object and context.active_object.type == 'CURVE'

    def execute(self, context):
        # Add undo checkpoint
        bpy.ops.ed.undo_push(message="Convert to Mesh")
        
        if bpy.context.object.mode == 'EDIT':
            bpy.ops.object.editmode_toggle()

        bpy.ops.object.convert(target='MESH')
        mesh_obj = context.active_object
        
        # Get panel count and name for naming
        panel_count = context.scene.spp_panel_count if hasattr(context.scene, "spp_panel_count") else 1
        panel_name = context.scene.spp_panel_name if hasattr(context.scene, "spp_panel_name") else "Panel"
        
        # Use descriptive name if provided, otherwise use default naming
        if panel_name and panel_name.strip():
            mesh_obj.name = f"{panel_name}_Mesh_{panel_count}"
        else:
            mesh_obj.name = f"PanelMesh_{panel_count}"
        
        # Add to proper collection
        add_object_to_panel_collection(mesh_obj, panel_count, panel_name)
        
        bpy.ops.object.editmode_toggle()

        if bpy.context.object.type == 'MESH':
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.mesh.select_all(action='SELECT')
            
            # First apply surface snap
            apply_surface_snap()
            
            # Then try to space vertices evenly
            try:
                bpy.ops.mesh.looptools_space(
                    influence=100,
                    input='selected',
                    interpolation='cubic',
                    lock_x=False,
                    lock_y=False,
                    lock_z=False
                )
            except Exception as e:
                self.report({'WARNING'}, f"LoopTools not available: {str(e)}")
            
            # Apply surface snap again after spacing
            apply_surface_snap()
        else:
            self.report({'ERROR'}, "Active object is not a mesh.")
            return {'CANCELLED'}

        bpy.ops.object.editmode_toggle()
        self.report({'INFO'}, f"Curve converted to Mesh and renamed to '{mesh_obj.name}'.")
        return {'FINISHED'}

# Registration
classes = [OBJECT_OT_ConvertToMesh]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
