"""
Shoelace Generator for SneakerPanel Pro addon.

This module provides operators for generating 3D shoelaces from bezier curves
with customizable profiles and materials.
"""

import bpy
import math
from bpy.props import (
    EnumProperty,
    FloatProperty,
    StringProperty,
    BoolProperty,
    FloatVectorProperty,
    PointerProperty
)


class SPP_OT_CreateShoelaceGeoNodes(bpy.types.Operator):
    """Create a new shoelace object from a bezier curve using geometry nodes"""
    bl_idname = "spp.create_shoelace_geonodes"
    bl_label = "Create Shoelace (Geo Nodes)"
    bl_description = "Generate a shoelace by extruding a profile along a curve path"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Input properties
    curve_object: StringProperty(
        name="Curve Object",
        description="Bezier curve to use as the shoelace path",
        default=""
    )
    
    profile_type: EnumProperty(
        name="Profile Type",
        description="Type of profile to use for the shoelace",
        items=[
            ('CIRCLE', "Circle", "Circular profile"),
            ('OVAL', "Oval", "Oval (elliptical) profile"),
            ('FLAT', "Flat", "Flattened profile with rounded edges"),
            ('CUSTOM', "Custom", "Use custom curve as profile")
        ],
        default='CIRCLE'
    )
    
    profile_curve: StringProperty(
        name="Profile Curve",
        description="Custom curve to use as shoelace profile (only used with Custom profile type)",
        default=""
    )
    
    orientation_type: EnumProperty(
        name="Orientation",
        description="How to orient the profile along the curve",
        items=[
            ('NORMAL', "Normal", "Orient profile to curve normal"),
            ('Z_UP', "Z Up", "Keep profile Z axis pointing up"),
            ('TANGENT', "Tangent", "Orient profile along curve tangent")
        ],
        default='NORMAL'
    )
    
    radius: FloatProperty(
        name="Radius",
        description="Radius of the shoelace profile",
        default=0.05,
        min=0.001,
        soft_max=1.0,
        unit='LENGTH'
    )
    
    width: FloatProperty(
        name="Width",
        description="Width for oval and flat profiles",
        default=0.07,
        min=0.001,
        soft_max=1.0,
        unit='LENGTH'
    )
    
    height: FloatProperty(
        name="Height",
        description="Height for oval and flat profiles",
        default=0.04,
        min=0.001,
        soft_max=1.0,
        unit='LENGTH'
    )
    
    corner_radius: FloatProperty(
        name="Corner Radius",
        description="Radius of corners for flat profile",
        default=0.01,
        min=0.0,
        soft_max=0.5,
        unit='LENGTH'
    )
    
    resolution: FloatProperty(
        name="Resolution",
        description="Resolution of the profile curve",
        default=16,
        min=3,
        max=64,
        step=1
    )
    
    twist: FloatProperty(
        name="Twist",
        description="Additional twist along the curve",
        default=0.0,
        min=-360.0,
        max=360.0,
        step=5,
        subtype='ANGLE',
        unit='ROTATION'
    )
    
    material_name: StringProperty(
        name="Material",
        description="Material to apply to the shoelace",
        default="Shoelace_Material"
    )
    
    color: FloatVectorProperty(
        name="Color",
        description="Color for the generated material",
        subtype='COLOR',
        default=(0.8, 0.8, 0.8, 1.0),
        size=4,
        min=0.0,
        max=1.0
    )
    
    auto_assign_material: BoolProperty(
        name="Auto-assign Material",
        description="Automatically create and assign material if it doesn't exist",
        default=True
    )
    
    uv_scale_u: FloatProperty(
        name="UV Scale U",
        description="Scale of the U coordinate in UV mapping",
        default=1.0,
        min=0.01,
        soft_max=10.0
    )
    
    uv_scale_v: FloatProperty(
        name="UV Scale V",
        description="Scale of the V coordinate in UV mapping",
        default=1.0,
        min=0.01,
        soft_max=10.0
    )

    def create_geometry_nodes_setup(self, context, curve_obj, name_prefix="Shoelace"):
        """Create the geometry nodes setup for the shoelace"""
        # Create a new curve object to hold the geometry nodes modifier
        mesh = bpy.data.meshes.new(name_prefix + "_Mesh")
        shoelace_obj = bpy.data.objects.new(name_prefix, mesh)
        context.collection.objects.link(shoelace_obj)
        
        # Add the Geometry Nodes modifier
        gn_mod = shoelace_obj.modifiers.new(name="ShoelaceGeometry", type='NODES')
        
        # Create a new node group or use existing one
        node_group_name = "ShoelaceGenerator"
        if node_group_name in bpy.data.node_groups:
            gn_mod.node_group = bpy.data.node_groups[node_group_name]
        else:
            node_group = bpy.data.node_groups.new(name=node_group_name, type='GeometryNodeTree')
            gn_mod.node_group = node_group
            
            # Set up the node group with inputs and outputs
            # First clear any existing sockets
            node_group.inputs.clear()
            node_group.outputs.clear()
            
            # Define basic group inputs
            group_in = node_group.nodes.new('NodeGroupInput')
            group_in.location = (-800, 0)
            
            # Define basic group outputs
            group_out = node_group.nodes.new('NodeGroupOutput')
            group_out.location = (800, 0)
            
            # Create input sockets for the node group
            node_group.inputs.new('NodeSocketGeometry', "Curve")
            node_group.inputs.new('NodeSocketEnum', "Profile Type").default_value = self.profile_type
            node_group.inputs.new('NodeSocketFloat', "Radius").default_value = self.radius
            node_group.inputs.new('NodeSocketFloat', "Width").default_value = self.width
            node_group.inputs.new('NodeSocketFloat', "Height").default_value = self.height
            node_group.inputs.new('NodeSocketFloat', "Corner Radius").default_value = self.corner_radius
            node_group.inputs.new('NodeSocketFloat', "Resolution").default_value = self.resolution
            node_group.inputs.new('NodeSocketFloat', "Twist").default_value = self.twist
            node_group.inputs.new('NodeSocketEnum', "Orientation").default_value = self.orientation_type
            node_group.inputs.new('NodeSocketGeometry', "Profile Curve")
            node_group.inputs.new('NodeSocketFloat', "UV Scale U").default_value = self.uv_scale_u
            node_group.inputs.new('NodeSocketFloat', "UV Scale V").default_value = self.uv_scale_v
            
            # Create output socket
            node_group.outputs.new('NodeSocketGeometry', "Geometry")
            
            # Curve input node
            curve_to_points = node_group.nodes.new('GeometryNodeCurveToPoints')
            curve_to_points.location = (-600, 100)
            
            # Profile nodes for different profile types
            profile_switch = node_group.nodes.new('GeometryNodeSwitch')
            profile_switch.location = (-200, 0)
            
            # Circle profile
            circle_profile = node_group.nodes.new('GeometryNodeCurvePrimitiveCircle')
            circle_profile.location = (-400, 200)
            
            # Oval profile (using ellipse)
            oval_profile = node_group.nodes.new('GeometryNodeCurveQuadraticBezier')
            oval_profile.location = (-400, 0)
            
            # Flat profile (rounded rectangle)
            flat_profile = node_group.nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
            flat_profile.location = (-400, -200)
            
            # Custom profile input
            custom_profile = node_group.nodes.new('GeometryNodeInputCurve')
            custom_profile.location = (-400, -400)
            
            # Profile to points
            profile_to_points = node_group.nodes.new('GeometryNodeCurveToPoints')
            profile_to_points.location = (0, 0)
            
            # Curve to mesh node
            curve_to_mesh = node_group.nodes.new('GeometryNodeCurveToMesh')
            curve_to_mesh.location = (200, 0)
            
            # UV generation node
            uv_node = node_group.nodes.new('GeometryNodeUVUnwrap')
            uv_node.location = (400, 0)
            
            # Set up node connections
            node_group.links.new(group_in.outputs["Curve"], curve_to_points.inputs["Curve"])
            
            # Connect outputs to the curve_to_mesh node
            node_group.links.new(profile_switch.outputs["Output"], profile_to_points.inputs["Curve"])
            node_group.links.new(profile_to_points.outputs["Points"], curve_to_mesh.inputs["Profile"])
            node_group.links.new(curve_to_points.outputs["Curve"], curve_to_mesh.inputs["Curve"])
            
            # Connect the UV node
            node_group.links.new(curve_to_mesh.outputs["Mesh"], uv_node.inputs["Mesh"])
            node_group.links.new(uv_node.outputs["UV"], group_out.inputs["Geometry"])

        # Connect the input curve to the geometry nodes modifier
        gn_mod["Input_2"] = curve_obj
        
        # Link orientation type
        gn_mod["Input_10"] = self.orientation_type
        
        # Connect other parameters
        gn_mod["Input_3"] = self.radius
        gn_mod["Input_4"] = self.width
        gn_mod["Input_5"] = self.height
        gn_mod["Input_6"] = self.corner_radius
        gn_mod["Input_7"] = self.resolution
        gn_mod["Input_8"] = self.twist
        gn_mod["Input_12"] = self.uv_scale_u
        gn_mod["Input_13"] = self.uv_scale_v

        # Set profile type
        gn_mod["Input_1"] = self.profile_type
        
        # Link profile curve if custom profile is used
        if self.profile_type == 'CUSTOM' and self.profile_curve in bpy.data.objects:
            profile_obj = bpy.data.objects[self.profile_curve]
            gn_mod["Input_11"] = profile_obj

        # Handle material
        if self.auto_assign_material:
            if self.material_name not in bpy.data.materials:
                mat = bpy.data.materials.new(name=self.material_name)
                mat.use_nodes = True
                
                # Set material color
                if mat.node_tree:
                    bsdf = mat.node_tree.nodes.get('Principled BSDF')
                    if bsdf:
                        bsdf.inputs['Base Color'].default_value = self.color
            else:
                mat = bpy.data.materials[self.material_name]
                
            # Assign material to shoelace object
            if len(shoelace_obj.data.materials) == 0:
                shoelace_obj.data.materials.append(mat)
            else:
                shoelace_obj.data.materials[0] = mat

        return shoelace_obj

    def execute(self, context):
        # Check if curve object exists
        if self.curve_object and self.curve_object in bpy.data.objects:
            curve_obj = bpy.data.objects[self.curve_object]
            
            # Verify it's a curve
            if curve_obj.type != 'CURVE':
                self.report({'ERROR'}, f"Selected object '{self.curve_object}' is not a curve")
                return {'CANCELLED'}
                
            # Custom profile validation
            if self.profile_type == 'CUSTOM':
                if not self.profile_curve:
                    self.report({'ERROR'}, "Custom profile selected but no profile curve specified")
                    return {'CANCELLED'}
                if self.profile_curve not in bpy.data.objects:
                    self.report({'ERROR'}, f"Profile curve '{self.profile_curve}' not found")
                    return {'CANCELLED'}
                if bpy.data.objects[self.profile_curve].type != 'CURVE':
                    self.report({'ERROR'}, f"Profile object '{self.profile_curve}' is not a curve")
                    return {'CANCELLED'}
            
            # Create geometry nodes setup
            shoelace_obj = self.create_geometry_nodes_setup(context, curve_obj)
            
            # Select the new object
            for obj in context.selected_objects:
                obj.select_set(False)
            shoelace_obj.select_set(True)
            context.view_layer.objects.active = shoelace_obj
            
            self.report({'INFO'}, f"Shoelace generated from curve '{self.curve_object}'")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No valid curve object selected")
            return {'CANCELLED'}

    def invoke(self, context, event):
        # Get the active object if it's a curve
        if context.active_object and context.active_object.type == 'CURVE':
            self.curve_object = context.active_object.name
        
        # Open property panel
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)
        
    def draw(self, context):
        layout = self.layout
        
        # Curve object selection
        layout.prop_search(self, "curve_object", bpy.data, "objects", text="Curve Path")
        
        # Profile section
        box = layout.box()
        box.label(text="Profile Settings", icon='CURVE_NCIRCLE')
        box.prop(self, "profile_type", text="Profile")
        
        # Show appropriate profile settings based on type
        if self.profile_type == 'CIRCLE':
            box.prop(self, "radius")
        elif self.profile_type == 'OVAL':
            box.prop(self, "width")
            box.prop(self, "height")
        elif self.profile_type == 'FLAT':
            box.prop(self, "width")
            box.prop(self, "height")
            box.prop(self, "corner_radius")
        elif self.profile_type == 'CUSTOM':
            box.prop_search(self, "profile_curve", bpy.data, "objects", text="Profile Curve")
        
        # Common profile settings
        box.prop(self, "resolution")
        
        # Orientation settings
        box = layout.box()
        box.label(text="Orientation Settings", icon='ORIENTATION_LOCAL')
        box.prop(self, "orientation_type")
        box.prop(self, "twist")
        
        # Material settings
        box = layout.box()
        box.label(text="Material Settings", icon='MATERIAL')
        box.prop(self, "auto_assign_material")
        if self.auto_assign_material:
            box.prop(self, "material_name")
            box.prop(self, "color")
            
        # UV settings
        box = layout.box()
        box.label(text="UV Settings", icon='UV')
        row = box.row()
        row.prop(self, "uv_scale_u", text="U Scale")
        row.prop(self, "uv_scale_v", text="V Scale")


class SPP_OT_UpdateShoelaceMaterial(bpy.types.Operator):
    """Update the material of a shoelace object"""
    bl_idname = "spp.update_shoelace_material"
    bl_label = "Update Shoelace Material"
    bl_description = "Update the material of a selected shoelace object"
    bl_options = {'REGISTER', 'UNDO'}
    
    material_name: StringProperty(
        name="Material",
        description="Material to apply to the shoelace",
        default="Shoelace_Material"
    )
    
    color: FloatVectorProperty(
        name="Color",
        description="Color for the generated material",
        subtype='COLOR',
        default=(0.8, 0.8, 0.8, 1.0),
        size=4,
        min=0.0,
        max=1.0
    )
    
    def execute(self, context):
        if context.active_object and context.active_object.type == 'MESH':
            obj = context.active_object
            
            # Check if material exists, create if not
            if self.material_name not in bpy.data.materials:
                mat = bpy.data.materials.new(name=self.material_name)
                mat.use_nodes = True
                
                # Set material color
                if mat.node_tree:
                    bsdf = mat.node_tree.nodes.get('Principled BSDF')
                    if bsdf:
                        bsdf.inputs['Base Color'].default_value = self.color
            else:
                mat = bpy.data.materials[self.material_name]
                # Update existing material color
                if mat.node_tree:
                    bsdf = mat.node_tree.nodes.get('Principled BSDF')
                    if bsdf:
                        bsdf.inputs['Base Color'].default_value = self.color
                
            # Assign material to object
            if len(obj.data.materials) == 0:
                obj.data.materials.append(mat)
            else:
                obj.data.materials[0] = mat
                
            self.report({'INFO'}, f"Material '{self.material_name}' applied")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No valid mesh object selected")
            return {'CANCELLED'}
            
    def invoke(self, context, event):
        # If object has a material, get its current settings
        if context.active_object and context.active_object.type == 'MESH':
            obj = context.active_object
            if len(obj.data.materials) > 0 and obj.data.materials[0]:
                self.material_name = obj.data.materials[0].name
                mat = obj.data.materials[0]
                if mat.node_tree:
                    bsdf = mat.node_tree.nodes.get('Principled BSDF')
                    if bsdf:
                        self.color = bsdf.inputs['Base Color'].default_value
        
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
        
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "material_name")
        layout.prop(self, "color")


# Collection of all operators
classes = (
    SPP_OT_CreateShoelaceGeoNodes,
    SPP_OT_UpdateShoelaceMaterial,
)

def register():
    """Register the operators."""
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    """Unregister the operators."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
