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
        
        # Find lace modifier for direct socket control
        lace_modifier = None
        if obj:
            for mod in obj.modifiers:
                if mod.type == 'NODES' and mod.node_group:
                    # Check for both old naming and new asset-based node group
                    if 'LaceFromCurves' in mod.node_group.name or 'spp_lace' in mod.node_group.name or 'Lace' in mod.name:
                        lace_modifier = mod
                        break
        
        # Main controls column
        col = lace_box.column(align=True)
        
        # Profile Type Selection
        col.label(text="Profile Type:")
        col.prop(scene, "spp_lace_profile", text="")
        
        # Custom Profile Object (only show for Custom type)
        # Accept multiple representations of the custom profile enum (e.g. 'CUSTOM', '2', etc.)
        if scene.spp_lace_profile in {'CUSTOM', 'Custom', 'custom', '2', 2}:
            # If a lace modifier has already been applied, expose socket 12 directly.
            # According to the asset file, the custom profile lives on Socket_12.
            if lace_modifier:
                try:
                    if "Socket_12" in lace_modifier:
                        col.prop(lace_modifier, '["Socket_12"]', text="Custom Profile")
                    else:
                        # Fallback to scene property when socket 12 is not yet available
                        col.prop(scene, "spp_lace_custom_profile", text="Custom Profile")
                except Exception:
                    # Fallback to scene property if direct access fails
                    col.prop(scene, "spp_lace_custom_profile", text="Custom Profile")
            else:
                # No modifier yet, show scene property so the user can choose a profile before applying
                col.prop(scene, "spp_lace_custom_profile", text="Custom Profile")
        
        # Geometry Controls - direct socket control
        col.separator()
        col.label(text="Geometry Settings:")
        
        if lace_modifier:
            # Direct modifier socket control with fallback
            try:
                if "Socket_8" in lace_modifier:  # Resample
                    col.prop(lace_modifier, '["Socket_8"]', text="Resample")
                elif "Resample" in lace_modifier:
                    col.prop(lace_modifier, '["Resample"]', text="Resample")
                else:
                    col.prop(scene, "spp_lace_resample", text="Resample")
                    
                if "Socket_2" in lace_modifier:  # Scale
                    col.prop(lace_modifier, '["Socket_2"]', text="Scale")
                elif "Scale" in lace_modifier:
                    col.prop(lace_modifier, '["Scale"]', text="Scale")
                else:
                    col.prop(scene, "spp_lace_scale", text="Scale")
                    
                if "Socket_3" in lace_modifier:  # Tilt
                    col.prop(lace_modifier, '["Socket_3"]', text="Tilt")
                elif "Tilt" in lace_modifier:
                    col.prop(lace_modifier, '["Tilt"]', text="Tilt")
                else:
                    col.prop(scene, "spp_lace_tilt", text="Tilt")
            except:
                # Fallback to scene properties if socket access fails
                col.prop(scene, "spp_lace_resample", text="Resample")
                col.prop(scene, "spp_lace_scale", text="Scale")
                col.prop(scene, "spp_lace_tilt", text="Tilt")
        else:
            # Fallback to scene properties when no modifier exists
            col.prop(scene, "spp_lace_resample", text="Resample")
            col.prop(scene, "spp_lace_scale", text="Scale")
            col.prop(scene, "spp_lace_tilt", text="Tilt")
        
        # Normal Mode
        col.separator()
        col.label(text="Normal Settings:")
        
        # Normal Mode - always use scene property to prevent collapse
        col.prop(scene, "spp_lace_normal_mode", text="Normal Mode")
        
        # Free Normal Controls - show when Free mode is selected
        if scene.spp_lace_normal_mode == '2':
            col.separator()
            col.label(text="Free Normal Direction:")
            if lace_modifier and "Socket_10" in lace_modifier:
                # Direct socket control for Free Normal vector
                row = col.row(align=True)
                row.prop(lace_modifier, '["Socket_10"]', index=0, text="X")
                row.prop(lace_modifier, '["Socket_10"]', index=1, text="Y")
                row.prop(lace_modifier, '["Socket_10"]', index=2, text="Z")
            else:
                col.prop(scene, "spp_lace_free_normal", text="")
        # This else block is no longer needed as we always use scene properties for normal mode
        
        # Flip Options and Material
        col.separator()
        col.label(text="Appearance:")
        
        if lace_modifier:
            # Color - Socket_11
            if "Socket_11" in lace_modifier:
                col.prop(lace_modifier, '["Socket_11"]', text="Color")
            else:
                col.prop(scene, "spp_lace_color", text="Color")
            
            # Flip Normal - Socket_6
            if "Socket_6" in lace_modifier:
                col.prop(lace_modifier, '["Socket_6"]', text="Flip Normal")
            else:
                col.prop(scene, "spp_lace_flip_normal", text="Flip Normal")
            
            # Shade Smooth - Socket_9
            if "Socket_9" in lace_modifier:
                col.prop(lace_modifier, '["Socket_9"]', text="Shade Smooth")
            else:
                col.prop(scene, "spp_lace_shade_smooth", text="Shade Smooth")
            
            # Material section removed - using default lace material only
        else:
            # Fallback to scene properties when no modifier exists
            col.prop(scene, "spp_lace_color", text="Color")
            col.prop(scene, "spp_lace_flip_normal", text="Flip Normal")
            col.prop(scene, "spp_lace_shade_smooth", text="Shade Smooth")
            
            # Material section removed - using default lace material only
        
        # Apply Button
        col.separator()
        apply_col = col.column(align=True)
        apply_col.scale_y = 1.2
        
        # Apply lace operator - uses scene properties internally
        apply_col.operator("spp.apply_lace", text="Apply Lace", icon="CURVE_DATA")
        
        # Custom profile is now handled directly above


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
