import bpy
from bpy.types import Panel

from ..utils import icons


class PP_PT_Main(Panel):
    bl_label = " Profile Projection"
    bl_idname = "PP_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sneaker Panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        """Draw custom header with icon."""
        layout = self.layout
        # Get the custom ref_image icon ID
        icon_id = icons.get_icon("ref_image")
        if icon_id:
            layout.label(text="", icon_value=icon_id)

    @classmethod
    def poll(cls, context):
        # Only show panel when the toggle is enabled
        wm = context.window_manager
        return getattr(wm, "spp_show_profile_projection", False)

    def draw(self, context):
        layout = self.layout
        props = context.scene.profile_proj
        icon_id = icons.get_icon("ref_image")

        # Main box for the panel content
        main_box = layout.box()
        main_header = main_box.row(align=True)

        # Panel header
        main_header.label(text="Profile Projection", icon_value=icon_id)

        # Add tooltip icon
        icon = "LIGHT_SUN" if context.scene.spp_show_profile_proj_tooltip else "INFO"
        main_header.prop(
            context.scene,
            "spp_show_profile_proj_tooltip",
            text="",
            toggle=True,
            icon=icon,
        )

        # Show tooltip if enabled
        if context.scene.spp_show_profile_proj_tooltip:
            tip_box = main_box.box()
            tip_box.alert = True  # Makes the box stand out with a different color
            tip_col = tip_box.column(align=True)
            tip_col.scale_y = 0.9  # Slightly smaller text
            tip_col.label(text="Profile Projection Tips:", icon="HELP")
            tip_col.label(text="• Select reference image to be projected")
            tip_col.label(text="• Pick preferred orthographic view")
            tip_col.label(
                text="• Run 'Create Projection UV' to create 'Projection' UV map"
            )
            tip_col.label(
                text="• Switch to UV Editor and scale UV to cover reference image"
            )
            tip_col.label(text="• Select output size")
            tip_col.label(text="• Run 'Create Image Texture and Material'")
            tip_col.label(text="• Run 'Transfer Image UV'")
            tip_col.label(
                text="• Switch to Texture Paint mode to paint mesh with reference image"
            )
            tip_col.label(
                text="• Make sure 'Clone tool' is active and set to 'Single Image' with 'Projected Design' as 'Clone image' - Active UV is 'UV Mesh'"
            )
            tip_col.label(
                text="• In brush settings make sure 'Clone From Paint Slot' is ticked and 'Clone Image' is set to your reference drawing, and 'Source UV' is set to 'Projection'"
            )
            tip_col.label(text="• With render settings set to 'Material Preview', paint mesh with the reference image")
            tip_col.label(text="• Remember to save images")
            tip_col.label(text="• Adjust Reference Image opacity in material properties to control the amount of projected image")        
            tip_col.operator(
                "wm.url_open",
                text="View Reference Image Projection Tutorial",
                icon="URL",
            ).url = "https://youtu.be/JTzSzB_lelk"

        # Parameters section
        params_box = main_box.box()
        params_box.label(text="Parameters:", icon="PROPERTIES")
        params_col = params_box.column(align=True)
        params_col.scale_y = 1.1

        params_col.prop(props, "image_path")
        params_col.prop(props, "projection_uv")
        params_col.prop(props, "main_uv")
        params_col.prop(props, "dest_size")

        # Actions section
        actions_box = main_box.box()
        actions_box.label(text="Actions:", icon="PLAY")
        actions_col = actions_box.column(align=True)
        actions_col.scale_y = 1.1

        actions_col.operator("pp.create_projection_uv", icon="IMAGE_PLANE")
        actions_col.separator()
        actions_col.operator("pp.create_dest_and_material", icon="MATERIAL")
        actions_col.separator()
        actions_col.operator("pp.auto_clone_transfer", icon="BRUSH_DATA")


# Registration
classes = [PP_PT_Main]


def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception:
            pass


def unregister():
    for cls in reversed(classes):
        try:
            if hasattr(cls, "bl_rna"):
                bpy.utils.unregister_class(cls)
        except Exception:
            pass


if __name__ == "__main__":
    register()
