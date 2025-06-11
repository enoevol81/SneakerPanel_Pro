"""
Generates panels from mesh outlines on shoe shells.

This operator takes a panel mesh outline and generates a filled panel mesh
with proper topology and surface conformity to the shoe shell. It uses the
panel_generator module to perform the actual mesh generation and ensures
the result is properly named and added to the correct collection.
"""
import bpy
import bmesh
import mathutils
from ..utils.collections import add_object_to_panel_collection
from . import panel_generator

class OBJECT_OT_PanelGenerate(bpy.types.Operator):
    """Generate a filled panel mesh from an outline.
    
    This operator takes a panel mesh outline (typically created from a curve)
    and fills it with a quad-based grid topology that conforms to the shoe shell.
    The resulting mesh is properly named, added to the appropriate collection,
    and the original outline mesh is hidden.
    
    Prerequisites:
    - A panel mesh outline must exist with the appropriate naming convention
    - A shell object must be set in the scene properties
    - Grid fill span settings must be configured in scene properties
    """
    bl_idname = "object.panel_generate"
    bl_label = "Generate Panel"
    bl_description = "Generate a filled panel mesh from an outline"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        """Check if we have a valid shell object."""
        return (hasattr(context.scene, 'spp_shell_object') and 
                context.scene.spp_shell_object and 
                context.scene.spp_shell_object.type == 'MESH')

    def execute(self, context):
        # Add undo checkpoint
        bpy.ops.ed.undo_push(message="Generate Panel")
        
        # Get panel count and name for naming
        panel_count = context.scene.spp_panel_count if hasattr(context.scene, "spp_panel_count") else 1
        panel_name = context.scene.spp_panel_name if hasattr(context.scene, "spp_panel_name") else "Panel"
        
        # Check if we have a custom panel name
        if panel_name and panel_name.strip():
            PANEL_OBJ_NAME_PREFIX = f"{panel_name}_Mesh"
            FILLED_OBJ_NAME = f"{panel_name}_Filled_{panel_count}"
        else:
            PANEL_OBJ_NAME_PREFIX = "PanelMesh"
            FILLED_OBJ_NAME = f"PanelMesh_Filled_{panel_count}"
            
        SHELL_OBJ_NAME = context.scene.spp_shell_object.name if context.scene.spp_shell_object else "3DShoeShell"
        UV_LAYER_NAME = "UVMap"

        try:
            # Ensure we're in object mode
            if bpy.context.object and bpy.context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')

            # Get the shell object
            shell_obj = bpy.data.objects.get(SHELL_OBJ_NAME)
            if not shell_obj:
                self.report({'ERROR'}, f"Shell object {SHELL_OBJ_NAME} not found.")
                return {'CANCELLED'}
            
            # Find the panel object with our naming convention
            panel_obj = None
            
            # Try different naming patterns
            possible_names = [
                f"{PANEL_OBJ_NAME_PREFIX}_{panel_count}",  # New naming: Counter_Mesh_1
                f"PanelMesh_{panel_count}",              # Old naming: PanelMesh_1
                f"{panel_name}_Mesh_{panel_count}"       # Alternate naming: Counter_Mesh_1
            ]
            
            # Print available objects for debugging
            mesh_objects = [obj.name for obj in bpy.data.objects if obj.type == 'MESH']
            self.report({'INFO'}, f"Available mesh objects: {', '.join(mesh_objects)}")
            self.report({'INFO'}, f"Looking for panel with names: {', '.join(possible_names)}")
            
            # Try each possible name
            for name in possible_names:
                obj = bpy.data.objects.get(name)
                if obj:
                    panel_obj = obj
                    self.report({'INFO'}, f"Found panel object: {name}")
                    break
            
            # If still not found, try a more flexible approach
            if not panel_obj:
                for obj in bpy.data.objects:
                    if obj.type == 'MESH':
                        # Check various naming patterns
                        if (obj.name.startswith(PANEL_OBJ_NAME_PREFIX) or
                            obj.name.startswith(f"{panel_name}_Mesh") or
                            obj.name.startswith("PanelMesh")):
                            panel_obj = obj
                            self.report({'INFO'}, f"Found panel by prefix: {obj.name}")
                            break
            
            if not panel_obj:
                self.report({'ERROR'}, f"Panel mesh not found. Tried names: {', '.join(possible_names)}")
                return {'CANCELLED'}
            
            # Use the panel_generator module to generate the panel
            grid_span = context.scene.spp_grid_fill_span
            
            # Generate the panel using the utility module
            filled_obj = panel_generator.generate_panel(
                panel_obj=panel_obj,
                shell_obj=shell_obj,
                filled_obj_name=FILLED_OBJ_NAME,
                grid_span=grid_span,
                uv_layer_name=UV_LAYER_NAME
            )
            
            if not filled_obj:
                self.report({'ERROR'}, "Panel generation failed. Check console for details.")
                return {'CANCELLED'}
            
            # Add to proper collection
            add_object_to_panel_collection(filled_obj, panel_count, panel_name)
            
            # Hide the input mesh to keep the viewport clean
            if panel_obj:
                panel_obj.hide_viewport = True
                self.report({'INFO'}, f"Hidden input mesh: {panel_obj.name}")
            
            # Make the new filled object active and selected
            bpy.ops.object.select_all(action='DESELECT')
            filled_obj.select_set(True)
            bpy.context.view_layer.objects.active = filled_obj
            
            # Increment panel count if needed
            if hasattr(context.scene, "spp_panel_count"):
                context.scene.spp_panel_count += 1

            self.report({'INFO'}, f"✅ Flattened and filled: {FILLED_OBJ_NAME}")
            
        except Exception as e:
            self.report({'ERROR'}, f"Error generating panel: {str(e)}")
            return {'CANCELLED'}
            
        return {'FINISHED'}

# Registration
classes = [OBJECT_OT_PanelGenerate]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
