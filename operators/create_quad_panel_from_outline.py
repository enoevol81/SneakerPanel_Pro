# File: SneakerPanel_Pro/operators/create_quad_panel_from_outline.py
# This operator takes a mesh outline and creates a filled quad panel using the inset method.

import bpy
from bpy.props import FloatProperty, BoolProperty
from bpy.types import Operator
from ..utils.collections import add_object_to_panel_collection 

class MESH_OT_CreateQuadPanelFromOutline(Operator):
    """Creates a filled panel from an active mesh outline using an inset-fill method."""
    bl_idname = "mesh.create_quad_panel_from_outline"
    bl_label = "Create Quad Panel from Outline"
    bl_options = {'REGISTER', 'UNDO'}

    inset_thickness: FloatProperty(
        name="Border Inset Thickness",
        default=0.05, 
        min=0.001,
        description="Thickness of the inset that forms the clean border"
    )
    
    keep_original_outline: BoolProperty(
        name="Keep Original Outline",
        default=False, 
        description="Keep the input mesh outline object after creating the filled panel"
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def execute(self, context):
        original_outline_obj = context.active_object
        if not (original_outline_obj and original_outline_obj.type == 'MESH'):
            self.report({'ERROR'}, "An active Mesh outline object is required."); return {'CANCELLED'}

        bpy.ops.ed.undo_push(message=self.bl_label)

        bpy.ops.object.select_all(action='DESELECT')
        original_outline_obj.select_set(True)
        context.view_layer.objects.active = original_outline_obj
        bpy.ops.object.duplicate()
        working_obj = context.active_object 

        panel_count = getattr(context.scene, "spp_panel_count", 1)
        panel_name_prop = getattr(context.scene, "spp_panel_name", "Panel")
        working_obj.name = f"{panel_name_prop}_{panel_count}_PanelFillMesh"

        self.report({'INFO'}, "Attempting N-gon fill, inset, and deleting interior.")
        bpy.ops.object.select_all(action='DESELECT'); working_obj.select_set(True); context.view_layer.objects.active = working_obj
        if working_obj.mode != 'EDIT': bpy.ops.object.mode_set(mode='EDIT')
        
        try:
            # Step 1: Create single N-gon from boundary edges
            bpy.ops.mesh.select_all(action='SELECT') 
            bpy.ops.mesh.edge_face_add()
            self.report({'INFO'}, "Created N-gon face from boundary.")

            # Step 2: Inset the N-gon
            bpy.ops.mesh.select_mode(type="FACE")
            bpy.ops.mesh.inset(thickness=self.inset_thickness, use_even_offset=True, depth=0)
            self.report({'INFO'}, f"Applied inset with thickness {self.inset_thickness}.")
            
            # Step 3: Delete the interior face (which is left selected by inset)
            bpy.ops.mesh.delete(type='FACE')
            self.report({'INFO'}, "Deleted interior face, leaving quad border loop.")
            
            bpy.ops.mesh.select_mode(type="VERT")

        except RuntimeError as e:
            self.report({'ERROR'}, f"Failed during fill/inset/delete sequence: {e}")
            bpy.ops.object.mode_set(mode='OBJECT')
            if working_obj.name in bpy.data.objects: bpy.data.objects.remove(working_obj, do_unlink=True)
            return {'CANCELLED'}
            
        bpy.ops.object.mode_set(mode='OBJECT')

        if not working_obj.data.polygons:
            self.report({'ERROR'}, "Inset border creation failed to produce faces.")
            if working_obj.name in bpy.data.objects: bpy.data.objects.remove(working_obj, do_unlink=True)
            return {'CANCELLED'}
        
        add_object_to_panel_collection(working_obj, panel_count, panel_name_prop)
        
        if not self.keep_original_outline:
            bpy.data.objects.remove(original_outline_obj, do_unlink=True)
        else:
            original_outline_obj.hide_viewport = True 
        
        bpy.ops.object.select_all(action='DESELECT')
        working_obj.select_set(True)
        context.view_layer.objects.active = working_obj
        self.report({'INFO'}, f"Successfully created quad panel border: '{working_obj.name}'.")
        return {'FINISHED'}

classes = [MESH_OT_CreateQuadPanelFromOutline]
def register():
    for cls in classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
