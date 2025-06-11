"""
Shell unwrapping operator for SneakerPanel Pro.

This module provides functionality to unwrap a 3D shoe shell mesh for UV mapping.
It creates or ensures a UVMap layer exists and performs angle-based unwrapping
to create a clean UV layout suitable for panel design and visualization.
"""

import bpy
import bmesh
from bpy.types import Operator


class OBJECT_OT_UnwrapShell(Operator):
    """Unwrap the selected shell object using smart UV unwrapping.
    
    This operator creates or ensures a UVMap layer exists on the active mesh
    and performs angle-based unwrapping to create a clean UV layout. This is
    typically used on shoe shell meshes to prepare them for panel design in UV space.
    
    The unwrapping uses Blender's angle-based method with a small margin to
    prevent UV islands from touching. The operator works in edit mode and
    restores the original mode when finished.
    """
    bl_idname = "object.unwrap_shell"
    bl_label = "Unwrap Shell"
    bl_description = "Unwrap the selected shell mesh for UV mapping"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        """Check if the operator can be executed.
        
        Args:
            context: Blender context
            
        Returns:
            bool: True if active object is a mesh
        """
        obj = context.active_object
        return obj is not None and obj.type == 'MESH'
    
    def execute(self, context):
        """Execute the unwrap operation.
        
        Args:
            context: Blender context
            
        Returns:
            set: {'FINISHED'} on success, {'CANCELLED'} on error
        """
        # Add undo checkpoint
        bpy.ops.ed.undo_push(message="Unwrap Shell")
        
        try:
            # Get the active object
            obj = context.active_object
            
            if not obj or obj.type != 'MESH':
                self.report({'ERROR'}, "Please select a mesh object")
                return {'CANCELLED'}
            
            # Store the current mode and switch to edit mode
            original_mode = obj.mode
            bpy.ops.object.mode_set(mode='EDIT')
            
            try:
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
                
                self.report({'INFO'}, "Shell unwrapped successfully")
                return {'FINISHED'}
                
            except Exception as e:
                self.report({'ERROR'}, f"Error during unwrapping: {str(e)}")
                return {'CANCELLED'}
                
            finally:
                # Return to original mode
                if obj.mode != original_mode:
                    bpy.ops.object.mode_set(mode=original_mode)
                
        except Exception as e:
            self.report({'ERROR'}, f"Unwrap operation failed: {str(e)}")
            return {'CANCELLED'}


# Registration
classes = [OBJECT_OT_UnwrapShell]


def register():
    """Register the operator."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister the operator."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
