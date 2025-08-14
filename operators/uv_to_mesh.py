"""
UV to Mesh conversion operator for SneakerPanel Pro.

This module provides functionality to convert a UV map from a 3D shell object into
a 2D mesh representation. It creates a flat mesh based on the UV coordinates and
sets up a Grease Pencil object for drawing on this UV mesh. This is a critical part
of the workflow for creating 2D panel patterns from 3D shoe surfaces.
"""

import math

import bmesh
import bpy
from bpy.props import BoolProperty
from bpy.types import Operator
from mathutils import Vector

from ..utils.collections import add_object_to_panel_collection


def convert_object_to_mesh(obj, apply_modifiers=True, preserve_status=True):
    """Convert any object to a mesh object.

    Creates a duplicate of the input object and converts it to a mesh,
    optionally applying modifiers. Preserves the original selection state
    if requested.

    Args:
        obj: The source object to convert
        apply_modifiers: Whether to apply modifiers during conversion
        preserve_status: Whether to preserve original selection and active object

    Returns:
        The new mesh object
    """
    original_active = None
    original_selected = []

    # Store original selection state if requested
    if preserve_status:
        original_active = bpy.context.view_layer.objects.active
        original_selected = [o for o in bpy.context.selected_objects]
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        for o_sel in bpy.context.selected_objects:
            o_sel.select_set(False)

    # Select and duplicate the object
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.duplicate()
    new_obj = bpy.context.view_layer.objects.active

    # Convert to mesh
    if new_obj.type != "MESH":
        if apply_modifiers:
            bpy.ops.object.convert(target="MESH")
        else:
            bpy.ops.object.convert(target="MESH", keep_original=False)
    elif apply_modifiers and new_obj.type == "MESH":
        bpy.ops.object.convert(target="MESH")

    # Restore original selection state if requested
    if preserve_status:
        if new_obj not in original_selected:
            new_obj.select_set(False)
        for o_sel in original_selected:
            if o_sel and o_sel.name in bpy.data.objects:
                o_sel.select_set(True)
        if original_active and original_active.name in bpy.data.objects:
            bpy.context.view_layer.objects.active = original_active

    return new_obj


class OBJECT_OT_UVToMesh(Operator):
    """UV to Mesh and Prep for Drawing Operator

    Creates a UV Mesh, adds Grease Pencil, isolates, frames, and sets view for drawing.

    Properties:
        apply_modifiers (BoolProperty): Apply object's modifiers from the Shell Object
        vertex_groups (BoolProperty): Keep Vertex Groups
        materials (BoolProperty): Keep Materials
        auto_scale (BoolProperty): Resize (Preserve Area)
    """

    bl_idname = "object.uv_to_mesh"
    bl_label = "UV to Mesh and Prep for Drawing"
    bl_description = "Creates UV Mesh, adds Grease Pencil, isolates, frames, and sets view for drawing."
    bl_options = {"REGISTER", "UNDO"}

    apply_modifiers: BoolProperty(  # (Properties as before)
        name="Apply Modifiers",
        default=True,
        description="Apply object's modifiers from the Shell Object",
    )
    vertex_groups: BoolProperty(
        name="Keep Vertex Groups",
        default=True,
        description="Transfer all the Vertex Groups",
    )
    materials: BoolProperty(
        name="Keep Materials", default=True, description="Transfer all the Materials"
    )
    auto_scale: BoolProperty(
        name="Resize (Preserve Area)",
        default=True,
        description="Scale new object to preserve average surface area from Shell Object",
    )

    @classmethod
    def poll(cls, context):
        if (
            hasattr(context.scene, "spp_shell_object")
            and context.scene.spp_shell_object
        ):
            return context.scene.spp_shell_object.type == "MESH"
        return False

    def execute(self, context):
        # Context-agnostic execution - automatically switch to required mode
        source_object_from_scene = context.scene.spp_shell_object
        if not source_object_from_scene:  # Should be caught by poll
            self.report({"ERROR"}, "No 'Shell Object' defined in Scene Properties.")
            return {"CANCELLED"}
        if source_object_from_scene.type != "MESH":  # Should be caught by poll
            self.report({"ERROR"}, "'Shell Object' must be a Mesh type.")
            return {"CANCELLED"}
        if (
            not source_object_from_scene.data.uv_layers
            or not source_object_from_scene.data.uv_layers.active
        ):
            self.report(
                {"ERROR"},
                f"'{source_object_from_scene.name}' (Shell Object) has no active UV map.",
            )
            return {"CANCELLED"}

        # Store original mode for restoration
        original_mode = (
            context.active_object.mode if context.active_object else "OBJECT"
        )

        # Switch to Object Mode if not already there
        if context.mode != "OBJECT":
            try:
                bpy.ops.object.mode_set(mode="OBJECT")
            except Exception as e:
                self.report({"ERROR"}, f"Could not switch to Object Mode: {str(e)}")
                return {"CANCELLED"}

        active_obj_backup = context.view_layer.objects.active
        selected_objs_backup = context.selected_objects[:]
        if selected_objs_backup:
            bpy.ops.object.select_all(action="DESELECT")

        ob0_for_conversion = convert_object_to_mesh(
            source_object_from_scene,
            apply_modifiers=self.apply_modifiers,
            preserve_status=False,
        )
        me0_from_conversion = ob0_for_conversion.data
        original_source_name = source_object_from_scene.name

        # (Core UV mesh generation logic - bmesh, face creation, scaling - as before)
        # ...
        area_3d = 0
        bm = bmesh.new()
        polygons_to_process = me0_from_conversion.polygons
        if not polygons_to_process:  # ... (error handling) ...
            self.report(
                {"ERROR"}, f"No polygons in Shell Object '{original_source_name}'."
            )
            bpy.data.objects.remove(ob0_for_conversion)
            bpy.data.meshes.remove(me0_from_conversion)
            return {"CANCELLED"}
        active_uv_layer_data = me0_from_conversion.uv_layers.active.data
        uv_to_bm_vert_map = {}
        for face in polygons_to_process:
            area_3d += face.area
            face_bm_verts = []
            for loop_idx in face.loop_indices:
                uv = active_uv_layer_data[loop_idx].uv
                uv_key = (round(uv.x, 6), round(uv.y, 6))
                if uv_key not in uv_to_bm_vert_map:
                    uv_to_bm_vert_map[uv_key] = bm.verts.new((uv.x, uv.y, 0.0))
                face_bm_verts.append(uv_to_bm_vert_map[uv_key])
            if len(face_bm_verts) >= 3:
                try:
                    new_face = bm.faces.new(face_bm_verts)
                    if self.materials:
                        new_face.material_index = face.material_index
                except ValueError:
                    pass
        if not bm.faces:  # ... (error handling) ...
            self.report({"ERROR"}, "No valid UV faces generated.")
            bpy.data.objects.remove(ob0_for_conversion)
            bpy.data.meshes.remove(me0_from_conversion)
            bm.free()
            return {"CANCELLED"}

        # Naming for UV Mesh is already as requested: [Shell Name]_UV_Mesh
        new_uv_mesh_name = f"{original_source_name}_UV_Mesh"
        me_uv = bpy.data.meshes.new(f"{new_uv_mesh_name}_Data")
        ob_uv = bpy.data.objects.new(new_uv_mesh_name, me_uv)
        context.collection.objects.link(ob_uv)  # Temporarily link to current collection
        bm.to_mesh(me_uv)
        bm.free()
        me_uv.update()

        calculated_scale_factor = 1.0  # ... (auto-scaling logic as before) ...
        if self.auto_scale:
            area_uv_unscaled = sum(p.area for p in me_uv.polygons)
            if area_uv_unscaled > 1e-9:
                calculated_scale_factor = math.sqrt(area_3d / area_uv_unscaled)
                ob_uv.scale = Vector(
                    (calculated_scale_factor, calculated_scale_factor, 1.0)
                )
                current_active = context.view_layer.objects.active
                current_selected = context.selected_objects[:]
                bpy.ops.object.select_all(action="DESELECT")
                context.view_layer.objects.active = ob_uv
                ob_uv.select_set(True)
                bpy.ops.object.transform_apply(
                    location=False, rotation=False, scale=True
                )
                ob_uv.select_set(False)  # Deselect after applying
                for o in current_selected:
                    if o and o.name in bpy.data.objects:
                        o.select_set(True)
                if current_active and current_active.name in bpy.data.objects:
                    context.view_layer.objects.active = current_active
                else:
                    context.view_layer.objects.active = (
                        ob_uv  # Fallback if original active is gone
                    )

            elif area_3d > 1e-9:
                self.report({"WARNING"}, "UV mesh area zero, cannot auto-scale.")

        ob_uv["spp_original_3d_mesh_name"] = original_source_name
        ob_uv["spp_applied_scale_factor"] = calculated_scale_factor
        if source_object_from_scene.data.uv_layers.active:
            ob_uv["spp_source_uv_map_name"] = (
                source_object_from_scene.data.uv_layers.active.name
            )
        if self.materials:  # ... (material transfer as before) ...
            ob_uv.data.materials.clear()
            for mat_slot in source_object_from_scene.material_slots:
                if mat_slot.material:
                    ob_uv.data.materials.append(mat_slot.material)

        # (Finalize ob_uv: remove doubles - as before)
        # ...
        prev_active = context.view_layer.objects.active
        prev_selected = context.selected_objects[:]
        bpy.ops.object.select_all(action="DESELECT")
        context.view_layer.objects.active = ob_uv
        ob_uv.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.remove_doubles(threshold=1e-6)
        bpy.ops.object.mode_set(mode="OBJECT")
        for o_sel in prev_selected:
            if o_sel and o_sel.name in bpy.data.objects and o_sel != ob_uv:
                o_sel.select_set(True)
        if (
            prev_active
            and prev_active.name in bpy.data.objects
            and prev_active != ob_uv
        ):
            context.view_layer.objects.active = prev_active
        else:
            context.view_layer.objects.active = ob_uv

        bpy.data.objects.remove(ob0_for_conversion)
        bpy.data.meshes.remove(me0_from_conversion)

        # --- COLLECTION MANAGEMENT for UV Mesh ---
        panel_count = context.scene.spp_panel_count
        panel_name_prop = context.scene.spp_panel_name
        add_object_to_panel_collection(ob_uv, panel_count, panel_name_prop)
        self.report(
            {"INFO"},
            f"UV Mesh '{ob_uv.name}' added to collection for '{panel_name_prop} {panel_count}'.",
        )

        # --- SET UV MESH TO WIREFRAME DISPLAY ---
        # Set the display type to wireframe for better visibility when drawing
        ob_uv.display_type = "WIRE"  # Options: 'BOUNDS', 'WIRE', 'SOLID', 'TEXTURED'
        # Also set the viewport display settings
        if hasattr(ob_uv, "show_wire"):
            ob_uv.show_wire = True  # Show wireframe on top of solid/textured
        if hasattr(ob_uv, "show_all_edges"):
            ob_uv.show_all_edges = True  # Show all edges for better visibility

        # --- CREATE AND SETUP NEW GREASE PENCIL OBJECT ---
        self.report({"INFO"}, "Creating Grease Pencil object for UV drawing.")
        # Ensure ob_uv is at a known location if GP is parented or aligned (it should be at origin after scale apply)
        gp_location = (
            ob_uv.location
        )  # ob_uv is at origin if scale was applied without location change

        # Create GP object
        bpy.ops.object.select_all(
            action="DESELECT"
        )  # Deselect all before adding new GP
        bpy.ops.object.grease_pencil_add(
            location=gp_location, type="EMPTY"
        )  # Add blank GP
        gp_obj_uv_draw = context.active_object

        # Name the GP object
        gp_name_base = (
            f"{panel_name_prop}_GPDraw_UV_{panel_count}"
            if panel_name_prop and panel_name_prop.strip()
            else f"GPDraw_UV_{panel_count}"
        )
        gp_obj_uv_draw.name = gp_name_base
        if gp_obj_uv_draw.data:  # GP Data block also gets a name
            gp_obj_uv_draw.data.name = f"{gp_name_base}_Data"

        # Add GP object to the same panel collection
        add_object_to_panel_collection(gp_obj_uv_draw, panel_count, panel_name_prop)
        self.report(
            {"INFO"}, f"Grease Pencil '{gp_obj_uv_draw.name}' added to collection."
        )

        # Configure Grease Pencil for drawing on surface (similar to add_gp_draw.py)
        context.view_layer.objects.active = (
            gp_obj_uv_draw  # Make GP active for mode set
        )
        bpy.ops.object.mode_set(mode="PAINT_GREASE_PENCIL")
        context.scene.tool_settings.gpencil_stroke_placement_view3d = "SURFACE"
        context.scene.tool_settings.use_gpencil_automerge_strokes = True

        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
        brush = context.tool_settings.gpencil_paint.brush
        if brush:
            brush.use_smooth_stroke = getattr(
                context.scene, "spp_use_stabilizer", False
            )
            brush.smooth_stroke_factor = getattr(
                context.scene, "spp_stabilizer_factor", 0.75
            )
            brush.smooth_stroke_radius = getattr(
                context.scene, "spp_stabilizer_radius", 35
            )
            self.report({"INFO"}, "Grease Pencil brush configured for surface drawing.")
        else:
            self.report({"WARNING"}, "Could not get Grease Pencil brush to configure.")

        # --- VIEWPORT AND ISOLATION ENHANCEMENTS ---
        self.report({"INFO"}, "Configuring view and isolation for UV mesh and GP.")

        # Select both objects for framing
        bpy.ops.object.mode_set(mode="OBJECT")  # Ensure Object mode for selection
        bpy.ops.object.select_all(action="DESELECT")
        ob_uv.select_set(True)
        gp_obj_uv_draw.select_set(True)
        context.view_layer.objects.active = gp_obj_uv_draw  # GP active for drawing

        area_3d = None
        region_3d_window = None
        for area_iter in context.screen.areas:
            if area_iter.type == "VIEW_3D":
                area_3d = area_iter
                for region_iter in area_iter.regions:
                    if region_iter.type == "WINDOW":
                        if region_3d_window is None or (
                            region_iter.width * region_iter.height
                            > region_3d_window.width * region_3d_window.height
                        ):
                            region_3d_window = region_iter
                break

        if area_3d and region_3d_window:
            space_data = area_3d.spaces.active
            if space_data.type == "VIEW_3D":
                original_perspective = (
                    space_data.region_3d.view_perspective
                )  # Store for potential restore
                space_data.region_3d.view_perspective = "ORTHO"

                override_context = context.copy()
                override_context["area"] = area_3d
                override_context["region"] = region_3d_window
                override_context["screen"] = context.screen
                override_context["window"] = context.window

                with context.temp_override(**override_context):
                    bpy.ops.view3d.view_axis(type="TOP")
                    bpy.ops.view3d.view_selected(
                        use_all_regions=False
                    )  # Frames selected (both ob_uv and gp_obj_uv_draw)
                    bpy.ops.view3d.localview()  # Isolates selected
                self.report(
                    {"INFO"},
                    "Switched to Top Ortho, framed selection, and entered Local View.",
                )
                # Switch back to GP Draw mode after view ops
                context.view_layer.objects.active = gp_obj_uv_draw
                if gp_obj_uv_draw.mode != "PAINT_GREASE_PENCIL":
                    bpy.ops.object.mode_set(mode="PAINT_GREASE_PENCIL")

                # Deselect the UV mesh after framing but keep it in local view
                ob_uv.select_set(False)

                # Lock the UV mesh item to prevent selection
                ob_uv.hide_select = True

            else:
                self.report(
                    {"WARNING"}, "Active space in 3D View area is not 'VIEW_3D'."
                )
        else:
            self.report({"WARNING"}, "Could not find 3D View area/region to set view.")

        self.report(
            {"INFO"},
            f"Created UV Mesh '{ob_uv.name}' and GP Layer '{gp_obj_uv_draw.name}'. Ready for UV drawing.",
        )
        return {"FINISHED"}


# Registration
classes = [
    OBJECT_OT_UVToMesh,
]


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
