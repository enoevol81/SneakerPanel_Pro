# File: SneakerPanel_Pro/operators/create_2d_filled_mesh.py

import bpy
from bpy.props import IntProperty, BoolProperty
from bpy.types import Operator
from ..utils.collections import add_object_to_panel_collection # Assuming you want to use this

class CURVE_OT_Create2DFilledMesh(Operator):
    """Converts active 2D curve to a 2D filled mesh using Grid Fill"""
    bl_idname = "curve.create_2d_filled_mesh"
    bl_label = "Curve to 2D Filled Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    grid_fill_span: IntProperty(
        name="Grid Fill Spans",
        default=4,
        min=1,
        max=100, # Adjusted max for practical use
        description="Number of spans for the grid fill. Higher values create more subdivisions."
    )
    grid_fill_offset: IntProperty(
        name="Grid Fill Offset",
        default=0,
        min=0,
        description="Offset for the grid fill pattern."
    )
    grid_fill_simple_blend: BoolProperty(
        name="Simple Blending",
        default=True, # Often gives better results for irregular boundaries
        description="Use simple blending for grid fill (less twisting)"
    )
    
    keep_original_curve: BoolProperty(
        name="Keep Original Curve",
        default=True,
        description="Keep the original input curve object after creating the mesh"
    )


    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'CURVE' and obj.data.dimensions == '2D')

    def execute(self, context):
        original_curve_obj = context.active_object
        if not original_curve_obj:
            self.report({'ERROR'}, "No active curve object selected.")
            return {'CANCELLED'}

        if original_curve_obj.data.dimensions != '2D':
            # Optionally, try to flatten it, or error out. For now, error out if not 2D.
            self.report({'ERROR'}, "Selected curve is not 2D. Please ensure Z values are 0 or use a 2D curve.")
            # You could add logic here to flatten the curve if desired:
            # for spline in original_curve_obj.data.splines:
            #     for pt in spline.points: pt.co.z = 0
            #     for bp in spline.bezier_points: bp.co.z = 0; bp.handle_left.z = 0; bp.handle_right.z = 0
            return {'CANCELLED'}

        bpy.ops.ed.undo_push(message=self.bl_label)

        # --- 1. Duplicate the curve ---
        bpy.ops.object.select_all(action='DESELECT')
        original_curve_obj.select_set(True)
        context.view_layer.objects.active = original_curve_obj
        bpy.ops.object.duplicate()
        working_obj = context.active_object # This is the duplicated curve

        # --- 2. Convert duplicated curve to mesh (creates an edge loop) ---
        self.report({'INFO'}, f"Converting '{working_obj.name}' to mesh.")
        bpy.ops.object.convert(target='MESH')
        # working_obj is now a mesh object

        if working_obj.type != 'MESH':
            self.report({'ERROR'}, "Conversion to mesh failed unexpectedly.")
            if working_obj.name in bpy.data.objects: bpy.data.objects.remove(working_obj, do_unlink=True) # Clean up duplicate
            return {'CANCELLED'}

        # Ensure all Z coordinates are 0 for a truly flat 2D mesh
        # (Conversion from 2D curve should handle this, but good to be sure)
        if working_obj.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
        for v in working_obj.data.vertices:
            v.co.z = 0.0
        working_obj.data.update()


        # --- 3. Perform Grid Fill ---
        self.report({'INFO'}, "Attempting Grid Fill.")
        bpy.ops.object.select_all(action='DESELECT')
        working_obj.select_set(True)
        context.view_layer.objects.active = working_obj
        
        if working_obj.mode != 'EDIT': bpy.ops.object.mode_set(mode='EDIT')
        
        bpy.ops.mesh.select_all(action='SELECT') # Select all edges of the boundary
        try:
            bpy.ops.mesh.fill_grid(
                span=self.grid_fill_span,
                offset=self.grid_fill_offset,
                use_simple_blending=self.grid_fill_simple_blend
            )
            self.report({'INFO'}, f"Grid Fill applied with span: {self.grid_fill_span}")
        except RuntimeError as e:
            self.report({'ERROR'}, f"Grid Fill failed: {e}. The boundary might be unsuitable. Trying simple fill.")
            # Fallback to simple fill if Grid Fill fails
            bpy.ops.mesh.select_all(action='SELECT') # Re-select if previous op deselected
            try:
                bpy.ops.mesh.fill() # 'F' key fill
                self.report({'INFO'}, "Fallback simple fill applied.")
                # Optionally try beautify after simple fill
                bpy.ops.mesh.select_mode(type="FACE")
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.beautify_fill()
                bpy.ops.mesh.select_mode(type="VERT") # Back to vert mode
                self.report({'INFO'}, "Beautify fill applied after fallback.")
            except RuntimeError as fill_e:
                self.report({'ERROR'}, f"Fallback simple fill also failed: {fill_e}")
                bpy.ops.object.mode_set(mode='OBJECT')
                # Clean up the partially processed mesh
                if working_obj.name in bpy.data.objects: bpy.data.objects.remove(working_obj, do_unlink=True)
                return {'CANCELLED'}

        bpy.ops.object.mode_set(mode='OBJECT')

        if not working_obj.data.polygons:
            self.report({'ERROR'}, "Failed to create any faces. Please check curve integrity (e.g., ensure it's closed).")
            if working_obj.name in bpy.data.objects: bpy.data.objects.remove(working_obj, do_unlink=True)
            return {'CANCELLED'}

        # --- 4. Finalize and Manage Objects ---
        panel_count = getattr(context.scene, "spp_panel_count", 1)
        panel_name_prop = getattr(context.scene, "spp_panel_name", "Panel")
        
        filled_mesh_name = f"{original_curve_obj.name}_FilledMesh"
        if panel_name_prop and panel_name_prop.strip() != "Panel":
             filled_mesh_name = f"{panel_name_prop}_{panel_count}_2DFilledMesh"
        
        working_obj.name = filled_mesh_name
        if working_obj.data:
            working_obj.data.name = f"{filled_mesh_name}_Data"

        # Add to collection using your utility
        add_object_to_panel_collection(working_obj, panel_count, panel_name_prop)
        self.report({'INFO'}, f"Created 2D filled mesh: '{working_obj.name}'")

        if not self.keep_original_curve:
            bpy.data.objects.remove(original_curve_obj, do_unlink=True)
            self.report({'INFO'}, "Original curve deleted.")
        else:
            original_curve_obj.hide_viewport = True # Hide original by default
            self.report({'INFO'}, "Original curve hidden.")

        # Make the new filled mesh active and selected
        bpy.ops.object.select_all(action='DESELECT')
        working_obj.select_set(True)
        context.view_layer.objects.active = working_obj
        
        return {'FINISHED'}

def register():
    bpy.utils.register_class(CURVE_OT_Create2DFilledMesh)

def unregister():
    bpy.utils.unregister_class(CURVE_OT_Create2DFilledMesh)
