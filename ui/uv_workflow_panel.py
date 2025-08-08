"""UV Workflow UI panel for the Sneaker Panel Pro addon."""
import bpy
from bpy.types import Panel

def register_properties():
    S = bpy.types.Scene
    def add(name, prop):
        if not hasattr(S, name):
            setattr(S, name, prop)
    add("spp_workflow_a_expanded", bpy.props.BoolProperty(default=True))
    add("spp_workflow_b_expanded", bpy.props.BoolProperty(default=True))
    add("spp_show_workflow_a_tooltip", bpy.props.BoolProperty(default=False))
    add("spp_show_workflow_b_tooltip", bpy.props.BoolProperty(default=False))
    add("spp_uv_boundary_action", bpy.props.EnumProperty(
        name="Boundary Action",
        items=[('CHECK',"Check Only",""),('FIX',"Fix Vertices",""),('INTERACTIVE',"Select for Manual Fix","")],
        default='CHECK'
    ))
    add("spp_uv_boundary_samples", bpy.props.IntProperty(default=10, min=3, max=50))
    add("spp_uv_boundary_margin", bpy.props.FloatProperty(default=0.01, min=0.0, max=0.1))
    add("spp_uv_boundary_status", bpy.props.EnumProperty(
        items=[('NONE',"Not Checked",""),('PASS',"Pass",""),('VIOLATIONS',"Violations Found",""),('ERROR',"Error","")],
        default='NONE'
    ))

def unregister_properties():
    S = bpy.types.Scene
    for name in ("spp_workflow_a_expanded","spp_workflow_b_expanded",
                 "spp_show_workflow_a_tooltip","spp_show_workflow_b_tooltip",
                 "spp_uv_boundary_action","spp_uv_boundary_samples",
                 "spp_uv_boundary_margin","spp_uv_boundary_status"):
        if hasattr(S, name): delattr(S, name)

class OBJECT_PT_UVWorkflow(Panel):
    bl_label = "UV Workflow [2D]"
    bl_idname = "OBJECT_PT_uv_workflow"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'
    bl_order = 2

    @classmethod
    def poll(cls, context):
        return context.window_manager.spp_active_workflow == 'UV_2D'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Step 1: UV to Mesh
        box = layout.box()
        box.label(text="UV to Mesh (Auto Add Grease Pencil Object):", icon='UV')
        row = box.row()
        row.operator("object.uv_to_mesh", icon='MESH_DATA')

        # ----- UI v2: Step 2: Create & Edit Curve (UV) -----
        curve_box = layout.box()
        curve_header = curve_box.row()
        curve_header.label(text="Step 2: Create & Edit Curve", icon='OUTLINER_OB_CURVE')

        curve_col = curve_box.column(align=True); curve_col.scale_y = 1.1
        curve_col.operator("object.gp_to_curve", text="Convert to Curve", icon='IPO_BEZIER')

        curve_tools_box = curve_box.box()
        curve_tools_box.label(text="Curve Editing Tools", icon="TOOL_SETTINGS")

        # Decimate
        decimate_col = curve_tools_box.column(align=True)
        decimate_col.label(text="Decimate Curve:", icon="MOD_DECIM")
        decimate_row = decimate_col.row(align=True)
        decimate_row.prop(scene, "spp_decimate_ratio", text="Ratio")
        decimate_row.operator("object.decimate_curve", text="Apply", icon='CHECKMARK')

        # Options
        opts_col = curve_tools_box.column(align=True)
        opts_col.label(text="Curve Options:", icon="CURVE_DATA")
        cyclic_row = opts_col.row()
        cyclic_row.prop(scene, "spp_curve_cyclic", text="")
        cyclic_row.label(text="Cyclic Curve")

        # Mirror
        mirror_col = curve_tools_box.column(align=True)
        mirror_header = mirror_col.row(align=True)
        mirror_header.label(text="Mirror Tools (Edit Mode):", icon="MOD_MIRROR")
        tooltip_icon = 'LIGHT_SUN' if getattr(scene, "spp_show_mirror_tooltip", False) else 'LIGHT'
        mirror_header.prop(scene, "spp_show_mirror_tooltip", text="", icon=tooltip_icon, emboss=False)
        mirror_col.operator("curve.mirror_selected_points_at_cursor", text="Mirror at Cursor", icon="CURVE_BEZCIRCLE")

        # ===== Existing UV Workflows =====
        # Workflow A
        box_workflow_a = layout.box()
        row = box_workflow_a.row()
        op_workflow_a = row.operator("wm.context_toggle_workflow", text="",
                 icon="TRIA_DOWN" if scene.spp_workflow_a_expanded else "TRIA_RIGHT", emboss=True)
        op_workflow_a.toggle_prop = "spp_workflow_a_expanded"
        op_workflow_a.other_prop = "spp_workflow_b_expanded"
        row.label(text="UV Curve to Panel - Quick & Dirty", icon='UV_VERTEXSEL')

        if scene.spp_workflow_a_expanded:
            # (existing boundary checker + shell UV to panel, refinement, etc.)
            box_boundary = box_workflow_a.box()
            boundary_header = box_boundary.row()
            boundary_header.label(text="UV Boundary Check (Recommended):", icon='CHECKMARK')
            action_row = box_boundary.row(align=True)
            action_row.prop(scene, "spp_uv_boundary_action", text="Action")
            boundary_op_row = box_boundary.row(align=True); boundary_op_row.scale_y = 1.2
            boundary_op_row.operator("mesh.check_uv_boundary", text="Check UV Boundary", icon='ZOOM_SELECTED')

            status_row = box_boundary.row(align=True); status_row.scale_y = 0.9
            status = getattr(scene, "spp_uv_boundary_status", 'NONE')
            if status == 'PASS': status_row.label(text="Status: PASS - No Violations", icon='CHECKMARK')
            elif status == 'VIOLATIONS': status_row.alert = True; status_row.label(text="Status: VIOLATIONS - Found Issues", icon='ERROR')
            elif status == 'ERROR': status_row.alert = True; status_row.label(text="Status: ERROR - Check Failed", icon='CANCEL')
            else: status_row.enabled = False; status_row.label(text="Status: NONE - Not Checked", icon='QUESTION')

            if context.active_object and context.active_object.type == 'MESH':
                has_violations = any(vg.name.startswith("UV_Violation_") for vg in context.active_object.vertex_groups)
                if has_violations:
                    reselect_row = box_boundary.row(align=True)
                    reselect_row.operator("mesh.reselect_uv_violations", text="Re-select Violations", icon='RESTRICT_SELECT_OFF')

            box = box_workflow_a.box()
            box.label(text=" Step 5. Shell UV to Panel:", icon='MODIFIER')
            row = box.row(); row.operator("object.shell_uv_to_panel", icon='MOD_SOLIDIFY')

            box_post = box_workflow_a.box()
            box_post.label(text="Panel Refinement Options:")
            box_post.prop(scene, "spp_grid_fill_span", text="Initial Grid Fill Span")
            row = box_post.row(); row.prop(scene, "spp_panel_add_subdivision", text="Add Subdivision")
            row_sub = box_post.row(align=True); row_sub.enabled = getattr(scene, "spp_panel_add_subdivision", False)
            row_sub.prop(scene, "spp_panel_subdivision_levels", text="Levels")
            row_sub.prop(scene, "spp_panel_conform_after_subdivision", text="Re-Conform")
            box_post.prop(scene, "spp_panel_shade_smooth", text="Shade Smooth")

        # Workflow B
        box_workflow_b = layout.box()
        header_row = box_workflow_b.row(align=True)
        op_workflow_b = header_row.operator("wm.context_toggle_workflow", text="",
                 icon="TRIA_DOWN" if scene.spp_workflow_b_expanded else "TRIA_RIGHT", emboss=True)
        op_workflow_b.toggle_prop = "spp_workflow_b_expanded"
        op_workflow_b.other_prop = "spp_workflow_a_expanded"
        header_row.label(text="2D Quad Mesh to Panel - Advanced", icon='MOD_LATTICE')

        if scene.spp_workflow_b_expanded:
            box_sample = box_workflow_b.box()
            sample_header = box_sample.row()
            sample_header.label(text="Step 5: Sample Curve to Polyline", icon='CURVE_DATA')
            if hasattr(scene, "spp_sampler_fidelity"):
                col_sample = box_sample.column(align=True)
                col_sample.prop(scene, "spp_sampler_fidelity", text="Boundary Samples")
                sample_row = col_sample.row(align=True); sample_row.scale_y = 1.2
                sample_row.operator("curve.sample_to_polyline", text="Sample Curve to Polyline", icon='CURVE_BEZCURVE')

            box_create = box_workflow_b.box()
            border_header = box_create.row()
            border_header.label(text="Step 6: Create Quad Panel Border", icon='MESH_GRID')
            border_row = box_create.row(align=True); border_row.scale_y = 1.2
            border_row.operator("mesh.create_quad_panel_from_outline", text="Create Quad Border from Outline", icon='OUTLINER_OB_MESH')

            box_fill = box_workflow_b.box()
            fill_header = box_fill.row()
            fill_header.label(text="Step 7: Fill Border with Grid", icon='GRID')
            fill_row = box_fill.row(align=True); fill_row.scale_y = 1.2
            fill_row.operator("mesh.fill_border_grid", text="Fill Panel Border", icon='MOD_TRIANGULATE')

            # Boundary check again before projection
            box_boundary = box_workflow_b.box()
            boundary_header = box_boundary.row()
            boundary_header.label(text="UV Boundary Check (Recommended):", icon='CHECKMARK')
            action_row = box_boundary.row(align=True)
            action_row.prop(scene, "spp_uv_boundary_action", text="Action")
            boundary_op_row = box_boundary.row(align=True); boundary_op_row.scale_y = 1.2
            boundary_op_row.operator("mesh.check_uv_boundary", text="Check UV Boundary", icon='ZOOM_SELECTED')

            status_row = box_boundary.row(align=True); status_row.scale_y = 0.9
            status = getattr(scene, "spp_uv_boundary_status", 'NONE')
            if status == 'PASS': status_row.label(text="Status: PASS - No Violations", icon='CHECKMARK')
            elif status == 'VIOLATIONS': status_row.alert = True; status_row.label(text="Status: VIOLATIONS - Found Issues", icon='ERROR')
            elif status == 'ERROR': status_row.alert = True; status_row.label(text="Status: ERROR - Check Failed", icon='CANCEL')
            else: status_row.enabled = False; status_row.label(text="Status: NONE - Not Checked", icon='QUESTION')

            if context.active_object and context.active_object.type == 'MESH':
                has_violations = any(vg.name.startswith("UV_Violation_") for vg in context.active_object.vertex_groups)
                if has_violations:
                    reselect_row = box_boundary.row(align=True)
                    reselect_row.operator("mesh.reselect_uv_violations", text="Re-select Violations", icon='RESTRICT_SELECT_OFF')

            box_relax = box_workflow_b.box()
            relax_header = box_relax.row()
            relax_header.label(text="Step 9: Relax Loops & Project", icon='MOD_SMOOTH')
            row_proj = box_relax.row(align=True); row_proj.scale_y = 1.2
            row_proj.operator("mesh.overlay_panel_onto_shell", text="Project 2D Panel to 3D Shell", icon='UV_DATA')


from . import workflow_operators

classes = [OBJECT_PT_UVWorkflow]

def register():
    register_properties()
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
    unregister_properties()
