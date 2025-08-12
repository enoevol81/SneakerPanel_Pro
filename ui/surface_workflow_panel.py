import bpy

class OBJECT_PT_SurfaceWorkflow(bpy.types.Panel):
    """Surface Direct Workflow [3D] — core, linear (no Q&D here)."""
    bl_label = "Surface Direct Workflow [3D]"
    bl_idname = "OBJECT_PT_surface_workflow"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return getattr(context.window_manager, "spp_active_workflow", '') == 'SURFACE_3D'

    def draw(self, context):
        layout = self.layout
        S = context.scene

        # ---------- Step 1: Create Grease Pencil ----------
        gp_box = layout.box()
        gp_box.label(text="Step 1: Create Grease Pencil – Design Your Panel", icon="GREASEPENCIL")

        col = gp_box.column(align=True); col.scale_y = 1.1
        col.operator("object.add_gp_draw", text="Create Grease Pencil", icon='OUTLINER_OB_GREASEPENCIL')

        # Stabilizer (optional)
        stab = gp_box.box()
        r = stab.row(align=True)
        r.prop(S, "spp_use_stabilizer", text="")
        r.label(text="Stabilizer Settings")
        if getattr(S, "spp_use_stabilizer", False):
            c = stab.column(align=True)
            c.prop(S, "spp_stabilizer_radius", text="Radius")
            c.prop(S, "spp_stabilizer_strength_ui", text="Strength")

        # ---------- Step 2: Create & Edit Curve ----------
        curve_box = layout.box()
        curve_box.label(text="Step 2: Create & Edit Curve", icon='OUTLINER_OB_CURVE')

        col = curve_box.column(align=True); col.scale_y = 1.1
        col.operator("object.gp_to_curve", text="Convert to Curve", icon='IPO_BEZIER')

        tools = curve_box.box()
        tools.label(text="Curve Editing Tools", icon="TOOL_SETTINGS")

        # Step 2a – Decimate
        dec = tools.column(align=True)
        dec.label(text="Decimate Curve:", icon="MOD_DECIM")
        r = dec.row(align=True)
        r.prop(S, "spp_decimate_ratio", text="Ratio")
        r.operator("object.decimate_curve", text="Apply", icon='CHECKMARK')

        # Curve options
        opts = tools.column(align=True)
        opts.label(text="Curve Options:", icon="CURVE_DATA")
        rr = opts.row(align=True)
        rr.prop(S, "spp_curve_cyclic", text="")
        rr.label(text="Cyclic Curve")

        # Step 2b – Mirror (Edit Mode)
        mir = tools.column(align=True)
        mr = mir.row(align=True)
        mr.label(text="Mirror Tools (Edit Mode):", icon="MOD_MIRROR")
        mir.operator("curve.mirror_selected_points_at_cursor",
                     text="Mirror at Cursor", icon="CURVE_BEZCIRCLE")

        # ---------- Step 3: Convert Curve to Boundary Mesh ----------
        mesh_box = layout.box()
        mesh_box.label(text="Step 3: Convert Curve to Boundary Mesh", icon='OUTLINER_OB_MESH')
        r = mesh_box.row(align=True); r.scale_y = 1.1
        r.operator("object.convert_to_mesh", text="Create Mesh", icon='MESH_DATA')

        # Step 3a – Refine Mesh
        refine = mesh_box.box()
        refine.label(text="Step 3a: Refine Mesh", icon='EDITMODE_HLT')

        # Smoothing
        sm = refine.column(align=True)
        sm.label(text="Smoothing:", icon='MOD_SMOOTH')
        rr = sm.row(align=True)
        rr.prop(S, "spp_smooth_factor", text="Factor")
        rr.operator("object.smooth_vertices", text="Apply", icon='CHECKMARK')

        # Vertex Reduction (show current verts and even-count previews)
        vr = refine.column(align=True)
        vr.label(text="Vertex Reduction:", icon='VERTEXSEL')

        obj = context.active_object
        vert_count = 0
        if obj and obj.type == 'MESH':
            vert_count = len(obj.data.vertices)

        info = vr.row(); info.alignment = 'CENTER'
        info.label(text=f"Current: {vert_count} vertices", icon='INFO')

        def even_after(original, factor):
            n = int(original * (1.0 - factor))
            return n if n % 2 == 0 else max(0, n - 1)

        # Parity status and quick-fix
        if obj and obj.type == 'MESH':
            if vert_count % 2 != 0:
                warn = vr.row(align=True)
                warn.alert = True
                warn.label(text="Odd vertex count", icon='ERROR')
                warn.operator("mesh.make_even_verts", text="Make Even", icon='AUTOMERGE_ON')
            elif vert_count > 0:
                ok = vr.row(align=True)
                ok.label(text="Even vertex count", icon='CHECKMARK')

        row1 = vr.row(align=True)
        b = row1.operator("object.reduce_verts", text=f"20% ({even_after(vert_count, 0.2)} verts)")
        b.factor = 0.2
        b = row1.operator("object.reduce_verts", text=f"40% ({even_after(vert_count, 0.4)} verts)")
        b.factor = 0.4

        row2 = vr.row(align=True)
        b = row2.operator("object.reduce_verts", text=f"60% ({even_after(vert_count, 0.6)} verts)")
        b.factor = 0.6
        b = row2.operator("object.reduce_verts", text=f"80% ({even_after(vert_count, 0.8)} verts)")
        b.factor = 0.8

        # ---------- Step 4: Generate Boundary Fill ----------
        fill_box = layout.box()
        fill_box.label(text="Step 4: Generate Boundary Fill", icon='MESH_GRID')
        fill_box.prop(S, "spp_grid_fill_span", text="Grid Fill Span")
        r = fill_box.row(align=True); r.scale_y = 1.2
        r.operator("object.panel_generate", text="Generate Panel", icon='MOD_MESHDEFORM')


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
