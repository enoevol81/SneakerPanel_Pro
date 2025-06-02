import bpy
import bmesh
from mathutils import Vector
from . import panel_generator
from ..utils.collections import add_object_to_panel_collection

class OBJECT_OT_FlattenPanelUV(bpy.types.Operator):
    bl_idname = "object.flatten_panel_uv"
    bl_label = "Generate Panel Overlay"
    bl_description = "Generate a flattened panel with proper UV mapping"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Add undo checkpoint
        bpy.ops.ed.undo_push(message="Generate Panel Overlay")
        
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
        exact_name = f"{PANEL_OBJ_NAME_PREFIX}_{panel_count}"
        
        # Print available objects for debugging
        mesh_objects = [obj.name for obj in bpy.data.objects if obj.type == 'MESH']
        self.report({'INFO'}, f"Available mesh objects: {', '.join(mesh_objects)}")
        self.report({'INFO'}, f"Looking for panel with name: {exact_name}")
        
        # First try the exact name
        panel_obj = bpy.data.objects.get(exact_name)
        
        # If not found, try other naming patterns
        if not panel_obj:
            # Try old naming convention
            old_name = f"PanelMesh_{panel_count}"
            panel_obj = bpy.data.objects.get(old_name)
            if panel_obj:
                self.report({'INFO'}, f"Found panel using old naming: {old_name}")
        
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
            self.report({'ERROR'}, f"Panel mesh not found. Expected name like {exact_name}")
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
        return {'FINISHED'}

def register():
    bpy.utils.register_class(OBJECT_OT_FlattenPanelUV)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_FlattenPanelUV)
