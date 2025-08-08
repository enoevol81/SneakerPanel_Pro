import bpy

def update_active_surface_resolution(self, context):
    obj = context.active_object
    if obj and obj.type == 'SURFACE':
        obj.data.resolution_u = context.scene.spp_resolution_u
        obj.data.resolution_v = context.scene.spp_resolution_v

class OBJECT_PT_SurfaceWorkflow(bpy.types.Panel):
    """Surface Workflow Panel."""
    bl_label = "Surface Direct Workflow [3D]"
    bl_idname = "OBJECT_PT_surface_workflow"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.window_manager.spp_active_workflow == 'SURFACE_3D'

    def draw(self, context):
        layout = self.layout

        # ----- UI v2: Step 1: Create Grease Pencil -----
        gp_box = layout.box()
        gp_header = gp_box.row()
        gp_header.label(text="Step 1: Create Grease Pencil Object - Design Your Panel", icon="GREASEPENCIL")

        tooltip_icon = "LIGHT_SUN" if getattr(context.scene, "spp_show_gp_tooltip", False) else "LIGHT"
        gp_header.prop(context.scene, "spp_show_gp_tooltip", text="", icon=tooltip_icon, emboss=False)

        if getattr(context.scene, "spp_show_gp_tooltip", False):
            tip_box = gp_box.box(); tip_box.alert = True
            tip_col = tip_box.column(align=True); tip_col.scale_y = 0.9
            tip_col.label(text="• Draw directly on the 3D shell surface", icon='HELP')
            tip_col.label(text="• Assign panel name and # first")
            tip_col.label(text="• Use stabilizer for smoother lines")

        gp_col = gp_box.column(align=True); gp_col.scale_y = 1.1
        gp_col.operator("object.add_gp_draw", text="Create Grease Pencil", icon='OUTLINER_OB_GREASEPENCIL')

        # Stabilizer settings
        stab_box = gp_box.box()
        stab_row = stab_box.row()
        stab_row.prop(context.scene, "spp_use_stabilizer", text="")
        stab_row.label(text="Stabilizer Settings")
        if getattr(context.scene, "spp_use_stabilizer", False):
            stab_col = stab_box.column(align=True)
            stab_col.prop(context.scene, "spp_stabilizer_radius", text="Radius")
            stab_col.prop(context.scene, "spp_stabilizer_strength_ui", text="Strength")

        # ----- UI v2: Step 2: Create & Edit Curve -----
        curve_box = layout.box()
        curve_header = curve_box.row()
        curve_header.label(text="Step 2: Create & Edit Curve", icon='OUTLINER_OB_CURVE')

        curve_col = curve_box.column(align=True); curve_col.scale_y = 1.1
        curve_col.operator("object.gp_to_curve", text="Convert to Curve", icon='IPO_BEZIER')

        # Curve Editing Tools
        curve_tools_box = curve_box.box()
        curve_tools_header = curve_tools_box.row()
        curve_tools_header.label(text="Curve Editing Tools", icon="TOOL_SETTINGS")

        # Decimate
        decimate_col = curve_tools_box.column(align=True)
        decimate_col.label(text="Decimate Curve:", icon="MOD_DECIM")
        decimate_row = decimate_col.row(align=True)
        decimate_row.prop(context.scene, "spp_decimate_ratio", text="Ratio")
        decimate_row.operator("object.decimate_curve", text="Apply", icon='CHECKMARK')

        # Options
        curve_options_col = curve_tools_box.column(align=True)
        curve_options_col.label(text="Curve Options:", icon="CURVE_DATA")
        cyclic_row = curve_options_col.row()
        cyclic_row.prop(context.scene, "spp_curve_cyclic", text="")
        cyclic_row.label(text="Cyclic Curve")

        # Mirror
        mirror_col = curve_tools_box.column(align=True)
        mirror_header = mirror_col.row(align=True)
        mirror_header.label(text="Mirror Tools (Edit Mode):", icon="MOD_MIRROR")
        tooltip_icon = 'LIGHT_SUN' if getattr(context.scene, "spp_show_mirror_tooltip", False) else 'LIGHT'
        mirror_header.prop(context.scene, "spp_show_mirror_tooltip", text="", icon=tooltip_icon, emboss=False)
        mirror_col.operator("curve.mirror_selected_points_at_cursor", text="Mirror at Cursor", icon="CURVE_BEZCIRCLE")
        if getattr(context.scene, "spp_show_mirror_tooltip", False):
            tip_box = mirror_col.box(); tip_box.alert = True
            tip_col = tip_box.column(align=True); tip_col.scale_y = 0.9
            tip_col.label(text="• Position 3D cursor at desired mirror axis", icon='HELP')
            tip_col.label(text="• Select points to mirror in Edit Mode")

        # ===== Existing Surface Workflows (unchanged) =====
        self.draw_bezier_workflow(layout, context)
        self.draw_boundary_workflow(layout, context)

    # ------- Existing methods below (unchanged logic) -------
    def draw_bezier_workflow(self, layout, context):
        scene = context.scene
        box = layout.box()
        row = box.row(align=True)
        op_bezier = row.operator("wm.context_toggle_workflow", text="",
                                 icon="TRIA_DOWN" if scene.spp_bezier_workflow_expanded else "TRIA_RIGHT",
                                 emboss=True)
        op_bezier.toggle_prop = "spp_bezier_workflow_expanded"
        op_bezier.other_prop = "spp_boundary_workflow_expanded"
        row.label(text="Bezier to Surface Panel", icon='SURFACE_NSURFACE')

        if scene.spp_bezier_workflow_expanded:
            inner = box.box()
            inner.label(text="Step 3: Generate NURBS Surface", icon='SURFACE_NSURFACE')
            op_bs = inner.operator("spp.convert_bezier_to_surface", text="Convert Bezier to Surface", icon='SURFACE_DATA')
            op_bs.center = scene.spp_bezier_center
            op_bs.Resolution_U = scene.spp_resolution_u
            op_bs.Resolution_V = scene.spp_resolution_v

            live_edit_box = inner.box()
            live_edit_box.label(text="Live Surface Editing:")
            live_edit_box.prop(scene, "spp_show_surface_resolution_controls", text="Advanced: Edit Resolution")
            if scene.spp_show_surface_resolution_controls:
                row = live_edit_box.box().row(align=True)
                row.prop(scene, "spp_resolution_u", text="Resolution U")
                row.prop(scene, "spp_resolution_v", text="Resolution V")

            box2 = layout.box()
            box2.label(text="Step 4: Surface to Mesh", icon='MESH_GRID')
            box2.prop(scene, "spp_preserve_surface", text="Preserve Surface")
            box2.prop(scene, "spp_shade_smooth", text="Smooth Shading")
            box2.operator("object.convert", text="Convert to Mesh Object", icon='MESH_GRID').target = 'MESH'

    def draw_boundary_workflow(self, layout, context):
        # (unchanged existing implementation)
        scene = context.scene
        box = layout.box()
        box.label(text="Step 3: Convert Curve to Boundary Mesh", icon='OUTLINER_OB_MESH')
        box.operator("object.convert_to_mesh", text="Create Mesh", icon='MESH_DATA')

        obj = context.active_object
        vert_count = 0
        if obj and obj.type == 'MESH':
            vert_count = len(obj.data.vertices)
            edit_box = box.box()
            edit_header = edit_box.row(align=True)
            expand_icon = "TRIA_DOWN" if scene.spp_show_mesh_edit_section else "TRIA_RIGHT"
            edit_header.prop(scene, "spp_show_mesh_edit_section", text="", icon=expand_icon, emboss=False)
            edit_header.label(text="Step 3a: Refine Mesh", icon="EDITMODE_HLT")

            if scene.spp_show_mesh_edit_section:
                smooth_col = edit_box.column(align=True)
                smooth_col.label(text="Smoothing:", icon='MOD_SMOOTH')
                smooth_row = smooth_col.row(align=True)
                smooth_row.prop(scene, "spp_smooth_factor", text="Factor")
                smooth_row.operator("object.smooth_vertices", text="Apply", icon='CHECKMARK')

                reduce_col = edit_box.column(align=True)
                reduce_col.label(text="Vertex Reduction:", icon='VERTEXSEL')

                def get_even_vert_count(original, factor):
                    result = int(original * (1.0 - factor))
                    return result if result % 2 == 0 else result - 1

                row1 = reduce_col.row(align=True)
                op1 = row1.operator("object.reduce_verts", text=f"20% ({get_even_vert_count(vert_count, 0.2)} verts)")
                op1.factor = 0.2
                op2 = row1.operator("object.reduce_verts", text=f"40% ({get_even_vert_count(vert_count, 0.4)} verts)")
                op2.factor = 0.4

                row2 = reduce_col.row(align=True)
                op3 = row2.operator("object.reduce_verts", text=f"60% ({get_even_vert_count(vert_count, 0.6)} verts)")
                op3.factor = 0.6
                op4 = row2.operator("object.reduce_verts", text=f"80% ({get_even_vert_count(vert_count, 0.8)} verts)")
                op4.factor = 0.8

        box2 = layout.box()
        box2.label(text="Step 4: Generate Boundary Fill", icon='MESH_GRID')
        box2.prop(context.scene, "spp_grid_fill_span", text="Grid Fill Span")
        box2.operator("object.panel_generate", text="Generate Panel", icon='MOD_MESHDEFORM')


# Shared toggle operator
from . import workflow_operators

# Registration (unchanged)
classes = [OBJECT_PT_SurfaceWorkflow]

def register():
    from bpy.utils import register_class
    # (properties registration left as in your existing file)
    bpy.types.Scene.spp_bezier_workflow_expanded = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.spp_boundary_workflow_expanded = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.spp_show_bezier_tooltip = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.spp_show_boundary_tooltip = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.spp_bezier_center = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.spp_resolution_u = bpy.props.IntProperty(default=12, min=2, max=64, update=update_active_surface_resolution)
    bpy.types.Scene.spp_resolution_v = bpy.props.IntProperty(default=12, min=2, max=64, update=update_active_surface_resolution)
    bpy.types.Scene.spp_show_surface_resolution_controls = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.spp_preserve_surface = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.spp_shade_smooth = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.spp_show_mesh_edit_section = bpy.props.BoolProperty(default=True)

    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for attr in (
        "spp_bezier_workflow_expanded","spp_boundary_workflow_expanded",
        "spp_show_bezier_tooltip","spp_show_boundary_tooltip","spp_bezier_center",
        "spp_resolution_u","spp_resolution_v","spp_show_surface_resolution_controls",
        "spp_preserve_surface","spp_shade_smooth","spp_show_mesh_edit_section",
    ):
        if hasattr(bpy.types.Scene, attr):
            delattr(bpy.types.Scene, attr)
    for cls in classes:
        try: unregister_class(cls)
        except Exception: pass
