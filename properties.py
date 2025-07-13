"""
Properties module for SneakerPanel Pro.

This module defines all the properties used by the SneakerPanel Pro addon,
organized by functionality categories. The properties are grouped into logical sections:

- Panel identification and naming properties
- Target object properties
- Grease Pencil stabilizer properties
- Mesh processing properties
- Curve processing properties
- Panel generation properties
- Solidify properties
- UV unwrapping properties

The module also provides helper functions for property registration, unregistration,
and updating modifier properties.
"""

import bpy
from .utils.panel_utils import update_stabilizer, update_stabilizer_ui


# Group properties by functionality for better organization
def register_properties():
    """Register all properties used by the SneakerPanel Pro addon."""
    # -------------------------------------------------------------------------
    # Lace generator properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_lace_profile = bpy.props.EnumProperty(
        name="Lace Profile",
        description="Shape profile to use for the lace",
        items=[
            ('0', "Circle", "Circular lace profile"),
            ('1', "Flat", "Flat rectangular lace profile"),
            ('2', "Custom", "Custom profile from another object")
        ],
        default='0',
        update=_update_lace_modifier
    )
    
    bpy.types.Scene.spp_lace_scale = bpy.props.FloatProperty(
        name="Scale",
        description="Size of the lace profile",
        default=0.005,
        min=0.0001,
        max=0.1,
        precision=4,
        subtype='DISTANCE',
        update=_update_lace_modifier
    )
    
    bpy.types.Scene.spp_lace_resample = bpy.props.IntProperty(
        name="Resample",
        description="Number of points to resample the curve with",
        default=110,
        min=1,
        max=1000,
        update=_update_lace_modifier
    )
    
    bpy.types.Scene.spp_lace_tilt = bpy.props.FloatProperty(
        name="Tilt",
        description="Rotation around the curve tangent",
        default=0.0,
        subtype='ANGLE',
        update=_update_lace_modifier
    )
    
    bpy.types.Scene.spp_lace_normal_mode = bpy.props.EnumProperty(
        name="Normal Mode",
        description="Method to calculate normals along the curve",
        items=[
            ('0', "Minimum Twist", "Use minimum twist for curve normals"),
            ('1', "Z Up", "Align normals with Z-up direction"),
            ('2', "Free", "Free normal direction")
        ],
        default='0',
        update=_update_lace_modifier
    )
    
    bpy.types.Scene.spp_lace_custom_profile = bpy.props.PointerProperty(
        name="Custom Profile",
        description="Object to use as custom profile (only used when Lace Profile is set to Custom)",
        type=bpy.types.Object,
        update=_update_lace_modifier
    )
    
    bpy.types.Scene.spp_lace_material = bpy.props.PointerProperty(
        name="Material",
        description="Material to apply to the lace",
        type=bpy.types.Material,
        update=_update_lace_modifier
    )
    
    bpy.types.Scene.spp_lace_shade_smooth = bpy.props.BoolProperty(
        name="Shade Smooth",
        description="Apply smooth shading to the generated mesh",
        default=True,
        update=_update_lace_modifier
    )
    
    # -------------------------------------------------------------------------
    # Panel identification and naming properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_panel_count = bpy.props.IntProperty(
        name="Panel Count",
        description="Counter for panel numbering",
        default=1,
        min=1
    )
    
    bpy.types.Scene.spp_panel_name = bpy.props.StringProperty(
        name="Panel Name",
        description="Descriptive name for the current panel (e.g., Toecap, Quarter Panel)",
        default="Panel"
    )
    
    # -------------------------------------------------------------------------
    # Target object properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_shell_object = bpy.props.PointerProperty(
        name="Shell Object", 
        description="Target mesh object to project panels onto",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'MESH'
    )
    
    # -------------------------------------------------------------------------
    # Grease Pencil stabilizer properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_use_stabilizer = bpy.props.BoolProperty(
        name="Use Stabilizer", 
        description="Enable stroke stabilization for Grease Pencil",
        default=False, 
        update=update_stabilizer
    )
    
    bpy.types.Scene.spp_stabilizer_radius = bpy.props.IntProperty(
        name="Stabilizer Radius", 
        description="Radius of stabilizer effect in pixels",
        default=10, 
        min=1, 
        max=100, 
        update=update_stabilizer
    )
    
    bpy.types.Scene.spp_stabilizer_factor = bpy.props.FloatProperty(
        name="Stabilizer Factor",
        description="Factor of stabilization effect (0.0 to 1.0)",
        default=0.5,
        min=0.0,
        max=1.0,
    )
    
    bpy.types.Scene.spp_stabilizer_strength_ui = bpy.props.IntProperty(
        name="Stabilizer Strength",
        description="Control stabilizer strength from 1 (low) to 10 (high)",
        default=10,
        min=1,
        max=10,
        update=update_stabilizer_ui
    )
    
    # -------------------------------------------------------------------------
    # Mesh processing properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_reduce_verts = bpy.props.BoolProperty(
        name="Reduce Verts",
        description="Enable vertex reduction options",
        default=False
    )
    
    bpy.types.Scene.spp_smooth_factor = bpy.props.FloatProperty(
        name="Smooth Factor", 
        description="Factor for mesh smoothing operations",
        default=1.0, 
        min=0.0, 
        max=1.0
    )
    
    bpy.types.Scene.spp_grid_fill_span = bpy.props.IntProperty(
        name="Grid Fill Span", 
        description="Span for grid fill operation",
        default=2, 
        min=0, 
        max=100
    )
    
    bpy.types.Scene.spp_decimate_ratio = bpy.props.FloatProperty(
        name="Decimate Ratio", 
        description="How much to simplify the curve (lower = simpler)",
        default=0.5, 
        min=0.01, 
        max=1.0
    )
    
    # -------------------------------------------------------------------------
    # Solidify modifier properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_solidify_thickness = bpy.props.FloatProperty(
        name="Thickness",
        description="Thickness of the solidified panel",
        default=0.01,
        min=0.0,
        unit='LENGTH',
        update=lambda self, context: _update_modifier_if_exists(context, 'Solidify', 'thickness', self.spp_solidify_thickness)
    )
    
    bpy.types.Scene.spp_solidify_offset = bpy.props.FloatProperty(
        name="Offset",
        description="Offset the thickness from the center",
        default=-1.0,
        min=-1.0,
        max=1.0,
        update=lambda self, context: _update_modifier_if_exists(context, 'Solidify', 'offset', self.spp_solidify_offset)
    )
    
    bpy.types.Scene.spp_solidify_even_thickness = bpy.props.BoolProperty(
        name="Even Thickness",
        description="Maintain thickness by adjusting for sharp corners",
        default=True,
        update=lambda self, context: _update_modifier_if_exists(context, 'Solidify', 'use_even_offset', self.spp_solidify_even_thickness)
    )
    
    bpy.types.Scene.spp_solidify_rim = bpy.props.BoolProperty(
        name="Fill Rim",
        description="Fill the rim with faces",
        default=True,
        update=lambda self, context: _update_modifier_if_exists(context, 'Solidify', 'use_rim', self.spp_solidify_rim)
    )
    
    bpy.types.Scene.spp_solidify_rim_only = bpy.props.BoolProperty(
        name="Only Rim",
        description="Only create the rim, without filling the surfaces",
        default=False,
        update=lambda self, context: _update_modifier_if_exists(context, 'Solidify', 'use_rim_only', self.spp_solidify_rim_only)
    )
    
    # -------------------------------------------------------------------------
    # Subdivision properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_panel_add_subdivision = bpy.props.BoolProperty(
        name="Add Subdivision",
        description="Add a Subdivision Surface modifier to the generated panel",
        default=True
    )

    bpy.types.Scene.spp_panel_subdivision_levels = bpy.props.IntProperty(
        name="Subdivision Levels",
        description="Number of subdivision levels to apply",
        default=1,
        min=0,  # Level 0 means no effective subdivision from modifier
        max=6 
    )

    bpy.types.Scene.spp_panel_conform_after_subdivision = bpy.props.BoolProperty(
        name="Conform After Subdivision",
        description="Apply a Shrinkwrap modifier after subdivision to re-conform to the shell",
        default=True
    )

    bpy.types.Scene.spp_panel_shade_smooth = bpy.props.BoolProperty(
        name="Shade Smooth Panel",
        description="Apply smooth shading to the final panel",
        default=True
    )

    # -------------------------------------------------------------------------
    # Curve sampling properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_sampler_fidelity = bpy.props.IntProperty(
        name="Fidelity (Samples)",
        description="Number of evenly spaced samples to create on the curve outline",
        default=64,
        min=8,
        max=512
    )


def _update_modifier_if_exists(context, modifier_name, property_name, value):
    """
    Helper function to update modifier properties if they exist.
    
    This function safely updates a property of a modifier on the active object,
    checking first if the object exists, if it has the specified modifier,
    and if the modifier has the specified property.
    
    Args:
        context (bpy.types.Context): Blender context
        modifier_name (str): Name of the modifier to update
        property_name (str): Name of the property to update
        value: New value for the property
        
    Returns:
        None
        
    Note:
        This function is used by property update callbacks to modify
        modifiers like Solidify, Shrinkwrap, etc. when UI controls change.
    """
    obj = context.active_object
    if obj and modifier_name in obj.modifiers:
        mod = obj.modifiers[modifier_name]
        if hasattr(mod, property_name):
            setattr(mod, property_name, value)
    return None


def _update_lace_modifier(self, context):
    """Callback to update Lace modifier inputs when scene properties change."""
    obj = context.active_object
    if not obj or obj.type != 'CURVE':
        return

    modifier = None
    for mod in obj.modifiers:
        if mod.type == 'NODES' and mod.name.startswith("Lace"):
            modifier = mod
            break

    if modifier:
        try:
            scene = context.scene
            if hasattr(scene, 'spp_lace_profile'):
                modifier["Socket_2"] = int(scene.spp_lace_profile)
            if hasattr(scene, 'spp_lace_scale'):
                modifier["Socket_3"] = scene.spp_lace_scale
            if hasattr(scene, 'spp_lace_resample'):
                modifier["Socket_4"] = scene.spp_lace_resample
            if hasattr(scene, 'spp_lace_tilt'):
                modifier["Socket_5"] = scene.spp_lace_tilt
            if hasattr(scene, 'spp_lace_normal_mode'):
                modifier["Socket_6"] = int(scene.spp_lace_normal_mode)
            if hasattr(scene, 'spp_lace_custom_profile'):
                modifier["Socket_7"] = scene.spp_lace_custom_profile
            if hasattr(scene, 'spp_lace_material'):
                modifier["Socket_8"] = scene.spp_lace_material
            if hasattr(scene, 'spp_lace_shade_smooth'):
                modifier["Socket_9"] = scene.spp_lace_shade_smooth

            # Force refresh
            modifier.show_viewport = False
            modifier.show_viewport = True

        except Exception as e:
            print(f"Error updating Lace modifier: {e}")



def unregister_properties():
    """Unregister all properties used by the SneakerPanel Pro addon."""
    props = [
        # Panel identification
        "spp_panel_count",
        "spp_panel_name",
        "spp_shell_object",
        
        # Grease Pencil stabilizer
        "spp_use_stabilizer",
        "spp_stabilizer_radius",
        "spp_stabilizer_factor",
        "spp_stabilizer_strength_ui",
        
        # Mesh processing
        "spp_reduce_verts",
        "spp_smooth_factor",
        "spp_grid_fill_span",
        "spp_decimate_ratio",
        
        # Solidify
        "spp_solidify_thickness",
        "spp_solidify_offset",
        "spp_solidify_even_thickness",
        "spp_solidify_rim",
        "spp_solidify_rim_only",
        
        # Subdivision
        "spp_panel_add_subdivision",
        "spp_panel_subdivision_levels",
        "spp_panel_conform_after_subdivision",
        "spp_panel_shade_smooth",
        
        # Curve sampling
        "spp_sampler_fidelity"  
    ]
    
    for prop in props:
        if hasattr(bpy.types.Scene, prop):
            delattr(bpy.types.Scene, prop)


def register():
    """Register all properties."""
    register_properties()


def unregister():
    """Unregister all properties."""
    unregister_properties()


if __name__ == "__main__":
    register()
