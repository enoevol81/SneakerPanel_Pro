
import bpy

from .utils.panel_utils import update_stabilizer, update_stabilizer_ui


def _update_lace_modifier_live(self, context):
    """Live update callback for lace modifier parameters"""
    try:
        obj = context.active_object
        if not obj or obj.type != 'CURVE':
            return
        
        # Find the lace modifier
        modifier = None
        for mod in obj.modifiers:
            if mod.type == 'NODES' and mod.node_group:
                # Check for both old naming and new asset-based node group
                if 'LaceFromCurves' in mod.node_group.name or 'spp_lace' in mod.node_group.name:
                    modifier = mod
                    break
        
        if not modifier:
            return
        
        scene = context.scene
        
        # Use index-based socket access for the asset-based node group
        # Correct socket mapping from geometry node:
        # Socket_2=Scale, Socket_3=Tilt, Socket_4=Normal Mode, Socket_5=Material,
        # Socket_6=Flip Normal, Socket_8=Resample, Socket_9=Shade Smooth,
        # Socket_10=[0,1,2]=Free Normal Controls, Socket_11=Color, Socket_12=Custom Profile
        
        # Profile type (convert enum to integer)
        if hasattr(scene, 'spp_lace_profile'):
            profile_map = {'ROUND': 0, 'OVAL': 0, 'FLAT': 1, 'CUSTOM': 2}
            profile_value = profile_map.get(scene.spp_lace_profile, 0)
            try:
                modifier["Socket_1"] = profile_value
            except:
                # Try named input as fallback
                if "Lace Profile" in modifier:
                    modifier["Lace Profile"] = profile_value
        
        # Scale
        if hasattr(scene, 'spp_lace_scale'):
            try:
                modifier["Socket_2"] = scene.spp_lace_scale
            except:
                if "Scale" in modifier:
                    modifier["Scale"] = scene.spp_lace_scale
        
        # Tilt - Socket_3
        if hasattr(scene, 'spp_lace_tilt'):
            try:
                modifier["Socket_3"] = scene.spp_lace_tilt
            except:
                if "Tilt" in modifier:
                    modifier["Tilt"] = scene.spp_lace_tilt
        
        # Normal Mode - Socket_4 (convert string to integer)
        if hasattr(scene, 'spp_lace_normal_mode'):
            # Ensure we convert string to int: '0'->0, '1'->1, '2'->2
            normal_value = int(scene.spp_lace_normal_mode) if isinstance(scene.spp_lace_normal_mode, str) else scene.spp_lace_normal_mode
            try:
                modifier["Socket_4"] = normal_value
            except:
                if "Normal Mode" in modifier:
                    modifier["Normal Mode"] = normal_value
        
        # Resample - Socket_8
        if hasattr(scene, 'spp_lace_resample'):
            try:
                modifier["Socket_8"] = scene.spp_lace_resample
            except:
                if "Resample" in modifier:
                    modifier["Resample"] = scene.spp_lace_resample
        
        # Material - Socket_5 (use default lace material)
        try:
            default_material = bpy.data.materials.get("spp_lace_material")
            if default_material:
                modifier["Socket_5"] = default_material
        except:
            if "Material" in modifier:
                default_material = bpy.data.materials.get("spp_lace_material")
                if default_material:
                    modifier["Material"] = default_material
        
        # Flip Normal - Socket_6
        if hasattr(scene, 'spp_lace_flip_normal'):
            try:
                modifier["Socket_6"] = scene.spp_lace_flip_normal
            except:
                if "Flip Normal" in modifier:
                    modifier["Flip Normal"] = scene.spp_lace_flip_normal
        
        # Shade Smooth - Socket_9
        if hasattr(scene, 'spp_lace_shade_smooth'):
            try:
                modifier["Socket_9"] = scene.spp_lace_shade_smooth
            except:
                if "Shade Smooth" in modifier:
                    modifier["Shade Smooth"] = scene.spp_lace_shade_smooth
        
        # Free Normal Controls - Socket_10 [0,1,2] (only when Normal Mode is Free)
        if hasattr(scene, 'spp_lace_free_normal') and scene.spp_lace_normal_mode == '2':
            try:
                modifier["Socket_10"] = scene.spp_lace_free_normal
            except:
                if "Free Normal Controls" in modifier:
                    modifier["Free Normal Controls"] = scene.spp_lace_free_normal
        
        # Color - Socket_11
        if hasattr(scene, 'spp_lace_color'):
            try:
                modifier["Socket_11"] = scene.spp_lace_color
            except:
                if "Color" in modifier:
                    modifier["Color"] = scene.spp_lace_color
        
        # Custom Profile - Socket_12 (only if CUSTOM is selected)
        if hasattr(scene, 'spp_lace_custom_profile') and scene.spp_lace_profile == 'CUSTOM':
            profile_set = False
            # Try multiple possible input names for custom profile
            for socket_name in ["Socket_12", "Custom Profile", "Object", "Profile Object", "Profile"]:
                try:
                    if socket_name in modifier:
                        modifier[socket_name] = scene.spp_lace_custom_profile
                        profile_set = True
                        break
                except:
                    continue
            
            if not profile_set:
                print(f"Warning: Could not set custom profile in live update")
        
        # Force viewport update without toggling modifier visibility
        if hasattr(context, 'view_layer'):
            context.view_layer.update()
        
        # Tag areas for redraw
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        
    except Exception as e:
        # Catch all exceptions to prevent panel collapse
        print(f"Warning in lace modifier update: {e}")
        # Do NOT raise the exception - this prevents panel collapse


def _update_reference_image_opacity(self, context):
    """Update opacity of reference image materials in real-time"""
    opacity_value = getattr(context.scene, "spp_reference_image_opacity", 1.0)
    
    # Find all UV-specific reference materials and update their opacity
    for material in bpy.data.materials:
        if material.name.startswith("Reference Image UV -") and material.use_nodes:
            nodes = material.node_tree.nodes
            bsdf = nodes.get("Principled BSDF")
            if bsdf and "Alpha" in bsdf.inputs:
                bsdf.inputs["Alpha"].default_value = opacity_value
            
            # Also update math node if it exists (for image alpha multiplication)
            for node in nodes:
                if node.type == 'MATH' and node.operation == 'MULTIPLY':
                    if len(node.inputs) > 1:
                        node.inputs[1].default_value = opacity_value
    
    # Force viewport update
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()


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
            ('ROUND', "Round", "Circular lace profile"),
            ('OVAL', "Oval", "Oval/elliptical lace profile"),
            ('FLAT', "Flat", "Flat rectangular lace profile"),
            ('CUSTOM', "Custom", "Custom profile from another object"),
        ],
        default='ROUND',
        update=_update_lace_modifier_live,
    )

    bpy.types.Scene.spp_lace_scale = bpy.props.FloatProperty(
        name="Scale",
        description="Size of the lace profile",
        default=0.05,
        min=0.001,
        max=10.0,
        precision=3,
        update=_update_lace_modifier_live,
    )

    bpy.types.Scene.spp_lace_resample = bpy.props.IntProperty(
        name="Resample",
        description="Number of points to resample the curve with",
        default=64,
        min=1,
        max=1000,
        update=_update_lace_modifier_live,
    )

    bpy.types.Scene.spp_lace_tilt = bpy.props.FloatProperty(
        name="Tilt",
        description="Rotation around the curve tangent",
        default=0.0,
        subtype="ANGLE",
        update=_update_lace_modifier_live,
    )

    bpy.types.Scene.spp_lace_normal_mode = bpy.props.EnumProperty(
        name="Normal Mode",
        description="Method to calculate normals along the curve",
        items=[
            ('0', "Minimum Twist", "Use minimum twist for curve normals"),
            ('1', "Z Up", "Align normals with Z-up direction"),
            ('2', "Free", "Free normal direction"),
        ],
        default='0',
        update=_update_lace_modifier_live,
    )

    bpy.types.Scene.spp_lace_custom_profile = bpy.props.PointerProperty(
        name="Custom Profile",
        description="Object to use as custom profile (only used when Lace Profile is set to Custom)",
        type=bpy.types.Object,
    )

    # Custom material property removed - using default lace material only

    bpy.types.Scene.spp_lace_shade_smooth = bpy.props.BoolProperty(
        name="Shade Smooth",
        description="Apply smooth shading to the generated mesh",
        default=True,
        update=_update_lace_modifier_live,
    )
    
    # Additional lace properties for new asset-based system
    bpy.types.Scene.spp_lace_free_normal = bpy.props.FloatVectorProperty(
        name="Free Normal",
        description="Free normal control vector",
        default=(0.0, 0.0, 1.0),
        subtype='DIRECTION',
        size=3,
        update=_update_lace_modifier_live,
    )
    
    bpy.types.Scene.spp_lace_flip_v = bpy.props.BoolProperty(
        name="Flip V",
        description="Flip UV V coordinate",
        default=False,
        update=_update_lace_modifier_live,
    )
    
    bpy.types.Scene.spp_lace_flip_normal = bpy.props.BoolProperty(
        name="Flip Normal",
        description="Flip face normals",
        default=False,
        update=_update_lace_modifier_live,
    )
    
    bpy.types.Scene.spp_lace_color = bpy.props.FloatVectorProperty(
        name="Lace Color",
        description="Color tint for the lace",
        default=(0.8, 0.8, 0.8, 1.0),
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        update=_update_lace_modifier_live,
    )
    
    # Use custom material property removed - using default lace material only

    # -------------------------------------------------------------------------
    # Panel identification and naming properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_panel_count = bpy.props.IntProperty(
        name="Panel Count", description="Counter for panel numbering", default=1, min=1
    )

    bpy.types.Scene.spp_panel_name = bpy.props.StringProperty(
        name="Panel Name",
        description="Descriptive name for the current panel (e.g., Toecap, Quarter Panel)",
        default="Panel",
    )
    # -------------------------------------------------------------------------
    # --- UI tooltip toggles
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_show_mirror_tooltip = bpy.props.BoolProperty(
        name="Show Mirror at Cursor Tooltip",
        default=False,
        description="Show helpful tips for the Mirror at Cursor function",
    )
    bpy.types.Scene.spp_show_uv_gen_tooltip = bpy.props.BoolProperty(
        name="Show UV Generation Tooltip",
        default=False,
        description="Show helpful tips for the Shell UV Generation workflow",
    )
    bpy.types.Scene.spp_show_gp_tooltip = bpy.props.BoolProperty(
        name="Show Grease Pencil Drawing Tooltip",
        default=False,
        description="Show helpful tips for drawing panels with Grease Pencil",
    )
    bpy.types.Scene.spp_show_helper_tooltip = bpy.props.BoolProperty(
        name="Show Helper Tooltip",
        default=False,
        description="Show helpful tips for the Helper Tools",
    )
    bpy.types.Scene.spp_show_surface_workflow_tooltip = bpy.props.BoolProperty(
        name="Show Surface Workflow Tooltip",
        default=False,
        description="Show helpful tips for the Surface Workflow",
    )
    bpy.types.Scene.spp_show_uv_workflow_tooltip = bpy.props.BoolProperty(
        name="Show UV Workflow Tooltip",
        default=False,
        description="Show helpful tips for the UV Workflow",
    )
    bpy.types.Scene.spp_show_lace_gen_tooltip = bpy.props.BoolProperty(
        name="Show Lace Generator Tooltip",
        default=False,
        description="Show helpful tips for the Lace Generator",
    )
    bpy.types.Scene.spp_show_profile_proj_tooltip = bpy.props.BoolProperty(
        name="Show Profile Projection Tooltip",
        default=False,
        description="Show helpful tips for the Profile Projection",
    )

    # -------------------------------------------------------------------------
    # Target object properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_shell_object = bpy.props.PointerProperty(
        name="Shell Object",
        description="Target mesh object to project panels onto",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == "MESH",
    )

    # -------------------------------------------------------------------------
    # Grease Pencil stabilizer properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_use_stabilizer = bpy.props.BoolProperty(
        name="Use Stabilizer",
        description="Enable stroke stabilization for Grease Pencil",
        default=False,
        update=update_stabilizer,
    )

    bpy.types.Scene.spp_stabilizer_radius = bpy.props.IntProperty(
        name="Stabilizer Radius",
        description="Radius of stabilizer effect in pixels",
        default=10,
        min=1,
        max=100,
        update=update_stabilizer,
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
        update=update_stabilizer_ui,
    )

    # -------------------------------------------------------------------------
    # Mesh processing properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_reduce_verts = bpy.props.BoolProperty(
        name="Reduce Verts",
        description="Enable vertex reduction options",
        default=False,
    )

    bpy.types.Scene.spp_smooth_factor = bpy.props.FloatProperty(
        name="Smooth Factor",
        description="Factor for mesh smoothing operations",
        default=1.0,
        min=0.0,
        max=1.0,
    )

    bpy.types.Scene.spp_grid_fill_span = bpy.props.IntProperty(
        name="Grid Fill Span",
        description="Span for grid fill operation",
        default=2,
        min=0,
        max=100,
    )

    bpy.types.Scene.spp_decimate_ratio = bpy.props.FloatProperty(
        name="Decimate Ratio",
        description="How much to simplify the curve (lower = simpler)",
        default=0.5,
        min=0.01,
        max=1.0,
    )

    # -------------------------------------------------------------------------
    # Curve processing properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_curve_cyclic = bpy.props.BoolProperty(
        name="Cyclic Curve",
        description="Make curve cyclic (closed loop) or open. Disable for half-curve mirror operations",
        default=True,
        update=_update_curve_cyclic,
    )

    # -------------------------------------------------------------------------
    # Solidify modifier properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_solidify_thickness = bpy.props.FloatProperty(
        name="Thickness",
        description="Thickness of the solidified panel",
        default=0.01,
        min=0.0,
        unit="LENGTH",
        update=lambda self, context: _update_modifier_if_exists(
            context, "Solidify", "thickness", self.spp_solidify_thickness
        ),
    )

    bpy.types.Scene.spp_solidify_offset = bpy.props.FloatProperty(
        name="Offset",
        description="Offset the thickness from the center",
        default=-1.0,
        min=-1.0,
        max=1.0,
        update=lambda self, context: _update_modifier_if_exists(
            context, "Solidify", "offset", self.spp_solidify_offset
        ),
    )

    bpy.types.Scene.spp_solidify_even_thickness = bpy.props.BoolProperty(
        name="Even Thickness",
        description="Maintain thickness by adjusting for sharp corners",
        default=True,
        update=lambda self, context: _update_modifier_if_exists(
            context, "Solidify", "use_even_offset", self.spp_solidify_even_thickness
        ),
    )

    bpy.types.Scene.spp_solidify_rim = bpy.props.BoolProperty(
        name="Fill Rim",
        description="Fill the rim with faces",
        default=True,
        update=lambda self, context: _update_modifier_if_exists(
            context, "Solidify", "use_rim", self.spp_solidify_rim
        ),
    )

    bpy.types.Scene.spp_solidify_rim_only = bpy.props.BoolProperty(
        name="Only Rim",
        description="Only create the rim, without filling the surfaces",
        default=False,
        update=lambda self, context: _update_modifier_if_exists(
            context, "Solidify", "use_rim_only", self.spp_solidify_rim_only
        ),
    )

    # -------------------------------------------------------------------------
    # Subdivision properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_panel_add_subdivision = bpy.props.BoolProperty(
        name="Add Subdivision",
        description="Add a Subdivision Surface modifier to the generated panel",
        default=True,
    )

    bpy.types.Scene.spp_panel_subdivision_levels = bpy.props.IntProperty(
        name="Subdivision Levels",
        description="Number of subdivision levels to apply",
        default=1,
        min=0,  # Level 0 means no effective subdivision from modifier
        max=6,
    )

    bpy.types.Scene.spp_panel_conform_after_subdivision = bpy.props.BoolProperty(
        name="Conform After Subdivision",
        description="Apply a Shrinkwrap modifier after subdivision to re-conform to the shell",
        default=True,
    )

    bpy.types.Scene.spp_panel_shade_smooth = bpy.props.BoolProperty(
        name="Shade Smooth Panel",
        description="Apply smooth shading to the final panel",
        default=True,
    )

    # -------------------------------------------------------------------------
    # Curve sampling properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_sampler_fidelity = bpy.props.IntProperty(
        name="Fidelity (Samples)",
        description="Number of evenly spaced samples to create on the curve outline",
        default=64,
        min=3,
        max=256,
    )

    # -------------------------------------------------------------------------
    # Reference image overlay properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_use_reference_image_overlay = bpy.props.BoolProperty(
        name="Apply Reference Image",
        description="Apply 'Reference Image' material to UV mesh if available",
        default=False
    )

    bpy.types.Scene.spp_reference_image_opacity = bpy.props.FloatProperty(
        name="Opacity",
        description="Opacity of the reference image overlay",
        default=0.5,
        min=0.0,
        max=1.0,
        step=0.01,
        precision=2,
        update=_update_reference_image_opacity
    )

    # -------------------------------------------------------------------------
    # Surface workflow collapsible section properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_show_stabilizer_settings = bpy.props.BoolProperty(
        name="Show Stabilizer Settings",
        description="Show/hide stabilizer settings section",
        default=False
    )

    bpy.types.Scene.spp_show_curve_editing_tools = bpy.props.BoolProperty(
        name="Show Curve Editing Tools",
        description="Show/hide curve editing tools section",
        default=False
    )

    bpy.types.Scene.spp_show_refine_mesh = bpy.props.BoolProperty(
        name="Show Refine Mesh",
        description="Show/hide refine mesh section",
        default=False
    )

    # -------------------------------------------------------------------------
    # Retopology viewport helper properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_show_retopology = bpy.props.BoolProperty(
        name="Show Retopology",
        description="Show/hide retopology section",
        default=False
    )

    # -------------------------------------------------------------------------
    # Main panel collapsible section properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_show_edge_refinement = bpy.props.BoolProperty(
        name="Show Edge & Loop Refinement",
        description="Show/hide edge and loop refinement section",
        default=False
    )

    bpy.types.Scene.spp_show_mesh_object = bpy.props.BoolProperty(
        name="Show Mesh Object",
        description="Show/hide mesh object section",
        default=False
    )

    # -------------------------------------------------------------------------
    # UV workflow collapsible section properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_show_uv_stabilizer_settings = bpy.props.BoolProperty(
        name="Show UV Stabilizer Settings",
        description="Show/hide UV stabilizer settings section",
        default=False
    )

    bpy.types.Scene.spp_show_uv_curve_editing_tools = bpy.props.BoolProperty(
        name="Show UV Curve Editing Tools",
        description="Show/hide UV curve editing tools section",
        default=False
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



def _update_curve_cyclic(self, context):
    """Callback to update curve cyclic property when scene property changes."""
    obj = context.active_object
    if not obj or obj.type != "CURVE":
        return

    # Update all splines in the curve
    for spline in obj.data.splines:
        spline.use_cyclic_u = context.scene.spp_curve_cyclic

    # Force viewport update
    context.view_layer.update()


def unregister_properties():
    """Unregister all properties used by the SneakerPanel Pro addon."""
    props = [
        # Lace generator properties
        "spp_lace_profile",
        "spp_lace_scale", 
        "spp_lace_resample",
        "spp_lace_tilt",
        "spp_lace_normal_mode",
        "spp_lace_custom_profile",
        "spp_lace_custom_material",
        "spp_lace_shade_smooth",
        "spp_lace_free_normal",
        "spp_lace_flip_v",
        "spp_lace_flip_normal",
        "spp_lace_color",
        "spp_lace_use_custom_material",
        # Panel identification
        "spp_panel_count",
        "spp_panel_name",
        "spp_shell_object",
        # --- UI tooltip toggles
        "spp_show_mirror_tooltip",
        "spp_show_uv_gen_tooltip",
        "spp_show_gp_tooltip",
        "spp_show_helper_tooltip",
        "spp_show_surface_workflow_tooltip",
        "spp_show_uv_workflow_tooltip",
        "spp_show_lace_gen_tooltip",
        "spp_show_profile_proj_tooltip",
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
        # Curve processing
        "spp_curve_cyclic",
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
        "spp_sampler_fidelity",
        # Reference image overlay
        "spp_use_reference_image_overlay",
        "spp_reference_image_opacity",
        # Surface workflow collapsible sections
        "spp_show_stabilizer_settings",
        "spp_show_curve_editing_tools", 
        "spp_show_refine_mesh",
        # Retopology viewport helper
        "spp_show_retopology",
        # Main panel collapsible sections
        "spp_show_edge_refinement",
        "spp_show_mesh_object",
        # UV workflow collapsible sections
        "spp_show_uv_stabilizer_settings",
        "spp_show_uv_curve_editing_tools",
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
