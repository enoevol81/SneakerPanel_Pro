# File: SneakerPanel_Pro/operators/fill_quad_border.py
# This operator fills the inner hole of a mesh border using a robust separate-and-join method.

import bpy
import bmesh
from bpy.props import BoolProperty
from bpy.types import Operator
from ..utils.collections import add_object_to_panel_collection 
from mathutils import Vector 

class MESH_OT_FillQuadPanelBorder(Operator):
    """Fills the interior hole of the active panel border mesh with quad topology."""
    bl_idname = "mesh.fill_quad_panel_border"
    bl_label = "Fill Panel Border"
    bl_options = {'REGISTER', 'UNDO'}
    
    keep_original_border: BoolProperty(
        name="Keep Original Border",
        default=False, 
        description="Keep the input mesh border object after creating the filled panel"
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def execute(self, context):
        original_border_obj = context.active_object
        if not (original_border_obj and original_border_obj.type == 'MESH'):
            self.report({'ERROR'}, "An active Mesh Border object is required."); return {'CANCELLED'}

        bpy.ops.ed.undo_push(message=self.bl_label)

        # --- 1. Duplicate the border object to work on ---
        bpy.ops.object.select_all(action='DESELECT')
        original_border_obj.select_set(True)
        context.view_layer.objects.active = original_border_obj
        bpy.ops.object.duplicate()
        working_obj = context.active_object 

        panel_count = getattr(context.scene, "spp_panel_count", 1)
        panel_name_prop = getattr(context.scene, "spp_panel_name", "Panel")
        working_obj.name = f"{panel_name_prop}_{panel_count}_FilledPanel"

        # --- 2. Create Quad Border and Isolate Center for Filling ---
        self.report({'INFO'}, "Creating border and preparing to fill center.")
        
        bpy.ops.object.select_all(action='DESELECT'); working_obj.select_set(True); context.view_layer.objects.active = working_obj
        if working_obj.mode != 'EDIT': bpy.ops.object.mode_set(mode='EDIT')
        
        center_fill_obj = None
        try:
            # Step A: Create single N-gon from boundary
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.edge_face_add() 
            self.report({'INFO'}, "Created initial N-gon face.")

            # Step B: Inset the N-gon face to create the border
            bpy.ops.mesh.select_mode(type="FACE")
            bpy.ops.mesh.inset(thickness=0.0189804, use_even_offset=True, depth=0) # Using your specific inset value
            self.report({'INFO'}, "Applied inset to create quad border.")
            
            # Step C: Separate the inner face for isolated processing
            # The inset op leaves the inner face selected.
            if any(f.select for f in bmesh.from_edit_mesh(working_obj.data).faces):
                bpy.ops.mesh.separate(type='SELECTED')
                # The separated part becomes a new object and is selected
                center_fill_obj = context.selected_objects[0]
                self.report({'INFO'}, f"Separated center face to new object: {center_fill_obj.name}")
            else:
                raise RuntimeError("Inset did not leave an inner face selected to separate.")
            
            # --- 3. Refine the Separated Center Piece ---
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            center_fill_obj.select_set(True)
            context.view_layer.objects.active = center_fill_obj
            bpy.ops.object.mode_set(mode='EDIT')
            
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.triangulate_faces()
            self.report({'INFO'}, "Triangulated center piece.")
            bpy.ops.mesh.tris_convert_to_quads()
            self.report({'INFO'}, "Converted center piece to quads.")
            
            bpy.ops.object.mode_set(mode='OBJECT')
            
            # --- 4. Join back and Merge ---
            self.report({'INFO'}, "Joining quad-filled center back to border.")
            bpy.ops.object.select_all(action='DESELECT')
            working_obj.select_set(True)
            center_fill_obj.select_set(True)
            context.view_layer.objects.active = working_obj # The target for the join
            
            bpy.ops.object.join()
            # 'working_obj' is now the combined mesh
            
            self.report({'INFO'}, "Merging vertices at seam.")
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles() # Merge by distance
            bpy.ops.object.mode_set(mode='OBJECT')


        except RuntimeError as e:
            self.report({'ERROR'}, f"Fill operation failed: {e}.")
            bpy.ops.object.mode_set(mode='OBJECT')
            if working_obj and working_obj.name in bpy.data.objects: bpy.data.objects.remove(working_obj, do_unlink=True)
            if center_fill_obj and center_fill_obj.name in bpy.data.objects: bpy.data.objects.remove(center_fill_obj, do_unlink=True)
            return {'CANCELLED'}
        
        # --- 5. Finalize ---
        add_object_to_panel_collection(working_obj, panel_count, panel_name_prop)
        
        if not self.keep_original_border:
            obj_to_remove = bpy.data.objects.get(original_border_obj.name)
            if obj_to_remove:
                bpy.data.objects.remove(obj_to_remove, do_unlink=True)
        else:
            original_border_obj.hide_viewport = True 
        
        bpy.ops.object.select_all(action='DESELECT')
        working_obj.select_set(True)
        context.view_layer.objects.active = working_obj
        self.report({'INFO'}, f"Successfully created filled panel: '{working_obj.name}'.")
        return {'FINISHED'}


classes = [MESH_OT_FillQuadPanelBorder]
def register():
    for cls in classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
