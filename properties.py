import bpy
from .utils.panel_utils import update_stabilizer, update_stabilizer_ui


# -----------------------------------------------------------------------------
# Utility functions and targeted update callbacks for the lace generator.
#
# The original live update function updated **all** inputs on every change,
# which caused user‑adjusted values (e.g. scale, resample, tilt) to be reset
# whenever another property (such as the free normal) changed.  The new
# approach defines per‑property update functions that only modify the
# corresponding socket on the active lace modifier.  This prevents unrelated
# inputs from being overwritten and restores proper live editing behaviour.


# Helper to find the first SPP lace modifier on the active curve
def _get_lace_modifier(context):
    obj = context.active_object
    if not obj or obj.type != "CURVE":
        return None
    for mod in obj.modifiers:
        if mod.type == "NODES" and mod.node_group:
            if (
                "LaceFromCurves" in mod.node_group.name
                or "spp_lace" in mod.node_group.name
            ):
                return mod
    return None


# Profile update: set the profile type and (for custom) the profile object
def _update_lace_profile(self, context):
    mod = _get_lace_modifier(context)
    if not mod:
        return
    scene = context.scene
    # Map enum to integer expected by the node group
    profile_map = {"ROUND": 0, "OVAL": 0, "FLAT": 1, "CUSTOM": 2}
    profile_value = profile_map.get(scene.spp_lace_profile, 0)
    try:
        mod["Socket_1"] = profile_value
    except Exception:
        if "Lace Profile" in mod:
            mod["Lace Profile"] = profile_value
    # If custom, set the custom profile object
    if scene.spp_lace_profile == "CUSTOM" and scene.spp_lace_custom_profile:
        for socket_name in [
            "Socket_12",
            "Custom Profile",
            "Object",
            "Profile Object",
            "Profile",
        ]:
            try:
                if socket_name in mod:
                    mod[socket_name] = scene.spp_lace_custom_profile
                    break
            except Exception:
                continue
    # Refresh viewport
    if hasattr(context, "view_layer"):
        context.view_layer.update()
    for area in context.screen.areas:
        if area.type == "VIEW_3D":
            area.tag_redraw()


# Scale update
def _update_lace_scale(self, context):
    mod = _get_lace_modifier(context)
    if not mod:
        return
    scene = context.scene
    try:
        mod["Socket_2"] = scene.spp_lace_scale
    except Exception:
        if "Scale" in mod:
            mod["Scale"] = scene.spp_lace_scale
    # Refresh viewport
    if hasattr(context, "view_layer"):
        context.view_layer.update()
    for area in context.screen.areas:
        if area.type == "VIEW_3D":
            area.tag_redraw()


# Resample update
def _update_lace_resample(self, context):
    mod = _get_lace_modifier(context)
    if not mod:
        return
    scene = context.scene
    try:
        mod["Socket_8"] = scene.spp_lace_resample
    except Exception:
        if "Resample" in mod:
            mod["Resample"] = scene.spp_lace_resample
    # Refresh viewport
    if hasattr(context, "view_layer"):
        context.view_layer.update()
    for area in context.screen.areas:
        if area.type == "VIEW_3D":
            area.tag_redraw()


# Tilt update
def _update_lace_tilt(self, context):
    mod = _get_lace_modifier(context)
    if not mod:
        return
    scene = context.scene
    try:
        mod["Socket_3"] = scene.spp_lace_tilt
    except Exception:
        if "Tilt" in mod:
            mod["Tilt"] = scene.spp_lace_tilt
    # Refresh viewport
    if hasattr(context, "view_layer"):
        context.view_layer.update()
    for area in context.screen.areas:
        if area.type == "VIEW_3D":
            area.tag_redraw()


# --- REPLACE in properties.py ----------------------------------------------


def _set_modifier_input_vec(mod, names, vec):
    """Try multiple key names (and per-axis fallbacks) to set a vector."""
    # 1) direct vector sockets
    for key in names:
        if key in mod:
            mod[key] = vec
            return True

    # 2) per-axis fallback (e.g. "Free Normal X", "Free Normal Y", "Free Normal Z")
    axis_keys_sets = [
        ("Free Normal X", "Free Normal Y", "Free Normal Z"),
        ("Free X", "Free Y", "Free Z"),
        ("Socket_10.0", "Socket_10.1", "Socket_10.2"),
    ]
    for xk, yk, zk in axis_keys_sets:
        if xk in mod and yk in mod and zk in mod:
            mod[xk], mod[yk], mod[zk] = vec[0], vec[1], vec[2]
            return True

    return False


def _force_modifier_recalc(context, obj, mod):
    """Rock-solid refresh: toggle viewport, bump frame, tag updates."""
    try:
        if obj:
            obj.update_tag()
        dg = context.evaluated_depsgraph_get()
        dg.update()

        if mod:
            orig = mod.show_viewport
            mod.show_viewport = False
            context.view_layer.update()
            mod.show_viewport = orig

            if mod.node_group:
                mod.node_group.update_tag()

        # bump the frame to trigger GN
        scn = context.scene
        scn.frame_set(scn.frame_current)

        # redraw 3D views
        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()

        if hasattr(context, "view_layer"):
            context.view_layer.update()

    except Exception as e:
        print(f"[SPP] Recalc refresh failed: {e}")


def _update_lace_normal_mode(self, context):
    mod = _get_lace_modifier(context)
    if not mod:
        return
    scene = context.scene
    # Ensure integer for the modifier input
    normal_value = (
        int(scene.spp_lace_normal_mode)
        if isinstance(scene.spp_lace_normal_mode, str)
        else scene.spp_lace_normal_mode
    )

    # Write to either Socket_4 or the named input
    wrote = False
    for key in ("Socket_4", "Normal Mode"):
        if key in mod:
            mod[key] = normal_value
            wrote = True
            break

    if not wrote:
        print("[SPP] Normal Mode input not found on modifier (Socket_4/Normal Mode).")

    # If switching to Free, immediately push the current free vector as well
    if normal_value == 2:
        _update_lace_free_normal(self, context)
    else:
        _force_modifier_recalc(context, context.active_object, mod)


def _update_lace_free_normal(self, context):
    mod = _get_lace_modifier(context)
    if not mod:
        return

    scene = context.scene
    obj = context.active_object

    # Always force modifier’s Normal Mode = Free (2) to ensure GN uses this branch.
    for key in ("Socket_4", "Normal Mode"):
        if key in mod:
            try:
                mod[key] = 2
                break
            except Exception:
                pass

    vec = scene.spp_lace_free_normal

    # Robust name matching across asset variants
    candidates = ("Socket_10", "Free Normal Controls", "Free Normal")
    ok = _set_modifier_input_vec(mod, candidates, vec)

    if not ok:
        # Log available keys once for debugging
        print(
            "[SPP] Could not find a Free Normal input. Available keys:",
            list(mod.keys()),
        )
        return

    _force_modifier_recalc(context, obj, mod)


# --- END REPLACE ------------------------------------------------------------


# Flip normal update
def _update_lace_flip_normal(self, context):
    mod = _get_lace_modifier(context)
    if not mod:
        return
    scene = context.scene
    try:
        mod["Socket_6"] = scene.spp_lace_flip_normal
    except Exception:
        if "Flip Normal" in mod:
            mod["Flip Normal"] = scene.spp_lace_flip_normal
    # Refresh viewport
    if hasattr(context, "view_layer"):
        context.view_layer.update()
    for area in context.screen.areas:
        if area.type == "VIEW_3D":
            area.tag_redraw()


# Shade smooth update
def _update_lace_shade_smooth(self, context):
    mod = _get_lace_modifier(context)
    if not mod:
        return
    scene = context.scene
    try:
        mod["Socket_9"] = scene.spp_lace_shade_smooth
    except Exception:
        if "Shade Smooth" in mod:
            mod["Shade Smooth"] = scene.spp_lace_shade_smooth
    # Refresh viewport
    if hasattr(context, "view_layer"):
        context.view_layer.update()
    for area in context.screen.areas:
        if area.type == "VIEW_3D":
            area.tag_redraw()


# Color update
def _update_lace_color(self, context):
    mod = _get_lace_modifier(context)
    if not mod:
        return
    scene = context.scene
    try:
        mod["Socket_11"] = scene.spp_lace_color
    except Exception:
        if "Color" in mod:
            mod["Color"] = scene.spp_lace_color
    # Refresh viewport
    if hasattr(context, "view_layer"):
        context.view_layer.update()
    for area in context.screen.areas:
        if area.type == "VIEW_3D":
            area.tag_redraw()


# Custom profile update (used when the user changes the custom profile field
# after applying the modifier)
def _update_lace_custom_profile(self, context):
    mod = _get_lace_modifier(context)
    if not mod:
        return
    scene = context.scene
    if scene.spp_lace_profile != "CUSTOM" or not scene.spp_lace_custom_profile:
        return
    for socket_name in [
        "Socket_12",
        "Custom Profile",
        "Object",
        "Profile Object",
        "Profile",
    ]:
        try:
            if socket_name in mod:
                mod[socket_name] = scene.spp_lace_custom_profile
                break
        except Exception as e:
            print(f"Failed to set custom profile via {socket_name}: {e}")
            continue
    # Refresh viewport
    if hasattr(context, "view_layer"):
        context.view_layer.update()
    for area in context.screen.areas:
        if area.type == "VIEW_3D":
            area.tag_redraw()


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
                if node.type == "MATH" and node.operation == "MULTIPLY":
                    if len(node.inputs) > 1:
                        node.inputs[1].default_value = opacity_value

    # Force viewport update
    for area in context.screen.areas:
        if area.type == "VIEW_3D":
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
            ("ROUND", "Round", "Circular lace profile"),
            ("OVAL", "Oval", "Oval/elliptical lace profile"),
            ("FLAT", "Flat", "Flat rectangular lace profile"),
            ("CUSTOM", "Custom", "Custom profile from another object"),
        ],
        default="ROUND",
        # Update only the profile and custom profile socket when this changes
        update=_update_lace_profile,
    )

    bpy.types.Scene.spp_lace_scale = bpy.props.FloatProperty(
        name="Scale",
        description="Size of the lace profile",
        default=0.05,
        min=0.001,
        max=10.0,
        precision=3,
        # Update only the scale socket when this changes
        update=_update_lace_scale,
    )

    bpy.types.Scene.spp_lace_resample = bpy.props.IntProperty(
        name="Resample",
        description="Number of points to resample the curve with",
        default=64,
        min=1,
        max=1000,
        # Update only the resample socket when this changes
        update=_update_lace_resample,
    )

    bpy.types.Scene.spp_lace_tilt = bpy.props.FloatProperty(
        name="Tilt",
        description="Rotation around the curve tangent",
        default=0.0,
        subtype="ANGLE",
        # Update only the tilt socket when this changes
        update=_update_lace_tilt,
    )

    bpy.types.Scene.spp_lace_normal_mode = bpy.props.EnumProperty(
        name="Normal Mode",
        description="Method to calculate normals along the curve",
        items=[
            ("0", "Minimum Twist", "Use minimum twist for curve normals"),
            ("1", "Z Up", "Align normals with Z-up direction"),
            ("2", "Free", "Free normal direction"),
        ],
        default="0",
        # Update only the normal mode socket when this changes, and refresh free normal if needed
        update=_update_lace_normal_mode,
    )

    bpy.types.Scene.spp_lace_custom_profile = bpy.props.PointerProperty(
        name="Custom Profile",
        description="Object to use as custom profile (only used when Lace Profile is set to Custom)",
        type=bpy.types.Object,
        # Update the custom profile socket when this changes and the profile is set to CUSTOM
        update=_update_lace_custom_profile,
    )

    # Custom material property removed - using default lace material only

    bpy.types.Scene.spp_lace_shade_smooth = bpy.props.BoolProperty(
        name="Shade Smooth",
        description="Apply smooth shading to the generated mesh",
        default=True,
        # Update only the shade smooth socket when this changes
        update=_update_lace_shade_smooth,
    )

    # Additional lace properties for new asset-based system
    bpy.types.Scene.spp_lace_free_normal = bpy.props.FloatVectorProperty(
        name="Free Normal",
        description="Free normal control vector - use the shader ball to interactively adjust direction",
        default=(0.0, 0.0, 1.0),
        subtype="DIRECTION",
        size=3,
        min=-1.0,
        max=1.0,
        # Update only the free normal socket when this changes and normal mode is set to Free
        update=_update_lace_free_normal,
    )

    bpy.types.Scene.spp_lace_flip_v = bpy.props.BoolProperty(
        name="Flip V",
        description="Flip UV V coordinate",
        default=False,
        update=None,
    )

    bpy.types.Scene.spp_lace_flip_normal = bpy.props.BoolProperty(
        name="Flip Normal",
        description="Flip face normals",
        default=False,
        # Update only the flip normal socket when this changes
        update=_update_lace_flip_normal,
    )

    bpy.types.Scene.spp_lace_color = bpy.props.FloatVectorProperty(
        name="Lace Color",
        description="Color tint for the lace",
        default=(0.8, 0.8, 0.8, 1.0),
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        # Update only the color socket when this changes
        update=_update_lace_color,
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
    # Boolean Builder properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_boolean_state = bpy.props.EnumProperty(
        name="Boolean Builder State",
        description="Current state of the boolean builder",
        items=[
            ("NONE", "None", "Boolean builder not active"),
            ("SELECT_MAIN", "Select Main", "Select main panel object"),
            ("SELECT_TARGET", "Select Target", "Select object to subtract"),
            ("READY_TO_BOOLEAN", "Ready", "Ready to create boolean operation"),
        ],
        default="NONE",
    )

    bpy.types.Scene.spp_boolean_main_object = bpy.props.StringProperty(
        name="Boolean Main Object",
        description="Name of the main object for boolean operation",
        default="",
    )

    bpy.types.Scene.spp_boolean_target_object = bpy.props.StringProperty(
        name="Boolean Target Object", 
        description="Name of the target object for boolean operation",
        default="",
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
        default=False,
    )

    bpy.types.Scene.spp_reference_image_opacity = bpy.props.FloatProperty(
        name="Opacity",
        description="Opacity of the reference image overlay",
        default=0.5,
        min=0.0,
        max=1.0,
        step=0.01,
        precision=2,
        update=_update_reference_image_opacity,
    )

    # -------------------------------------------------------------------------
    # Surface workflow collapsible section properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_show_stabilizer_settings = bpy.props.BoolProperty(
        name="Show Stabilizer Settings",
        description="Show/hide stabilizer settings section",
        default=False,
    )

    bpy.types.Scene.spp_show_curve_editing_tools = bpy.props.BoolProperty(
        name="Show Curve Editing Tools",
        description="Show/hide curve editing tools section",
        default=False,
    )

    bpy.types.Scene.spp_show_refine_mesh = bpy.props.BoolProperty(
        name="Show Refine Mesh",
        description="Show/hide refine mesh section",
        default=False,
    )

    # -------------------------------------------------------------------------
    # Retopology viewport helper properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_show_retopology = bpy.props.BoolProperty(
        name="Show Retopology",
        description="Show/hide retopology section",
        default=False,
    )

    # -------------------------------------------------------------------------
    # Main panel collapsible section properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_show_edge_refinement = bpy.props.BoolProperty(
        name="Show Edge & Loop Refinement",
        description="Show/hide edge and loop refinement section",
        default=False,
    )

    bpy.types.Scene.spp_show_mesh_object = bpy.props.BoolProperty(
        name="Show Mesh Object",
        description="Show/hide mesh object section",
        default=False,
    )

    # -------------------------------------------------------------------------
    # UV workflow collapsible section properties
    # -------------------------------------------------------------------------
    bpy.types.Scene.spp_show_uv_stabilizer_settings = bpy.props.BoolProperty(
        name="Show UV Stabilizer Settings",
        description="Show/hide UV stabilizer settings section",
        default=False,
    )

    bpy.types.Scene.spp_show_uv_curve_editing_tools = bpy.props.BoolProperty(
        name="Show UV Curve Editing Tools",
        description="Show/hide UV curve editing tools section",
        default=False,
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
        # Boolean Builder
        "spp_boolean_state",
        "spp_boolean_main_object", 
        "spp_boolean_target_object",
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
