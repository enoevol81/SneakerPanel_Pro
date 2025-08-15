# -------------------------------------------------------------------------
# Surface Workflow Panel UI
# -------------------------------------------------------------------------

import bpy


class OBJECT_PT_SurfaceWorkflow(bpy.types.Panel):
    """Surface Direct Workflow [3D] — core, linear workflow."""

    bl_label = "Surface Direct Workflow [3D]"
    bl_idname = "OBJECT_PT_surface_workflow"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sneaker Panel"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return (
            getattr(context.window_manager, "spp_active_workflow", "") == "SURFACE_3D"
        )

    def draw(self, context):
        layout = self.layout
        S = context.scene

        surface_box = layout.box()
        surface_header = surface_box.row(align=True)

        # Panel header
        surface_header.label(text="Surface Direct Workflow [3D]", icon="MESH_CUBE")

        # Tooltip toggle
        tooltip_icon = (
            "LIGHT_SUN" if context.scene.spp_show_surface_workflow_tooltip else "INFO"
        )
        surface_header.prop(
            context.scene,
            "spp_show_surface_workflow_tooltip",
            text="",
            icon=tooltip_icon,
            emboss=False,
        )

        # Tooltip content
        if context.scene.spp_show_surface_workflow_tooltip:
            surface_box.separator(factor=0.3)
            tip_box = surface_box.box()
            tip_box.alert = True
            tip_col = tip_box.column(align=True)
            tip_col.scale_y = 0.9
            tip_col.label(text="Surface Workflow Tips:", icon="HELP")
            tip_col.label(text="• Use Stabilizer for pencil control")
            tip_col.operator(
                "wm.url_open", text="View Surface Workflow Tutorial", icon="URL"
            ).url = "https://example.com/surface-workflow-tutorial"

        # Step 1: Create Grease Pencil
        surface_box.separator(factor=0.5)
        gp_box = surface_box.box()
        gp_box.label(
            text="Step 1: Create Grease Pencil – Design Your Panel", icon="GREASEPENCIL"
        )

        gp_box.separator(factor=0.3)
        col = gp_box.column(align=True)
        col.scale_y = 1.0
        col.operator(
            "object.add_gp_draw",
            text="Create Grease Pencil",
            icon="OUTLINER_OB_GREASEPENCIL",
        )

        # Stabilizer settings
        gp_box.separator(factor=0.3)
        stab = gp_box.box()
        stab_header = stab.row(align=True)
        stab_header.prop(S, "spp_use_stabilizer", text="")
        stab_header.label(text="Stabilizer Settings")

        if getattr(S, "spp_use_stabilizer", False):
            stab.separator(factor=0.2)
            stab_col = stab.column(align=True)
            stab_col.scale_y = 0.9
            stab_col.prop(S, "spp_stabilizer_radius", text="Radius")
            stab_col.prop(S, "spp_stabilizer_strength_ui", text="Strength")

        # Step 2: Create & Edit Curve (collapsible)
        step2_header = surface_box.row(align=True)
        step2_header.prop(
            context.window_manager,
            "spp_show_surface_step_2",
            text="",
            icon="TRIA_DOWN" if context.window_manager.spp_show_surface_step_2 else "TRIA_RIGHT",
            emboss=False,
        )
        step2_header.label(text="Step 2: Create & Edit Curve", icon="OUTLINER_OB_CURVE")
        
        if context.window_manager.spp_show_surface_step_2:
            # Check requirements
            obj = context.active_object
            if not obj or obj.type not in {"GPENCIL", "CURVE"}:
                req_box = surface_box.box()
                req_box.alert = True
                req_box.label(text="Requires: Select a Grease Pencil stroke or Curve", icon="INFO")
            else:
                curve_box = surface_box.box()
                
                curve_box.separator(factor=0.3)
                col = curve_box.column(align=True)
                col.scale_y = 1.0
                col.operator("object.gp_to_curve", text="Convert to Curve", icon="IPO_BEZIER")

                # Curve editing tools
                curve_box.separator(factor=0.3)
                tools = curve_box.box()
                tools.label(text="Curve Editing Tools", icon="TOOL_SETTINGS")

                # Decimate curve
                tools.separator(factor=0.2)
                dec = tools.column(align=True)
                dec.label(text="Decimate Curve", icon="MOD_DECIM")
                dec_row = dec.row(align=True)
                dec_row.prop(S, "spp_decimate_ratio", text="Ratio")
                dec_row.operator("object.decimate_curve", text="Apply", icon="CHECKMARK")

                # Curve options
                tools.separator(factor=0.2)
                opts = tools.column(align=True)
                opts.label(text="Curve Options", icon="CURVE_DATA")
                cyclic_row = opts.row(align=True)
                cyclic_row.prop(S, "spp_curve_cyclic", text="")
                cyclic_row.label(text="Cyclic Curve")

                # Mirror tools
                tools.separator(factor=0.2)
                mir = tools.column(align=True)
                mir.label(text="Mirror Tools (Edit Mode)", icon="MOD_MIRROR")
                mir.operator(
                    "curve.mirror_selected_points_at_cursor",
                    text="Mirror at Cursor",
                    icon="CURVE_BEZCIRCLE",
                )

        # Step 3: Convert Curve to Boundary Mesh (collapsible)
        step3_header = surface_box.row(align=True)
        step3_header.prop(
            context.window_manager,
            "spp_show_surface_step_3",
            text="",
            icon="TRIA_DOWN" if context.window_manager.spp_show_surface_step_3 else "TRIA_RIGHT",
            emboss=False,
        )
        step3_header.label(text="Step 3: Convert Curve to Boundary Mesh", icon="OUTLINER_OB_MESH")
        
        if context.window_manager.spp_show_surface_step_3:
            # Check requirements
            obj = context.active_object
            if not obj or obj.type != "CURVE":
                req_box = surface_box.box()
                req_box.alert = True
                req_box.label(text="Requires: Select a Curve", icon="INFO")
            else:
                mesh_box = surface_box.box()
                
                mesh_box.separator(factor=0.3)
                mesh_row = mesh_box.row(align=True)
                mesh_row.scale_y = 1.0
                mesh_row.operator(
                    "object.convert_to_mesh", text="Create Mesh", icon="MESH_DATA"
                )

                # Refine mesh tools
                mesh_box.separator(factor=0.3)
                refine = mesh_box.box()
                refine.label(text="Step 3a: Refine Mesh", icon="EDITMODE_HLT")

                # Smoothing
                refine.separator(factor=0.2)
                sm = refine.column(align=True)
                sm.label(text="Smoothing", icon="MOD_SMOOTH")
                smooth_row = sm.row(align=True)
                smooth_row.prop(S, "spp_smooth_factor", text="Factor")
                smooth_row.operator("object.smooth_vertices", text="Apply", icon="CHECKMARK")

                # Vertex reduction
                refine.separator(factor=0.2)
                vr = refine.column(align=True)
                vr.label(text="Vertex Reduction", icon="VERTEXSEL")

                obj = context.active_object
                vert_count = 0
                if obj and obj.type == "MESH":
                    vert_count = len(obj.data.vertices)

                info_row = vr.row()
                info_row.alignment = "CENTER"
                info_row.scale_y = 0.9
                info_row.label(text=f"Current: {vert_count} vertices", icon="INFO")

                def even_after(original, factor):
                    n = int(original * (1.0 - factor))
                    return n if n % 2 == 0 else max(0, n - 1)

                # Vertex parity check
                if obj and obj.type == "MESH":
                    parity_row = vr.row(align=True)
                    parity_row.scale_y = 0.9
                    
                    if vert_count % 2 != 0:
                        parity_row.alert = True
                        parity_row.label(text="Odd vertex count", icon="ERROR")
                        parity_row.operator(
                            "mesh.make_even_verts", text="Make Even", icon="AUTOMERGE_ON"
                        )
                    elif vert_count > 0:
                        parity_row.label(text="Even vertex count", icon="CHECKMARK")

                row1 = vr.row(align=True)
                b = row1.operator(
                    "object.reduce_verts", text=f"20% ({even_after(vert_count, 0.2)} verts)"
                )
                b.factor = 0.2
                b = row1.operator(
                    "object.reduce_verts", text=f"40% ({even_after(vert_count, 0.4)} verts)"
                )
                b.factor = 0.4

                row2 = vr.row(align=True)
                b = row2.operator(
                    "object.reduce_verts", text=f"60% ({even_after(vert_count, 0.6)} verts)"
                )
                b.factor = 0.6
                b = row2.operator(
                    "object.reduce_verts", text=f"80% ({even_after(vert_count, 0.8)} verts)"
                )
                b.factor = 0.8

        # Step 4: Generate Boundary Fill (collapsible)
        step4_header = surface_box.row(align=True)
        step4_header.prop(
            context.window_manager,
            "spp_show_surface_step_4",
            text="",
            icon="TRIA_DOWN" if context.window_manager.spp_show_surface_step_4 else "TRIA_RIGHT",
            emboss=False,
        )
        step4_header.label(text="Step 4: Generate Boundary Fill", icon="MESH_GRID")
        
        if context.window_manager.spp_show_surface_step_4:
            # Check requirements
            obj = context.active_object
            if not obj or obj.type != "MESH":
                req_box = surface_box.box()
                req_box.alert = True
                req_box.label(text="Requires: Select a Mesh", icon="INFO")
            else:
                fill_box = surface_box.box()
                
                fill_box.separator(factor=0.3)
                fill_box.prop(S, "spp_grid_fill_span", text="Grid Fill Span")
                
                fill_box.separator(factor=0.3)
                fill_row = fill_box.row(align=True)
                fill_row.scale_y = 1.1
                fill_row.operator(
                    "object.panel_generate", text="Generate Panel", icon="MOD_MESHDEFORM"
                )


# (No extra operators defined here; we reuse existing ones.)
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
