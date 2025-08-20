import bpy
from ..utils import icons


class OBJECT_PT_SneakerPanelLace(bpy.types.Panel):

    bl_label = "Lace Generator"
    bl_idname = "OBJECT_PT_sneaker_panel_pro_lace"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sneaker Panel"

    @classmethod
    def poll(cls, context):
        return bool(context.window_manager.spp_show_lace_gen)
        
    def draw_header(self, context):
        """Draw custom header with icon."""
        layout = self.layout
        # Get the custom icon ID
        icon_id = icons.get_icon("laces")
        layout.label(text="", icon_value=icon_id)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        icon_id = icons.get_icon("laces")
        obj = context.active_object

        lace_box = layout.box()
        lace_header = lace_box.row(align=True)

        # Panel header
        lace_header.label(text="Lace Generator", icon_value=icons.get_icon("laces"))

        # Add tooltip icon
        icon = "LIGHT_SUN" if context.scene.spp_show_lace_gen_tooltip else "INFO"
        lace_header.prop(context.scene, "spp_show_lace_gen_tooltip", text="", toggle=True, icon=icon)

        # Show tooltip if enabled
        if context.scene.spp_show_lace_gen_tooltip:
            tip_box = lace_box.box()
            tip_box.alert = True  # Makes the box stand out with a different color
            tip_col = tip_box.column(align=True)
            tip_col.scale_y = 0.9  # Slightly smaller text
            tip_col.label(text="Lace Generator Tips:", icon="HELP")
            tip_col.label(text="• Select curve object to apply lace geometry")
            tip_col.label(text="• Adjust parameters after applying")
            tip_col.label(text="• Use custom profile for unique lace shapes")
            tip_col.operator(
                "wm.url_open", text="View Lace Generator Tutorial", icon="URL"
            ).url = "https://example.com/lace-generator-tutorial"

        # Check if object has a lace modifier
        has_lace_modifier = False
        if obj:
            for mod in obj.modifiers:
                if mod.type == "NODES" and mod.name.startswith("Lace"):
                    has_lace_modifier = True
                    break

        if not has_lace_modifier:
            # Show apply button if no lace modifier exists
            apply_col = lace_box.column(align=True)
            apply_col.scale_y = 1.1
            apply_col.operator(
                "object.apply_lace_nodegroup",
                text="Apply Lace Geometry",
                icon="CURVE_DATA",
            )
            return

        # Parameters section - only shown if the modifier exists
        params_col = lace_box.column(align=True)

        # Profile type selection
        params_col.prop(scene, "spp_lace_profile", text="Profile")

        # Scale control
        params_col.prop(scene, "spp_lace_scale", text="Scale")

        # Resolution control
        params_col.prop(scene, "spp_lace_resample", text="Resolution")

        # Tilt control
        params_col.prop(scene, "spp_lace_tilt", text="Tilt")

        # Normal mode selection
        params_col.prop(scene, "spp_lace_normal_mode", text="Normal Mode")

        # Custom profile object - only show if profile type is Custom
        if scene.spp_lace_profile == "2":
            params_col.prop(scene, "spp_lace_custom_profile", text="Custom Profile")

        # Material assignment
        params_col.prop(scene, "spp_lace_material", text="Material")

        # Shade smooth toggle
        params_col.prop(scene, "spp_lace_shade_smooth", text="Shade Smooth")


# Registration
classes = [OBJECT_PT_SneakerPanelLace]


def register():
    # Register the panel class
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    # Unregister the panel class
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
