"""
Properties module for SneakerPanel Pro.

This module defines all the properties used by the SneakerPanel Pro addon,
organized by functionality categories.
"""

import bpy
from .utils.panel_utils import update_stabilizer, update_stabilizer_ui


# Group properties by functionality for better organization
def register_properties():
    """Register all properties used by the SneakerPanel Pro addon."""
    
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
    """Helper function to update modifier properties if they exist.
    
    Args:
        context: Blender context
        modifier_name: Name of the modifier to update
        property_name: Name of the property to update
        value: New value for the property
        
    Returns:
        None
    """
    if (context.active_object and 
            context.active_object.modifiers.get(modifier_name)):
        setattr(context.active_object.modifiers.get(modifier_name), 
                property_name, value)
    return None


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
