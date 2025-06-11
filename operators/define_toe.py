"""
Defines the toe area of the shoe by placing an empty at the 3D cursor position.

This operator creates or updates an empty object at the 3D cursor position
to mark the toe area of the shoe. It also stores the toe direction as a
custom property on the active mesh object.
"""
import bpy
import bmesh
from bpy.types import Operator
from mathutils import Vector

class OBJECT_OT_DefineToe(Operator):
    """Define the toe area of the shoe by placing an empty at the 3D cursor position.
    
    Creates or updates an empty object at the 3D cursor position to mark the toe
    area of the shoe. The toe direction (from object origin to toe marker) is
    stored as a custom property on the active mesh object.
    
    This information can be used for orientation-aware operations on the shoe.
    """
    bl_idname = "object.define_toe"
    bl_label = "Define Toe"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        """Check if there is an active mesh object."""
        return context.active_object and context.active_object.type == 'MESH'
    
    def execute(self, context):
        # Get the active object (should be the shoe mesh)
        obj = context.active_object
        
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object")
            return {'CANCELLED'}
        
        # Get the 3D cursor position
        cursor_location = context.scene.cursor.location.copy()
        
        # Create an empty at the cursor location to mark the toe
        toe_empty = None
        
        # Check if a toe empty already exists
        if "Toe_Marker" in bpy.data.objects:
            # Use the existing empty
            toe_empty = bpy.data.objects["Toe_Marker"]
            toe_empty.location = cursor_location
        else:
            # Create a new empty
            toe_empty = bpy.data.objects.new("Toe_Marker", None)
            toe_empty.empty_display_type = 'ARROWS'
            toe_empty.empty_display_size = 0.2
            context.collection.objects.link(toe_empty)
            toe_empty.location = cursor_location
        
        # Store the original selection and active object
        original_active = context.view_layer.objects.active
        original_selected = context.selected_objects.copy()
        
        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')
        
        # Select the shoe mesh and make it active
        obj.select_set(True)
        context.view_layer.objects.active = obj
        
        # Store the current mode and ensure we're in object mode
        original_mode = obj.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Store the toe direction as a custom property on the mesh
        # Calculate direction from object origin to toe empty
        toe_direction = toe_empty.location - obj.location
        toe_direction.normalize()
        
        # Store the normalized direction as a custom property
        obj["toe_direction"] = toe_direction.to_tuple()
        
        # Restore original mode
        bpy.ops.object.mode_set(mode=original_mode)
        
        # Restore original selection
        bpy.ops.object.select_all(action='DESELECT')
        for o in original_selected:
            o.select_set(True)
        context.view_layer.objects.active = original_active
        
        self.report({'INFO'}, "Toe direction defined at cursor location")
        return {'FINISHED'}

# Registration
classes = [OBJECT_OT_DefineToe]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
