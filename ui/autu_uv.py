import bpy


class OBJECT_PT_autu_uv(bpy.types.Panel):

    bl_label = "Auto UV"
    bl_idname = "OBJECT_PT_sneaker_panel_pro_autu_uv"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sneaker Panel"

    @classmethod
    def poll(cls, context):
        return bool(context.window_manager.spp_show_auto_uv)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = context.active_object

        uv_box = layout.box()
        uv_header = uv_box.row(align=True)

        # Panel header
        uv_header.label(text="Shell UV Generation", icon="OUTLINER_OB_LIGHTPROBE")

        # Add light bulb icon for tooltip
        tooltip_icon = "LIGHT_SUN" if context.scene.spp_show_uv_gen_tooltip else "INFO"
        uv_header.prop(
            context.scene,
            "spp_show_uv_gen_tooltip",
            text="",
            icon=tooltip_icon,
            emboss=False,
        )

        # Show tooltip if enabled
        if context.scene.spp_show_uv_gen_tooltip:
            tip_box = uv_box.box()
            tip_box.alert = True  # Makes the box stand out with a different color
            tip_col = tip_box.column(align=True)
            tip_col.scale_y = 0.9  # Slightly smaller text
            tip_col.label(text="• Mark seams at Boundary and Heel Counter Edges")
            tip_col.label(text="• Run 'Unwrap Shell' to create UV layout")
            tip_col.label(text="• Place 3D cursor at toe tip → Click 'Define Toe'")
            tip_col.label(
                text="• Place cursor at direction point → Click 'Define Up Axis [Z+ Axis]'"
            )
            tip_col.label(text="• Run 'Orient UV Island' for precise orientation")
            tip_col.label(text="• Direction point: tongue area or toward ankle")
            tip_col.operator(
                "wm.url_open", text="View UV Setup Tutorial", icon="URL"
            ).url = "https://example.com/uv-setup-tutorial"

        # Steps with better visual flow
        steps_col = uv_box.column(align=True)
        steps_col.scale_y = 1.1
        steps_col.operator(
            "object.unwrap_shell", text="1. Unwrap Shell", icon="MOD_UVPROJECT"
        )

        # Two-button system for toe direction
        toe_row = steps_col.row(align=True)
        toe_row.operator("object.define_toe", text="2a. Define Toe", icon="MESH_CIRCLE")
        toe_row.operator(
            "object.define_up_direction",
            text="2b. Define Up Axis [Z+ Axis]",
            icon="ORIENTATION_LOCAL",
        )

        steps_col.operator(
            "object.orient_uv_island", text="3. Orient UV Island", icon="SNAP_ON"
        )


# Registration
classes = [OBJECT_PT_autu_uv]


def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception:
            pass  # safe hot-reload


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
