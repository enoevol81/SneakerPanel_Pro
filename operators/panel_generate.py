"""
Generate filled panels from outline meshes — merged operator + utilities.

This module merges the previous split:
- `object.panel_generate` operator (formerly in panel_generate.py)
- Utility functions (formerly in panel_generator.py)

Backwards compatibility:
- `panel_generator.py` remains as a thin shim re-exporting `generate_panel`
  from this module so any legacy imports continue to work.
"""

import bmesh
import bpy
from mathutils import Vector

from ..utils.collections import add_object_to_panel_collection

# ------------------------------
# Utilities (previously panel_generator.py)
# ------------------------------


def info(msg: str):
    print(f"[PANEL GENERATOR] {msg}")


def error(msg: str):
    print(f"[PANEL GENERATOR ERROR] {msg}")


def get_boundary_verts(bm: bmesh.types.BMesh):
    """Return ordered boundary BMVerts (single-face edges)."""
    boundary_edges = [e for e in bm.edges if len(e.link_faces) < 2]
    if not boundary_edges:
        return []
    verts = []
    visited_edges = set()
    first_edge = boundary_edges[0]
    current = first_edge.verts[0]
    start = current
    while True:
        verts.append(current)
        next_edge = None
        for edge in current.link_edges:
            if edge in boundary_edges and edge not in visited_edges:
                next_edge = edge
                visited_edges.add(edge)
                break
        if not next_edge:
            break
        current = next_edge.other_vert(current)
        if current == start:
            break
    return verts


def project_verts_to_surface(obj, vert_indices, shell_obj):
    """Project selected boundary vertices to target shell via Shrinkwrap."""
    info(f"Projecting {len(vert_indices)} boundary vertices for {obj.name}.")
    if not vert_indices:
        info("No vertex indices provided for projection.")
        return
    try:
        if obj.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        for v in obj.data.vertices:
            v.select = False
        valid = 0
        for idx in vert_indices:
            if idx < len(obj.data.vertices):
                obj.data.vertices[idx].select = True
                valid += 1
            else:
                error(
                    f"Invalid vertex index {idx} for object {obj.name} in project_verts_to_surface."
                )
        if valid == 0:
            info("No valid vertices were selected for projection.")
            return
        vg_name = "TempProjectionGroup"
        if vg_name in obj.vertex_groups:
            obj.vertex_groups.remove(obj.vertex_groups[vg_name])
        vg = obj.vertex_groups.new(name=vg_name)

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.object.vertex_group_assign()
        bpy.ops.object.mode_set(mode="OBJECT")

        mod = obj.modifiers.new(name="TempShrinkwrap", type="SHRINKWRAP")
        mod.target = shell_obj
        mod.wrap_method = "NEAREST_SURFACEPOINT"
        mod.vertex_group = vg_name
        mod.offset = 0.0001

        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        info(f"Applied shrinkwrap to {valid} vertices.")

        if vg_name in obj.vertex_groups:
            obj.vertex_groups.remove(obj.vertex_groups[vg_name])
            info(f"Removed temporary vertex group '{vg_name}'.")
    except Exception as e:
        error(f"Error in project_verts_to_surface: {str(e)}")
        if "mod" in locals() and mod.name in obj.modifiers:  # type: ignore
            obj.modifiers.remove(mod)  # type: ignore
        if "vg_name" in locals() and vg_name in obj.vertex_groups:  # type: ignore
            obj.vertex_groups.remove(obj.vertex_groups[vg_name])  # type: ignore


def apply_surface_snap(obj_to_snap, target_shell_obj, iterations=1):
    """Iteratively shrinkwrap whole object to the shell (gentle conform)."""
    info(
        f"Applying iterative Shrinkwrap snap to '{obj_to_snap.name}' targeting '{target_shell_obj.name}'."
    )
    try:
        original_active = bpy.context.view_layer.objects.active
        original_selected_objects = bpy.context.selected_objects[:]
        for i in range(iterations):
            mod = None
            try:
                mod = obj_to_snap.modifiers.new(name=f"TempSnap_{i}", type="SHRINKWRAP")
                mod.target = target_shell_obj
                mod.wrap_method = "NEAREST_SURFACEPOINT"
                mod.offset = 0.0001
                bpy.ops.object.select_all(action="DESELECT")
                obj_to_snap.select_set(True)
                bpy.context.view_layer.objects.active = obj_to_snap
                bpy.ops.object.modifier_apply(modifier=mod.name)
                info(
                    f"Shrinkwrap snap iteration {i+1} applied to '{obj_to_snap.name}'."
                )
            except RuntimeError as e:
                error(
                    f"Shrinkwrap snap iteration {i+1} failed for '{obj_to_snap.name}': {e}"
                )
                if mod and mod.name in obj_to_snap.modifiers:
                    obj_to_snap.modifiers.remove(mod)
                break
            except Exception as e:
                error(
                    f"Unexpected error in Shrinkwrap snap iteration {i+1} for '{obj_to_snap.name}': {e}"
                )
                if mod and mod.name in obj_to_snap.modifiers:
                    obj_to_snap.modifiers.remove(mod)
                break
        bpy.ops.object.select_all(action="DESELECT")
        for o in original_selected_objects:
            if o and o.name in bpy.data.objects:
                o.select_set(True)
        if original_active and original_active.name in bpy.data.objects:
            bpy.context.view_layer.objects.active = original_active
        elif (
            bpy.context.view_layer.objects.active != obj_to_snap
            and obj_to_snap.name in bpy.data.objects
        ):
            bpy.context.view_layer.objects.active = obj_to_snap
    except Exception as e:
        error(f"Error in apply_surface_snap: {str(e)}")


def create_flow_based_quads(bm: bmesh.types.BMesh):
    """Recalc normals + smooth verts to encourage quad flow."""
    try:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for _ in range(3):
            bmesh.ops.smooth_vert(bm, verts=bm.verts, factor=0.5)
    except Exception as e:
        error(f"Flow-based quad op failed: {e}")
    return bm


def generate_panel(
    panel_obj, shell_obj, filled_obj_name=None, grid_span=4, uv_layer_name="UVMap"
):
    """Generate a filled panel mesh from outline + conform to shell."""
    info("Starting panel generation.")
    try:
        if not panel_obj:
            error("Input panel object not provided.")
            return None
        if not shell_obj:
            error("Shell object not provided.")
            return None
        if panel_obj.type != "MESH":
            error(f"Input panel object {panel_obj.name} is not a mesh.")
            return None
        if shell_obj.type != "MESH":
            error(f"Shell object {shell_obj.name} is not a mesh.")
            return None

        if bpy.context.object and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        # Duplicate working copy
        bpy.ops.object.select_all(action="DESELECT")
        panel_obj.select_set(True)
        bpy.context.view_layer.objects.active = panel_obj
        bpy.ops.object.duplicate()
        filled_obj = bpy.context.active_object
        filled_obj.name = (
            filled_obj_name if filled_obj_name else f"{panel_obj.name}_Filled"
        )
        info(f"Duplicated to '{filled_obj.name}'.")
        if filled_obj.type != "MESH":
            error("Duplicate is not a mesh.")
            return None

        # Store original boundary
        bpy.ops.object.mode_set(mode="OBJECT")
        bm_orig = bmesh.new()
        bm_orig.from_mesh(filled_obj.data)
        orig_boundary_verts = get_boundary_verts(bm_orig)
        orig_boundary_coords = [v.co.copy() for v in orig_boundary_verts]
        bm_orig.free()
        info(f"Stored {len(orig_boundary_coords)} original boundary vertex positions.")
        if len(orig_boundary_coords) < 3:
            error("Invalid boundary after preprocessing: Not enough vertices.")
            return None

        # Grid fill
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        try:
            bpy.ops.mesh.fill_grid(span=grid_span if grid_span > 0 else 1)
            info(f"Grid fill succeeded with span={grid_span}.")
        except Exception as e:
            error(f"Grid fill failed: {e}")
            bpy.ops.object.mode_set(mode="OBJECT")
            return None
        bpy.ops.object.mode_set(mode="OBJECT")

        # Restore boundary coords
        bm_new = bmesh.new()
        bm_new.from_mesh(filled_obj.data)
        new_boundary_verts = get_boundary_verts(bm_new)
        if len(new_boundary_verts) == len(orig_boundary_coords):
            for bm_v, orig_co in zip(new_boundary_verts, orig_boundary_coords):
                bm_v.co = orig_co
            info("Restored original boundary positions after grid fill.")
        else:
            error(
                f"Boundary vertex count mismatch after grid fill "
                f"({len(new_boundary_verts)} vs {len(orig_boundary_coords)}); "
                "could not reliably restore outline coordinates."
            )
        bm_new.to_mesh(filled_obj.data)
        bm_new.free()
        filled_obj.data.update()

        # Project boundary verts
        bm_sel = bmesh.new()
        bm_sel.from_mesh(filled_obj.data)
        boundary_indices = [v.index for v in get_boundary_verts(bm_sel)]
        bm_sel.free()
        if boundary_indices:
            project_verts_to_surface(filled_obj, boundary_indices, shell_obj)
        else:
            info("No boundary vertices found to project.")

        # Encourage quad flow + set basic UVs
        bm_flow = bmesh.new()
        bm_flow.from_mesh(filled_obj.data)
        bm_flow = create_flow_based_quads(bm_flow)
        if not filled_obj.data.uv_layers:
            filled_obj.data.uv_layers.new(name=uv_layer_name)
        uv_layer = bm_flow.loops.layers.uv.verify()
        for face in bm_flow.faces:
            for loop in face.loops:
                co = loop.vert.co
                loop[uv_layer].uv = (co.x, co.y)  # placeholder UVs
        bm_flow.to_mesh(filled_obj.data)
        filled_obj.data.update()
        bm_flow.free()
        info("UVs assigned and mesh updated from flow_based_quads.")

        # Light relax + global conform
        bpy.context.view_layer.objects.active = filled_obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.vertices_smooth(factor=0.5)
        bpy.ops.object.mode_set(mode="OBJECT")
        apply_surface_snap(filled_obj, shell_obj, iterations=3)

        info("Panel generation complete!")
        return filled_obj
    except Exception as e:
        error(f"Error in generate_panel: {str(e)}")
        return None


# ------------------------------
# Operator (previously panel_generate.py)
# ------------------------------


class OBJECT_OT_PanelGenerate(bpy.types.Operator):
    """Generate a filled panel mesh from an outline (uses merged utilities)."""

    bl_idname = "object.panel_generate"
    bl_label = "Generate Panel"
    bl_description = "Generate a filled panel mesh from an outline"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (
            hasattr(context.scene, "spp_shell_object")
            and context.scene.spp_shell_object
            and context.scene.spp_shell_object.type == "MESH"
        )

    def execute(self, context):
        bpy.ops.ed.undo_push(message="Generate Panel")
        panel_count = getattr(context.scene, "spp_panel_count", 1)
        panel_name = getattr(context.scene, "spp_panel_name", "Panel")

        if panel_name and panel_name.strip():
            PANEL_OBJ_NAME_PREFIX = f"{panel_name}_Mesh"
            FILLED_OBJ_NAME = f"{panel_name}_Filled_{panel_count}"
        else:
            PANEL_OBJ_NAME_PREFIX = "PanelMesh"
            FILLED_OBJ_NAME = f"PanelMesh_Filled_{panel_count}"

        shell = (
            context.scene.spp_shell_object
            if getattr(context.scene, "spp_shell_object", None)
            else None
        )
        if not shell:
            self.report({"ERROR"}, "Shell object not set.")
            return {"CANCELLED"}
        UV_LAYER_NAME = "UVMap"

        try:
            if bpy.context.object and bpy.context.object.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")

            shell_obj = bpy.data.objects.get(shell.name)
            if not shell_obj:
                self.report({"ERROR"}, f"Shell object {shell.name} not found.")
                return {"CANCELLED"}

            panel_obj = None
            possible_names = [
                f"{PANEL_OBJ_NAME_PREFIX}_{panel_count}",
                f"PanelMesh_{panel_count}",
                f"{panel_name}_Mesh_{panel_count}",
            ]

            mesh_objects = [obj.name for obj in bpy.data.objects if obj.type == "MESH"]
            self.report({"INFO"}, f"Available mesh objects: {', '.join(mesh_objects)}")
            self.report(
                {"INFO"}, f"Looking for panel with names: {', '.join(possible_names)}"
            )

            for name in possible_names:
                obj = bpy.data.objects.get(name)
                if obj:
                    panel_obj = obj
                    self.report({"INFO"}, f"Found panel object: {name}")
                    break

            if not panel_obj:
                for obj in bpy.data.objects:
                    if obj.type == "MESH":
                        if (
                            obj.name.startswith(PANEL_OBJ_NAME_PREFIX)
                            or obj.name.startswith(f"{panel_name}_Mesh")
                            or obj.name.startswith("PanelMesh")
                        ):
                            panel_obj = obj
                            self.report({"INFO"}, f"Found panel by prefix: {obj.name}")
                            break

            if not panel_obj:
                self.report(
                    {"ERROR"},
                    f"Panel mesh not found. Tried names: {', '.join(possible_names)}",
                )
                return {"CANCELLED"}

            grid_span = getattr(context.scene, "spp_grid_fill_span", 4)
            filled_obj = generate_panel(
                panel_obj=panel_obj,
                shell_obj=shell_obj,
                filled_obj_name=FILLED_OBJ_NAME,
                grid_span=grid_span,
                uv_layer_name=UV_LAYER_NAME,
            )

            if not filled_obj:
                self.report(
                    {"ERROR"}, "Panel generation failed. Check console for details."
                )
                return {"CANCELLED"}

            add_object_to_panel_collection(filled_obj, panel_count, panel_name)

            if panel_obj:
                panel_obj.hide_viewport = True
                self.report({"INFO"}, f"Hidden input mesh: {panel_obj.name}")

            bpy.ops.object.select_all(action="DESELECT")
            filled_obj.select_set(True)
            bpy.context.view_layer.objects.active = filled_obj

            if hasattr(context.scene, "spp_panel_count"):
                context.scene.spp_panel_count += 1

            self.report({"INFO"}, f"✅ Flattened and filled: {FILLED_OBJ_NAME}")
        except Exception as e:
            self.report({"ERROR"}, f"Error generating panel: {str(e)}")
            return {"CANCELLED"}

        return {"FINISHED"}


# ------------------------------
# Registration
# ------------------------------
classes = [OBJECT_OT_PanelGenerate]


def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception:
            pass


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass


if __name__ == "__main__":
    register()
