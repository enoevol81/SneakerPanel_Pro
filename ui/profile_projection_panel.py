import bpy
from bpy.types import Panel

from ..utils import icons


class PP_PT_Main(Panel):
    bl_label = " Profile Projection"
    bl_idname = "PP_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Sneaker Panel"
    bl_options = {'DEFAULT_CLOSED'}

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
        props = context.scene.profile_proj
        layout = self.layout
        
        layout.prop(props, "image_path")
        layout.prop(props, "projection_uv")
        layout.prop(props, "main_uv")
        layout.prop(props, "dest_size")
        layout.separator()
        layout.operator("pp.create_projection_uv", icon='IMAGE_PLANE')
        layout.operator("pp.create_dest_and_material", icon='MATERIAL')
        layout.separator()
        layout.operator("pp.auto_clone_transfer", icon='BRUSH_DATA')


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
