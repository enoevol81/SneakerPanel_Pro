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
        """Always available regardless of context."""
        return True
    
    def execute(self, context):
        # Add undo checkpoint
        bpy.ops.ed.undo_push(message="Define Toe Marker")
        
        # Get the active object (should be the shoe mesh)
        obj = context.active_object
        
        # Check if there's an active object
        if not obj:
            self.report({'WARNING'}, "No active object. Creating toe marker at cursor position.")
            # We'll still create the toe marker, just won't store direction on any object
        
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
        
        # Store the original active object
        original_active = context.view_layer.objects.active
        
        # We'll avoid using bpy.ops.object.select_all() as it's context-sensitive
        # Instead, we'll store which objects were selected
        original_selected_names = [o.name for o in context.view_layer.objects if o.select_get()]
        
        # We'll also avoid using mode_set operators which are context-sensitive
        original_mode = None
        if obj:
            original_mode = obj.mode
            # Try to make the object active if possible
            try:
                context.view_layer.objects.active = obj
            except:
                pass
        
        # Store the toe direction as a custom property if we have a valid mesh object
        if obj and obj.type == 'MESH':
            # Calculate direction from object origin to toe empty
            toe_direction = toe_empty.location - obj.location
            toe_direction.normalize()
            
            # Store the normalized direction as a custom property
            obj["toe_direction"] = toe_direction.to_tuple()
            self.report({'INFO'}, f"Toe marker created at cursor and direction stored on {obj.name}")
        else:
            self.report({'INFO'}, "Toe marker created at cursor position")
        
        # Restore original active object if possible
        try:
            if original_active:
                context.view_layer.objects.active = original_active
        except:
            pass
            
        # Restore original selection state if possible
        try:
            # First deselect all objects directly
            for obj in context.view_layer.objects:
                obj.select_set(False)
                
            # Then select the originally selected objects
            for name in original_selected_names:
                if name in bpy.data.objects:
                    bpy.data.objects[name].select_set(True)
        except:
            pass
        
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
