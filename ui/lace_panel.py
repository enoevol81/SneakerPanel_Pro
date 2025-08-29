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

        # Check if active object is a curve
        if not obj or obj.type != 'CURVE':
            error_col = lace_box.column(align=True)
            error_col.alert = True
            error_col.label(text="Select a curve object to apply lace", icon="ERROR")
            return
        
        # Main controls column
        col = lace_box.column(align=True)
        
        # Profile Type Selection
        col.label(text="Profile Type:")
        col.prop(scene, "spp_lace_profile", text="")
        
        # Custom Profile Object (only show for Custom type)
        if scene.spp_lace_profile == 'CUSTOM':
            col.prop(scene, "spp_lace_custom_profile", text="Custom Profile")
        
        # Find lace modifier for direct socket control
        lace_modifier = None
        if obj:
            for mod in obj.modifiers:
                if mod.type == 'NODES' and mod.node_group and 'spp_lace' in mod.node_group.name:
                    lace_modifier = mod
                    break
        
        # Geometry Controls - direct socket control
        col.separator()
        col.label(text="Geometry Settings:")
        
        if lace_modifier:
            # Direct modifier socket control
            if "Socket_8" in lace_modifier:  # Resample
                col.prop(lace_modifier, '["Socket_8"]', text="Resample")
            if "Socket_2" in lace_modifier:  # Scale
                col.prop(lace_modifier, '["Socket_2"]', text="Scale")
            if "Socket_3" in lace_modifier:  # Tilt
                col.prop(lace_modifier, '["Socket_3"]', text="Tilt")
        else:
            # Fallback to scene properties when no modifier exists
            col.prop(scene, "spp_lace_resample", text="Resample")
            col.prop(scene, "spp_lace_scale", text="Scale")
            col.prop(scene, "spp_lace_tilt", text="Tilt")
        
        # Normal Mode
        col.separator()
        col.label(text="Normal Settings:")
        
        if lace_modifier:
            if "Socket_4" in lace_modifier:  # Normal Mode
                # Create a custom enum property for the normal mode dropdown
                normal_mode_value = lace_modifier.get("Socket_4", 0)
                
                # Custom dropdown for normal mode
                row = col.row()
                row.label(text="Normal Mode:")
                
                # Create enum items based on the geometry node setup
                enum_items = [
                    ("0", "Minimum Twist", "Use minimum twist for curve normals"),
                    ("1", "Z Up", "Align normals with Z-up direction"), 
                    ("2", "Free", "Free normal direction")
                ]
                
                # Use scene property for the dropdown but sync with socket
                col.prop(scene, "spp_lace_normal_mode", text="")
                
                # Sync scene property to socket when changed
                if str(scene.spp_lace_normal_mode) != str(normal_mode_value):
                    lace_modifier["Socket_4"] = int(scene.spp_lace_normal_mode)
                
            # Free Normal Controls (Socket_10 with X=0, Y=1, Z=2) - only show when Free mode selected
            if "Socket_10" in lace_modifier and scene.spp_lace_normal_mode == '2':
                col.separator()
                col.label(text="Free Normal:")
                row = col.row(align=True)
                row.prop(lace_modifier, '["Socket_10"]', index=0, text="X")
                row.prop(lace_modifier, '["Socket_10"]', index=1, text="Y")
                row.prop(lace_modifier, '["Socket_10"]', index=2, text="Z")
        else:
            col.prop(scene, "spp_lace_normal_mode", text="")
            if scene.spp_lace_normal_mode == '2':
                col.prop(scene, "spp_lace_free_normal", text="Free Normal")
        
        # Flip Options
        col.separator()
        if lace_modifier:
            if "Socket_6" in lace_modifier:  # Flip Normal
                col.prop(lace_modifier, '["Socket_6"]', text="Flip Normal")
            if "Socket_9" in lace_modifier:  # Shade Smooth
                col.prop(lace_modifier, '["Socket_9"]', text="Shade Smooth")
        else:
            row = col.row(align=True)
            row.prop(scene, "spp_lace_flip_v", text="Flip V")
            row.prop(scene, "spp_lace_flip_normal", text="Flip Normal")
            col.prop(scene, "spp_lace_shade_smooth", text="Shade Smooth")
        
        # Color and Material
        col.separator()
        col.label(text="Appearance:")
        if lace_modifier:
            if "Socket_11" in lace_modifier:  # Lace Color
                col.prop(lace_modifier, '["Socket_11"]', text="Lace Color")
            
            # Material Selection - make it user-definable
            col.separator()
            col.label(text="Material:")
            row = col.row(align=True)
            row.prop(scene, "spp_lace_use_custom_material", text="Custom")
            if scene.spp_lace_use_custom_material:
                col.prop(scene, "spp_lace_custom_material", text="")
                # Apply custom material to socket when selected
                if scene.spp_lace_custom_material and "Socket_5" in lace_modifier:
                    lace_modifier["Socket_5"] = scene.spp_lace_custom_material
            else:
                # Show default material info
                col.label(text="Using default lace material")
        else:
            col.prop(scene, "spp_lace_color", text="Lace Color")
            # Material Section
            col.separator()
            col.label(text="Material:")
            row = col.row(align=True)
            row.prop(scene, "spp_lace_use_custom_material", text="Custom")
            if scene.spp_lace_use_custom_material:
                col.prop(scene, "spp_lace_custom_material", text="")
        
        # Apply Button
        col.separator()
        apply_col = col.column(align=True)
        apply_col.scale_y = 1.2
        
        # Apply lace operator - uses scene properties internally
        apply_col.operator("spp.apply_lace", text="Apply Lace", icon="CURVE_DATA")


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
