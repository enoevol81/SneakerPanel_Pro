import math

import bmesh
import bpy
from bpy.props import BoolProperty
from bpy.types import Operator
from mathutils import Vector

from ..utils.collections import add_object_to_panel_collection


def convert_object_to_mesh(obj, apply_modifiers=True, preserve_status=True):
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
    bl_idname = "object.uv_to_mesh"
    bl_label = "UV to Mesh and Prep for Drawing"
    bl_description = "Creates UV Mesh, adds Grease Pencil, isolates, frames, and sets view for drawing."
    bl_options = {"REGISTER", "UNDO"}

    apply_modifiers: BoolProperty(
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
        source_object_from_scene = context.scene.spp_shell_object
        if not source_object_from_scene:
            self.report({"ERROR"}, "No 'Shell Object' defined in Scene Properties.")
            return {"CANCELLED"}
        if source_object_from_scene.type != "MESH":
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

        # Switch to Object Mode if not already there
        if context.mode != "OBJECT":
            try:
                bpy.ops.object.mode_set(mode="OBJECT")
            except Exception as e:
                self.report({"ERROR"}, f"Could not switch to Object Mode: {str(e)}")
                return {"CANCELLED"}

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

        area_3d = 0
        bm = bmesh.new()
        polygons_to_process = me0_from_conversion.polygons
        if not polygons_to_process:
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

        # Apply Reference Image material if toggle is enabled and material exists
        if getattr(context.scene, "spp_use_reference_image_overlay", False):
            ref_material = bpy.data.materials.get("Reference Image")
            if ref_material:
                # Create a duplicate material specifically for UV mesh with proper scaling
                uv_material_name = f"Reference Image UV - {ob_uv.name}"
                uv_material = bpy.data.materials.get(uv_material_name)
                if uv_material:
                    bpy.data.materials.remove(uv_material)

                # Duplicate the original reference material
                uv_material = ref_material.copy()
                uv_material.name = uv_material_name

                # Modify the material for UV mesh - remove projection mapping and use direct UV
                if uv_material.use_nodes:
                    nodes = uv_material.node_tree.nodes
                    links = uv_material.node_tree.links

                    # Find the main UV node and image texture node
                    uv_node = nodes.get("SPP_MainUV")
                    image_node = nodes.get("SPP_BakedImage")
                    bsdf = nodes.get("Principled BSDF")

                    if uv_node and image_node:
                        # Remove any existing mapping/transform nodes between UV and image
                        for link in list(image_node.inputs["Vector"].links):
                            links.remove(link)

                        # Connect UV directly to image texture for 1:1 mapping
                        links.new(uv_node.outputs["UV"], image_node.inputs["Vector"])

                        # Update UV node to use the UV mesh's UV layer
                        uv_node.uv_map = "UVMap"

                    # Set up transparency for opacity control
                    if bsdf:
                        # Enable transparency
                        uv_material.blend_method = "BLEND"
                        uv_material.use_backface_culling = False

                        # Set initial opacity from scene property
                        initial_opacity = getattr(
                            context.scene, "spp_reference_image_opacity", 0.5
                        )
                        bsdf.inputs["Alpha"].default_value = initial_opacity

                        # Connect image alpha to BSDF alpha if not already connected
                        if image_node and not bsdf.inputs["Alpha"].is_linked:
                            if "Alpha" in image_node.outputs:
                                # Create a math node to multiply image alpha with opacity
                                math_node = nodes.new("ShaderNodeMath")
                                math_node.operation = "MULTIPLY"
                                math_node.location = (
                                    image_node.location.x + 200,
                                    image_node.location.y - 200,
                                )
                                math_node.inputs[1].default_value = initial_opacity

                                links.new(
                                    image_node.outputs["Alpha"], math_node.inputs[0]
                                )
                                links.new(
                                    math_node.outputs["Value"], bsdf.inputs["Alpha"]
                                )

                # Clear existing materials and apply the UV-specific material
                ob_uv.data.materials.clear()
                ob_uv.data.materials.append(uv_material)

                # Create UV coordinates for the UV mesh so material can display properly
                # The UV mesh vertices are positioned at UV coordinates, so we create a 1:1 UV mapping
                if not ob_uv.data.uv_layers:
                    uv_layer = ob_uv.data.uv_layers.new(name="UVMap")
                else:
                    uv_layer = ob_uv.data.uv_layers[0]

                # Set UV coordinates to match vertex positions, accounting for applied scale factor
                for face in ob_uv.data.polygons:
                    for loop_idx in face.loop_indices:
                        loop = ob_uv.data.loops[loop_idx]
                        vert = ob_uv.data.vertices[loop.vertex_index]
                        # Account for the scale factor that was applied to the mesh
                        # Divide by scale factor to get back to original UV space (0-1 range)
                        uv_x = vert.co.x / calculated_scale_factor
                        uv_y = vert.co.y / calculated_scale_factor
                        uv_layer.data[loop_idx].uv = (uv_x, uv_y)

                # Change display mode to solid so material is visible, but keep wireframe
                ob_uv.display_type = "SOLID"
                if hasattr(ob_uv, "show_wire"):
                    ob_uv.show_wire = True  # Keep wireframe overlay visible
                if hasattr(ob_uv, "show_all_edges"):
                    ob_uv.show_all_edges = True

                self.report(
                    {"INFO"},
                    f"Applied UV-specific Reference Image material '{uv_material.name}' with proper mapping.",
                )
            else:
                self.report(
                    {"WARNING"},
                    "Reference Image material not found. Create reference image projection first.",
                )
        else:
            # Keep original wireframe display when not using reference image
            ob_uv.display_type = "WIRE"
            if hasattr(ob_uv, "show_wire"):
                ob_uv.show_wire = True
            if hasattr(ob_uv, "show_all_edges"):
                ob_uv.show_all_edges = True

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

        self.report({"INFO"}, "Creating Grease Pencil object for UV drawing.")
        gp_location = ob_uv.location

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
