"""
Apply operator for SPP Lace Generator
Applies geometry nodes modifier with selected lace profile to curve objects
"""

import bpy
from bpy.types import Operator
from bpy.props import EnumProperty, FloatProperty, IntProperty, BoolProperty, PointerProperty, FloatVectorProperty
from .spp_lace_loader import ensure_lace_assets


class SPP_OT_apply_lace(Operator):
    """Apply lace geometry to selected curve"""
    bl_idname = "spp.apply_lace"
    bl_label = "Apply Lace"
    bl_options = {'REGISTER', 'UNDO'}
    
    lace_type: EnumProperty(
        name="Lace Type",
        description="Type of lace profile to apply",
        items=[
            ('ROUND', "Round", "Round lace profile"),
            ('OVAL', "Oval", "Oval lace profile"),
            ('FLAT', "Flat", "Flat lace profile"),
            ('CUSTOM', "Custom", "Custom curve profile")
        ],
        default='ROUND'
    )
    
    resample: IntProperty(
        name="Resample",
        description="Number of samples along curve",
        default=110,
        min=2,
        max=500
    )
    
    scale: FloatProperty(
        name="Scale",
        description="Lace width scaling",
        default=1.0,
        min=0.01,
        max=10.0
    )
    
    tilt: FloatProperty(
        name="Tilt",
        description="Tilt angle along curve",
        default=0.0,
        subtype='ANGLE'
    )
    
    normal_mode: EnumProperty(
        name="Normal Mode",
        description="Normal calculation mode",
        items=[
            ('0', "Minimum Twist", "Minimum twist normal mode"),
            ('1', "Z Up", "Z up normal mode"),
            ('2', "Free", "Free normal mode with custom control")
        ],
        default='0'
    )
    
    free_normal: FloatVectorProperty(
        name="Free Normal",
        description="Free normal control vector (only used when Normal Mode is Free)",
        default=(0.0, 0.0, 1.0),
        subtype='DIRECTION',
        size=3
    )
    
    flip_v: BoolProperty(
        name="Flip V",
        description="Flip UV V coordinate",
        default=False
    )
    
    flip_normal: BoolProperty(
        name="Flip Normal",
        description="Flip face normals",
        default=False
    )
    
    shade_smooth: BoolProperty(
        name="Shade Smooth",
        description="Apply smooth shading",
        default=True
    )
    
    use_default_material: BoolProperty(
        name="Use Default Material",
        description="Use the default spp_lace_material",
        default=True
    )
    
    custom_material: PointerProperty(
        name="Material",
        description="Custom material to use",
        type=bpy.types.Material
    )
    
    custom_profile: bpy.props.StringProperty(
        name="Custom Profile",
        description="Name of custom profile object",
        default=""
    )
    
    lace_color: FloatVectorProperty(
        name="Lace Color",
        description="Color for the lace",
        default=(0.8, 0.8, 0.8, 1.0),
        size=4,
        subtype='COLOR',
        min=0.0,
        max=1.0
    )
    
    custom_profile: PointerProperty(
        name="Custom Profile",
        description="Custom curve object to use as profile",
        type=bpy.types.Object
    )
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'CURVE'
    
    def execute(self, context):
        scene = context.scene
        
        # Ensure lace assets are loaded
        if not ensure_lace_assets():
            self.report({'ERROR'}, "Failed to load lace assets")
            return {'CANCELLED'}
        
        # Get active object
        obj = context.active_object
        if not obj or obj.type != 'CURVE':
            self.report({'ERROR'}, "Please select a curve object")
            return {'CANCELLED'}
        
        # Get lace type from scene properties
        lace_type = scene.spp_lace_profile
        
        # Map lace type to node group name
        node_group_map = {
            'ROUND': 'spp_lace_round',
            'OVAL': 'spp_lace_oval',
            'FLAT': 'spp_lace_flat',
            'CUSTOM': 'spp_lace_custom'
        }
        
        node_group_name = node_group_map.get(lace_type)
        if not node_group_name:
            self.report({'ERROR'}, f"Unknown lace type: {lace_type}")
            return {'CANCELLED'}
        
        # Get the node group
        node_group = bpy.data.node_groups.get(node_group_name)
        if not node_group:
            self.report({'ERROR'}, f"Node group '{node_group_name}' not found")
            return {'CANCELLED'}
        
        # Validate custom profile if needed
        if lace_type == 'CUSTOM':
            if not scene.spp_lace_custom_profile:
                self.report({'ERROR'}, "Custom profile object not specified")
                return {'CANCELLED'}
        
        # Remove existing lace modifiers
        modifiers_to_remove = []
        for modifier in obj.modifiers:
            if modifier.type == 'NODES' and modifier.node_group:
                # Check if it's one of our lace modifiers
                if any(lace_name in modifier.node_group.name.lower() for lace_name in ['spp_lace_round', 'spp_lace_oval', 'spp_lace_flat', 'spp_lace_custom']):
                    modifiers_to_remove.append(modifier)
        
        for modifier in modifiers_to_remove:
            obj.modifiers.remove(modifier)
        
        # Add new geometry nodes modifier
        modifier = obj.modifiers.new(name="SPP Lace", type='NODES')
        modifier.node_group = node_group
        
        # Set modifier inputs from scene properties
        try:
            # Basic parameters
            if "Resample" in modifier:
                modifier["Resample"] = scene.spp_lace_resample
            if "Scale" in modifier:
                modifier["Scale"] = scene.spp_lace_scale
            if "Tilt" in modifier:
                modifier["Tilt"] = scene.spp_lace_tilt
            if "Normal Mode" in modifier:
                modifier["Normal Mode"] = int(scene.spp_lace_normal_mode)
            if "Free Normal Control" in modifier:
                modifier["Free Normal Control"] = scene.spp_lace_free_normal
            if "Flip V" in modifier:
                modifier["Flip V"] = scene.spp_lace_flip_v
            if "Flip Normal" in modifier:
                modifier["Flip Normal"] = scene.spp_lace_flip_normal
            if "Shade Smooth" in modifier:
                modifier["Shade Smooth"] = scene.spp_lace_shade_smooth
            if "Lace Color" in modifier:
                modifier["Lace Color"] = scene.spp_lace_color
            
            # Custom profile for CUSTOM type
            if lace_type == 'CUSTOM' and "Custom Profile" in modifier:
                if scene.spp_lace_custom_profile:
                    modifier["Custom Profile"] = scene.spp_lace_custom_profile
            
            # Material assignment
            if "Material" in modifier:
                if scene.spp_lace_use_custom_material and scene.spp_lace_custom_material:
                    modifier["Material"] = scene.spp_lace_custom_material
                else:
                    # Use default material
                    default_material = bpy.data.materials.get("spp_lace_material")
                    if default_material:
                        modifier["Material"] = default_material
                    
        except Exception as e:
            print(f"Error setting modifier inputs: {e}")
        
        self.report({'INFO'}, f"Applied {lace_type.lower()} lace profile")
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        
        col = layout.column()
        col.prop(self, "lace_type")
        
        if self.lace_type == 'CUSTOM':
            col.prop(self, "custom_profile")
        
        col.separator()
        col.prop(self, "resample")
        col.prop(self, "scale")
        col.prop(self, "tilt")
        
        col.separator()
        col.prop(self, "normal_mode")
        if self.normal_mode == '2':
            col.prop(self, "free_normal")
        
        col.separator()
        col.prop(self, "flip_v")
        col.prop(self, "flip_normal")
        col.prop(self, "shade_smooth")
        
        col.separator()
        col.prop(self, "lace_color")
        
        col.separator()
        col.prop(self, "use_default_material")
        if not self.use_default_material:
            col.prop(self, "custom_material")


def register():
    bpy.utils.register_class(SPP_OT_apply_lace)


def unregister():
    bpy.utils.unregister_class(SPP_OT_apply_lace)
