import bpy
from ..utils import icons


class OBJECT_PT_SurfaceWorkflow(bpy.types.Panel):
    """Surface Direct Workflow [3D] — core, linear (no Q&D here)."""

    bl_label = "Surface Direct Workflow [3D]"
    bl_idname = "OBJECT_PT_surface_workflow"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sneaker Panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        layout = self.layout
        icon_id = icons.get_icon("3d")
        layout.label(text="", icon_value=icon_id)

    @classmethod
    def poll(cls, context):
        return getattr(context.window_manager, "spp_active_workflow", "") == "SURFACE_3D"

    def draw(self, context):
        layout = self.layout
        S = context.scene
        W = context.window_manager

        surface_box = layout.box()
        surface_header = surface_box.row(align=True)

        # Panel header
        surface_header.label(text="Draw Direct To Shell", icon_value=icons.get_icon("3d"))

        # Tooltip icon
        icon = "LIGHT_SUN" if getattr(context.scene, "spp_show_surface_workflow_tooltip", False) else "INFO"
        if hasattr(context.scene, "spp_show_surface_workflow_tooltip"):
            surface_header.prop(context.scene, "spp_show_surface_workflow_tooltip", text="", toggle=True, icon=icon)

        # Tooltip body
        if getattr(context.scene, "spp_show_surface_workflow_tooltip", False):
            tip_box = surface_box.box()
            tip_box.alert = True
            tip_col = tip_box.column(align=True)
            tip_col.scale_y = 0.9
            tip_col.label(text="Surface Workflow Tips:", icon="HELP")
            tip_col.label(text="• Use Stabilizer for pencil control")
            tip_col.operator("wm.url_open", text="View Surface Workflow Tutorial", icon="URL").url = "https://example.com/surface-workflow-tutorial"

        # ---------- Step 1: Create Grease Pencil ----------
        step1 = surface_box.box()
        hdr1 = step1.row(align=True)
        hdr1.prop(W, "spp_show_surface_step_1", toggle=True, text="Step 1: Create Grease Pencil – Design Your Panel", icon="GREASEPENCIL")

        if W.spp_show_surface_step_1:
            col = step1.column(align=True); col.scale_y = 1.1
            col.operator("object.add_gp_draw", text="Create Grease Pencil", icon="OUTLINER_OB_GREASEPENCIL")

            # Stabilizer (collapsible)
            stab = step1.box()
            r = stab.row(align=True)
            r.prop(S, "spp_show_stabilizer_settings", toggle=True, text="Stabilizer Settings", icon="TRIA_DOWN" if getattr(S, "spp_show_stabilizer_settings", False) else "TRIA_RIGHT")
            
            if getattr(S, "spp_show_stabilizer_settings", False):
                stab_content = stab.column(align=True)
                if hasattr(S, "spp_use_stabilizer"):
                    stab_content.prop(S, "spp_use_stabilizer", text="Use Stabilizer")
                if getattr(S, "spp_use_stabilizer", False):
                    if hasattr(S, "spp_stabilizer_radius"):
                        stab_content.prop(S, "spp_stabilizer_radius", text="Radius")
                    if hasattr(S, "spp_stabilizer_strength_ui"):
                        stab_content.prop(S, "spp_stabilizer_strength_ui", text="Strength")

        # ---------- Step 2: Create & Edit Curve ----------
        step2 = surface_box.box()
        hdr2 = step2.row(align=True)
        hdr2.prop(W, "spp_show_surface_step_2", toggle=True, text="Step 2: Create & Edit Curve", icon="OUTLINER_OB_CURVE")

        if W.spp_show_surface_step_2:
            col = step2.column(align=True); col.scale_y = 1.1
            col.operator("object.gp_to_curve", text="Convert to Curve", icon="IPO_BEZIER")

            # Curve Editing Tools (collapsible)
            tools = step2.box()
            tools_header = tools.row(align=True)
            tools_header.prop(S, "spp_show_curve_editing_tools", toggle=True, text="Curve Editing Tools", icon="TRIA_DOWN" if getattr(S, "spp_show_curve_editing_tools", False) else "TRIA_RIGHT")
            
            if getattr(S, "spp_show_curve_editing_tools", False):
                # Step 2a – Decimate
                dec = tools.column(align=True)
                dec.label(text="Decimate Curve:", icon="MOD_DECIM")
                r = dec.row(align=True)
                if hasattr(S, "spp_decimate_ratio"):
                    r.prop(S, "spp_decimate_ratio", text="Ratio")
                r.operator("object.decimate_curve", text="Apply", icon="CHECKMARK")

                # Curve options + mirror tooltip
                opts = tools.column(align=True)
                rr = opts.row(align=True)

                left_split = rr.split(factor=0.7, align=True)
                left_row = left_split.row(align=True)
                if hasattr(S, "spp_curve_cyclic"):
                    left_row.prop(S, "spp_curve_cyclic", text="")
                left_row.label(text="Cyclic Curve")

                right_split = left_split.row(align=True)
                right_split.alignment = 'RIGHT'
                icon = 'LIGHT_SUN' if getattr(context.scene, "spp_show_mirror_tooltip", False) else 'INFO'
                if hasattr(context.scene, "spp_show_mirror_tooltip"):
                    right_split.prop(context.scene, "spp_show_mirror_tooltip", text="", toggle=True, icon=icon)

                if getattr(context.scene, "spp_show_mirror_tooltip", False):
                    tip_box = tools.box(); tip_box.alert = True
                    tip_col = tip_box.column(align=True); tip_col.scale_y = 0.9
                    tip_col.label(text="Mirror Curve Tips:", icon="HELP")
                    tip_col.label(text="• Mirror curve in edit mode")
                    tip_col.label(text="• Mirror curve in object mode")
                    tip_col.operator("wm.url_open", text="View Mirror Curve Tutorial", icon="URL").url = "https://example.com/mirror_curve-tutorial"

                # Step 2b – Mirror (Edit Mode)
                mir = tools.column(align=True)
                mir.operator("curve.mirror_selected_points_at_cursor", text="Mirror Curve", icon="MOD_MIRROR")

        # ---------- Step 3: Sample Curve to Polyline ----------
        step3 = surface_box.box()
        hdr3 = step3.row(align=True)
        hdr3.prop(W, "spp_show_surface_step_3", toggle=True, text="Step 3: Sample Curve to Polyline", icon="CURVE_DATA")

        if W.spp_show_surface_step_3:
            if hasattr(S, "spp_sampler_fidelity"):
                step3.column(align=True).prop(S, "spp_sampler_fidelity", text="Boundary Samples")
            row = step3.row(align=True); row.scale_y = 1.2
            row.operator("curve.sample_to_polyline", text="Sample Curve to Polyline", icon="CURVE_BEZCURVE")

        # ---------- Step 4: Fill Border with Grid ----------
        step4 = surface_box.box()
        hdr4 = step4.row(align=True)
        hdr4.prop(W, "spp_show_surface_step_4", toggle=True, text="Step 4: Fill Border with Grid", icon="GRID")

        if W.spp_show_surface_step_4:
            fill_row = step4.row(align=True); fill_row.scale_y = 1.2
            fill_row.operator("mesh.simple_grid_fill", text="Fill Panel Border", icon="MOD_TRIANGULATE")
            smooth_row = step4.row(align=True)
            smooth_row.operator("mesh.smooth_mesh", text="Smooth Mesh (Optional)", icon="MOD_SMOOTH")

           

classes = [OBJECT_PT_SurfaceWorkflow]


def register():
    from bpy.utils import register_class
    for cls in classes:
        try:
            register_class(cls)
        except Exception:
            pass


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        try:
            unregister_class(cls)
        except Exception:
            pass
