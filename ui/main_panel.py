"""Main panel for the Sneaker Panel Pro addon.

This module defines the main panel that appears in the 3D View sidebar under the 'Sneaker Panel' category.
It provides access to common tools and settings used across the addon's workflow.
"""

import bpy
from bpy.props import BoolProperty


class OBJECT_PT_SneakerPanelProMain(bpy.types.Panel):
    """Main panel for Sneaker Panel Pro addon.
    
    This panel provides access to common tools and settings used in the panel creation workflow,
    including shell UV generation, panel settings, and the initial steps of the panel creation process.
    """
    bl_label = "Sneaker Panel Pro"
    bl_idname = "OBJECT_PT_sneaker_panel_pro_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'
    
    def draw(self, context):
        layout = self.layout
        
        # Panel Settings Section - Moved to top for better workflow
        main_box = layout.box()
        header_row = main_box.row()
        header_row.label(text="Panel Configuration", icon="SETTINGS")
        
        # Create a collapsible section using a row with a prop
        row = main_box.row()
        row.prop(context.scene, "spp_panel_count", text="Panel #")
        row.prop(context.scene, "spp_panel_name", text="Name")
        
        # Shell object selection with better formatting
        shell_row = main_box.row()
        shell_row.prop_search(context.scene, "spp_shell_object", bpy.data, "objects", text="Shell Object", icon="OUTLINER_OB_MESH")
        
        # Shell UV Generation Section - Collapsible box with better visual hierarchy
        uv_box = layout.box()
        uv_header = uv_box.row(align=True)
        
        # Add expand/collapse toggle with arrow icon
        expand_icon = "TRIA_DOWN" if context.scene.spp_show_uv_section else "TRIA_RIGHT"
        uv_header.prop(context.scene, "spp_show_uv_section", text="", icon=expand_icon, emboss=False)
        uv_header.label(text="Shell UV Generation", icon="OUTLINER_OB_LIGHTPROBE")
        
        # Add light bulb icon for tooltip
        tooltip_icon = 'LIGHT_SUN' if context.scene.spp_show_uv_gen_tooltip else 'LIGHT'
        uv_header.prop(context.scene, "spp_show_uv_gen_tooltip", text="", icon=tooltip_icon, emboss=False)
        
        # Only show content if expanded
        if context.scene.spp_show_uv_section:
            # Show tooltip if enabled
            if context.scene.spp_show_uv_gen_tooltip:
                tip_box = uv_box.box()
                tip_box.alert = True  # Makes the box stand out with a different color
                tip_col = tip_box.column(align=True)
                tip_col.scale_y = 0.9  # Slightly smaller text
                tip_col.label(text="Shell UV Generation Tips:", icon='HELP')
                tip_col.label(text="• Mark seams at heel counter and toe areas")
                tip_col.label(text="• Use the Smart UV Project first if needed")
                tip_col.label(text="• Proper orientation ensures accurate panel creation")
                tip_col.label(text="• The toe definition helps with panel alignment")
                tip_col.label(text="• Orient UV island for consistent panel direction")
                tip_col.operator("wm.url_open", text="View UV Setup Tutorial", icon='URL').url = "https://example.com/uv-setup-tutorial"
            
            # Important note with better formatting
            note_col = uv_box.column(align=True)
            note_col.label(text="Before Starting: Mark Seams at Heel and Boundary Edges", icon="INFO")
            
            # Steps with better visual flow
            steps_col = uv_box.column(align=True)
            steps_col.scale_y = 1.1
            steps_col.operator("object.unwrap_shell", text="1. Unwrap Shell", icon="MOD_UVPROJECT")
            steps_col.operator("object.define_toe", text="2. Define Toe", icon="CURVE_PATH")
            steps_col.operator("object.orient_uv_island", text="3. Orient UV Island", icon="ORIENTATION_LOCAL")
        
        # Panel Creation Workflow - Step 1
        gp_box = layout.box()
        gp_header = gp_box.row()
        gp_header.label(text="Step 1: Create Grease Pencil Object - Design Your Panel", icon="GREASEPENCIL")
        
        # Add tooltip toggle button
        tooltip_icon = "LIGHT_SUN" if context.scene.spp_show_gp_tooltip else "LIGHT"
        gp_header.prop(context.scene, "spp_show_gp_tooltip", text="", icon=tooltip_icon, emboss=False)
        
        # Show tooltip if enabled
        if context.scene.spp_show_gp_tooltip:
            tip_box = gp_box.box()
            tip_box.alert = True  # Makes the box stand out with a different color
            tip_col = tip_box.column(align=True)
            tip_col.scale_y = 0.9  # Slightly smaller text
            tip_col.label(text="Grease Pencil Drawing Tips:", icon='HELP')
            tip_col.label(text="• Draw directly on the 3D shell surface")
            tip_col.label(text="• Use the stabilizer for smoother lines")
            tip_col.label(text="• Creation of grease pencil is step 1 of panel creation workflow")
            tip_col.label(text="• New panel group automatically generated")
            tip_col.label(text="• Be sure to assign panel name and # before creating grease pencil")
            tip_col.label(text="• Use Undo (Ctrl+Z) to correct mistakes")
            tip_col.label(text="• Keep panel shapes simple and clean")
            tip_col.operator("wm.url_open", text="View Drawing Tutorial", icon='URL').url = "https://example.com/drawing-tutorial"
        
        # Grease pencil controls with better organization
        gp_col = gp_box.column(align=True)
        gp_col.scale_y = 1.1
        gp_col.operator("object.add_gp_draw", text="Create Grease Pencil", icon='OUTLINER_OB_GREASEPENCIL')
        
        # Stabilizer settings in a nested box for better visual hierarchy
        stab_box = gp_box.box()
        stab_row = stab_box.row()
        stab_row.prop(context.scene, "spp_use_stabilizer", text="")
        stab_row.label(text="Stabilizer Settings")
        
        # Only show settings when stabilizer is enabled
        if context.scene.spp_use_stabilizer:
            stab_col = stab_box.column(align=True)
            stab_col.prop(context.scene, "spp_stabilizer_radius", text="Radius")
            stab_col.prop(context.scene, "spp_stabilizer_strength_ui", text="Strength")

        # Panel Creation Workflow - Step 2
        curve_box = layout.box()
        curve_header = curve_box.row()
        curve_header.label(text="Step 2: Create & Edit Curve", icon='OUTLINER_OB_CURVE')
        
        # Curve creation with better organization
        curve_col = curve_box.column(align=True)
        curve_col.scale_y = 1.1
        curve_col.operator("object.gp_to_curve", text="Convert to Curve", icon='IPO_BEZIER')
        
        # Optional curve tools in a nested box
        curve_tools_box = curve_box.box()
        curve_tools_header = curve_tools_box.row()
        curve_tools_header.label(text="Curve Editing Tools", icon="TOOL_SETTINGS")
        
        # Decimate section
        decimate_col = curve_tools_box.column(align=True)
        decimate_col.label(text="Decimate Curve:", icon="MOD_DECIM")
        decimate_row = decimate_col.row(align=True)
        decimate_row.prop(context.scene, "spp_decimate_ratio", text="Ratio")
        decimate_row.operator("object.decimate_curve", text="Apply", icon='CHECKMARK')
        
        # Mirror section
        curve_tools_box.separator()
        mirror_col = curve_tools_box.column(align=True)
        
        # Mirror header with tooltip toggle
        mirror_header = mirror_col.row(align=True)
        mirror_header.label(text="Mirror Tools (Edit Mode):", icon="MOD_MIRROR")
        
        # Add light bulb icon for tooltip
        tooltip_icon = 'LIGHT_SUN' if context.scene.spp_show_mirror_tooltip else 'LIGHT'
        mirror_header.prop(context.scene, "spp_show_mirror_tooltip", text="", icon=tooltip_icon, emboss=False)
        
        # Mirror operator
        mirror_col.operator("curve.mirror_selected_points_at_cursor", text="Mirror at Cursor", icon="CURVE_BEZCIRCLE")
        
        # Show tooltip if enabled
        if context.scene.spp_show_mirror_tooltip:
            tip_box = mirror_col.box()
            tip_box.alert = True  # Makes the box stand out with a different color
            tip_col = tip_box.column(align=True)
            tip_col.scale_y = 0.9  # Slightly smaller text
            tip_col.label(text="Mirror at Cursor Tips:", icon='HELP')
            tip_col.label(text="• Position 3D cursor at desired mirror axis")
            tip_col.label(text="• Select points to mirror in Edit Mode")
            tip_col.label(text="• Creates symmetrical curves quickly")
            tip_col.label(text="• Great for creating matching left/right panels")
            tip_col.label(text="• Use front/side view for precise placement")
        
        # Lace Generator Section
        lace_box = layout.box()
        lace_header = lace_box.row(align=True)
        
        # Add expand/collapse toggle with arrow icon
        expand_icon = "TRIA_DOWN" if context.scene.spp_show_lace_options else "TRIA_RIGHT"
        lace_header.prop(context.scene, "spp_show_lace_options", text="", icon=expand_icon, emboss=False)
        lace_header.label(text="Lace Generator", icon="OUTLINER_OB_CURVE")
        
        # Only show content if expanded
        if context.scene.spp_show_lace_options:
            # Lace controls
            lace_col = lace_box.column(align=True)
            lace_col.prop(context.scene, "spp_lace_profile", text="Profile Type")
            lace_col.prop(context.scene, "spp_lace_scale", text="Scale")
            lace_col.prop(context.scene, "spp_lace_resample", text="Resample Points")
            lace_col.prop(context.scene, "spp_lace_tilt", text="Tilt")
            lace_col.prop(context.scene, "spp_lace_normal_mode", text="Normal Mode")
            lace_col.prop(context.scene, "spp_lace_shade_smooth", text="Shade Smooth")
            
            # Only show custom profile field when profile type is "Custom"
            if context.scene.spp_lace_profile == '2':
                lace_col.prop(context.scene, "spp_lace_custom_profile", text="Custom Profile")
            
            # Apply button
            op_col = lace_box.column(align=True)
            op_col.scale_y = 1.2
            op_col.operator("object.add_lace_modifier", text="Apply Lace Geometry", icon="MOD_CURVE")
     
# Registration
classes = [OBJECT_PT_SneakerPanelProMain]

def register():
    """Register the panel and properties."""
    bpy.utils.register_class(OBJECT_PT_SneakerPanelProMain)
    
    # Register UI section toggle properties
    bpy.types.Scene.spp_show_uv_section = bpy.props.BoolProperty(
        name="Show UV Generation Section",
        default=False,
        description="Expand or collapse the UV Generation section"
    )
    
    # Register tooltip properties
    bpy.types.Scene.spp_show_mirror_tooltip = bpy.props.BoolProperty(
        name="Show Mirror at Cursor Tooltip",
        default=False,
        description="Show helpful tips for the Mirror at Cursor function"
    )
    bpy.types.Scene.spp_show_uv_gen_tooltip = bpy.props.BoolProperty(
        name="Show UV Generation Tooltip",
        default=False,
        description="Show helpful tips for the Shell UV Generation workflow"
    )
    bpy.types.Scene.spp_show_gp_tooltip = bpy.props.BoolProperty(
        name="Show Grease Pencil Drawing Tooltip",
        default=False,
        description="Show helpful tips for drawing panels with Grease Pencil"
    )

def unregister():
    """Unregister the panel and properties."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    # Remove custom properties
    if hasattr(bpy.types.Scene, "spp_show_uv_section"):
        del bpy.types.Scene.spp_show_uv_section
    
    # Remove tooltip properties
    if hasattr(bpy.types.Scene, "spp_show_mirror_tooltip"):
        del bpy.types.Scene.spp_show_mirror_tooltip
    
    if hasattr(bpy.types.Scene, "spp_show_uv_gen_tooltip"):
        del bpy.types.Scene.spp_show_uv_gen_tooltip
        
    if hasattr(bpy.types.Scene, "spp_show_gp_tooltip"):
        del bpy.types.Scene.spp_show_gp_tooltip

if __name__ == "__main__":
    register()
