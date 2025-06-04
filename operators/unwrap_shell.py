import bpy
import bmesh
from bpy.types import Operator

class OBJECT_OT_UnwrapShell(Operator):
    """Unwrap the selected shell object using smart UV unwrapping"""
    bl_idname = "object.unwrap_shell"
    bl_label = "Unwrap Shell"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Get the active object
        obj = context.active_object
        
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object")
            return {'CANCELLED'}
        
        # Store the current mode and switch to edit mode
        original_mode = obj.mode
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Get the bmesh
        bm = bmesh.from_edit_mesh(obj.data)
        
        # Ensure we have a UV layer named "UVMap"
        if not obj.data.uv_layers:
            obj.data.uv_layers.new(name="UVMap")
        elif obj.data.uv_layers.active.name != "UVMap":
            # If there's already a UV layer but it's not named "UVMap"
            if "UVMap" not in obj.data.uv_layers:
                # Create a new UVMap layer
                obj.data.uv_layers.new(name="UVMap")
            # Make UVMap the active layer
            obj.data.uv_layers.active = obj.data.uv_layers["UVMap"]
        
        # Select all faces
        for face in bm.faces:
            face.select = True
        
        # Update the edit mesh
        bmesh.update_edit_mesh(obj.data)
        
        # Perform the unwrap operation
        bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
        
        # Return to original mode
        bpy.ops.object.mode_set(mode=original_mode)
        
        self.report({'INFO'}, "Shell unwrapped successfully")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(OBJECT_OT_UnwrapShell)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_UnwrapShell)

if __name__ == "__main__":
    register()
