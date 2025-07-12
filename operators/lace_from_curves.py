import bpy, mathutils

# Function to create the LaceFromCurves node group
# Important: This function will be called only when needed by the operator
# We DO NOT call it at module level import time

#initialize lacefromcurves node group
def lacefromcurves_node_group():
    lacefromcurves = bpy.data.node_groups.new(type = 'GeometryNodeTree', name = "LaceFromCurves")

    lacefromcurves.color_tag = 'NONE'
    lacefromcurves.description = ""
    lacefromcurves.default_group_node_width = 140
    

    lacefromcurves.is_modifier = True

    #lacefromcurves interface
    #Socket Geometry
    geometry_socket = lacefromcurves.interface.new_socket(name = "Geometry", in_out='OUTPUT', socket_type = 'NodeSocketGeometry')
    geometry_socket.attribute_domain = 'POINT'

    #Socket Geometry
    geometry_socket_1 = lacefromcurves.interface.new_socket(name = "Geometry", in_out='INPUT', socket_type = 'NodeSocketGeometry')
    geometry_socket_1.attribute_domain = 'POINT'

    #Socket Lace Profile
    lace_profile_socket = lacefromcurves.interface.new_socket(name = "Lace Profile", in_out='INPUT', socket_type = 'NodeSocketInt')
    lace_profile_socket.default_value = 0
    lace_profile_socket.min_value = 0
    lace_profile_socket.max_value = 2
    lace_profile_socket.subtype = 'NONE'
    lace_profile_socket.attribute_domain = 'POINT'
    lace_profile_socket.description = "Lace Profile: 0=Circle, 1=Flat, 2=Custom. Controls the cross-section shape of the lace."

    # Comments explaining enum values and switching logic
    # Normal Mode: 0 = Minimum Twist, 1 = Z Up, 2 = Free
    # Lace Profile: 0 = Circle, 1 = Flat, 2 = Custom
    
    # Normal Mode switching logic:
    # - Normal Mode = 0: Use set_curve_normal_003 (Minimum Twist)
    # - Normal Mode = 1: Use set_curve_normal_005 (Z Up)
    # - Normal Mode = 2: Use set_curve_normal_004 (Free)
    
    # Lace Profile switching logic:
    # - Profile = 0: Use curve_circle (Circle)
    # - Profile = 1: Use quadrilateral_001 (Flat)
    # - Profile = 2: Use object_info (Custom)"

    #Socket Scale
    scale_socket = lacefromcurves.interface.new_socket(name = "Scale", in_out='INPUT', socket_type = 'NodeSocketFloat')
    scale_socket.default_value = 0.004999999888241291
    scale_socket.min_value = 0.0
    scale_socket.max_value = 3.4028234663852886e+38
    scale_socket.subtype = 'DISTANCE'
    scale_socket.attribute_domain = 'POINT'

    #Socket Resample
    resample_socket = lacefromcurves.interface.new_socket(name = "Resample", in_out='INPUT', socket_type = 'NodeSocketInt')
    resample_socket.default_value = 110
    resample_socket.min_value = 1
    resample_socket.max_value = 100000
    resample_socket.subtype = 'NONE'
    resample_socket.attribute_domain = 'POINT'
    resample_socket.description = "Number of points to resample the curve with"

    #Socket Tilt
    tilt_socket = lacefromcurves.interface.new_socket(name = "Tilt", in_out='INPUT', socket_type = 'NodeSocketFloat')
    tilt_socket.default_value = -0.11344639211893082
    tilt_socket.min_value = -3.4028234663852886e+38
    tilt_socket.max_value = 3.4028234663852886e+38
    tilt_socket.subtype = 'ANGLE'
    tilt_socket.attribute_domain = 'POINT'

    #Socket Normal Mode
    normal_mode_socket = lacefromcurves.interface.new_socket(name = "Normal Mode", in_out='INPUT', socket_type = 'NodeSocketInt')
    normal_mode_socket.default_value = 0
    normal_mode_socket.min_value = 0
    normal_mode_socket.max_value = 2
    normal_mode_socket.subtype = 'NONE'
    normal_mode_socket.attribute_domain = 'POINT'
    normal_mode_socket.description = "Normal Mode: 0=Minimum Twist, 1=Z-Up, 2=Free. Controls how curve normals are calculated."


    #Socket Custom Profile
    custom_profile_socket = lacefromcurves.interface.new_socket(name = "Custom Profile", in_out='INPUT', socket_type = 'NodeSocketObject')
    custom_profile_socket.attribute_domain = 'POINT'

    #Socket Shade Smooth
    shade_smooth_socket = lacefromcurves.interface.new_socket(name = "Shade Smooth", in_out='INPUT', socket_type = 'NodeSocketBool')
    shade_smooth_socket.default_value = True
    shade_smooth_socket.attribute_domain = 'POINT'


    #initialize lacefromcurves nodes
    #node Group Input.001
    group_input_001 = lacefromcurves.nodes.new("NodeGroupInput")
    group_input_001.name = "Group Input.001"

    #node Group Output.001
    group_output_001 = lacefromcurves.nodes.new("NodeGroupOutput")
    group_output_001.name = "Group Output.001"
    group_output_001.is_active_output = True

    #node Resample Curve.001
    resample_curve_001 = lacefromcurves.nodes.new("GeometryNodeResampleCurve")
    resample_curve_001.name = "Resample Curve.001"
    resample_curve_001.keep_last_segment = False
    resample_curve_001.mode = 'COUNT'
    #Selection
    resample_curve_001.inputs[1].default_value = True

    #node Curve to Mesh.001
    curve_to_mesh_001 = lacefromcurves.nodes.new("GeometryNodeCurveToMesh")
    curve_to_mesh_001.name = "Curve to Mesh.001"
    #Fill Caps
    curve_to_mesh_001.inputs[2].default_value = False

    #node Quadrilateral.001
    quadrilateral_001 = lacefromcurves.nodes.new("GeometryNodeCurvePrimitiveQuadrilateral")
    quadrilateral_001.name = "Quadrilateral.001"
    quadrilateral_001.mode = 'RECTANGLE'
    #Width
    quadrilateral_001.inputs[0].default_value = 0.0020000000949949026
    #Height
    quadrilateral_001.inputs[1].default_value = 0.0010000000474974513

    #node Set Shade Smooth.001
    set_shade_smooth_001 = lacefromcurves.nodes.new("GeometryNodeSetShadeSmooth")
    set_shade_smooth_001.name = "Set Shade Smooth.001"
    set_shade_smooth_001.domain = 'EDGE'
    #Selection
    set_shade_smooth_001.inputs[1].default_value = True

    #node Set Curve Normal.003
    set_curve_normal_003 = lacefromcurves.nodes.new("GeometryNodeSetCurveNormal")
    set_curve_normal_003.name = "Set Curve Normal.003"
    set_curve_normal_003.mode = 'FREE'
    #Selection
    set_curve_normal_003.inputs[1].default_value = True
    #Normal
    set_curve_normal_003.inputs[2].default_value = (0.0, 0.0, 1.0)

    #node Set Curve Tilt.001
    set_curve_tilt_001 = lacefromcurves.nodes.new("GeometryNodeSetCurveTilt")
    set_curve_tilt_001.name = "Set Curve Tilt.001"
    #Selection
    set_curve_tilt_001.inputs[1].default_value = True

    #node Set Curve Normal.004
    set_curve_normal_004 = lacefromcurves.nodes.new("GeometryNodeSetCurveNormal")
    set_curve_normal_004.name = "Set Curve Normal.004"
    set_curve_normal_004.mode = 'MINIMUM_TWIST'
    #Selection
    set_curve_normal_004.inputs[1].default_value = True

    #node Set Curve Normal.005
    set_curve_normal_005 = lacefromcurves.nodes.new("GeometryNodeSetCurveNormal")
    set_curve_normal_005.name = "Set Curve Normal.005"
    set_curve_normal_005.mode = 'Z_UP'
    #Selection
    set_curve_normal_005.inputs[1].default_value = True

    #node Switch.002
    switch_002 = lacefromcurves.nodes.new("GeometryNodeSwitch")
    switch_002.name = "Switch.002"
    switch_002.input_type = 'GEOMETRY'

    # Create compare nodes for Normal Mode switching
    compare_004 = lacefromcurves.nodes.new("FunctionNodeCompare")
    compare_004.name = "Compare.004"
    compare_004.data_type = 'INT'
    compare_004.operation = 'EQUAL'
    compare_004.inputs[0].default_value = 0.0
    compare_004.inputs[1].default_value = 1.0
    compare_004.inputs[2].default_value = 0.0
    # Compare against value 1 (Z Up)
    compare_004.inputs[3].default_value = 1
    
    compare_005 = lacefromcurves.nodes.new("FunctionNodeCompare")
    compare_005.name = "Compare.005"
    compare_005.data_type = 'INT'
    compare_005.operation = 'EQUAL'
    compare_005.inputs[0].default_value = 0.0
    compare_005.inputs[1].default_value = 1.0
    compare_005.inputs[2].default_value = 0.0
    # Compare against value 2 (Free)
    compare_005.inputs[3].default_value = 2

    #node Switch.003
    switch_003 = lacefromcurves.nodes.new("GeometryNodeSwitch")
    switch_003.name = "Switch.003"
    switch_003.input_type = 'GEOMETRY'

    #node Set Curve Radius
    set_curve_radius = lacefromcurves.nodes.new("GeometryNodeSetCurveRadius")
    set_curve_radius.name = "Set Curve Radius"
    #Selection
    set_curve_radius.inputs[1].default_value = True

    #node Object Info
    object_info = lacefromcurves.nodes.new("GeometryNodeObjectInfo")
    object_info.name = "Object Info"
    object_info.transform_space = 'ORIGINAL'
    #As Instance
    object_info.inputs[1].default_value = False

    #node Curve Circle
    curve_circle = lacefromcurves.nodes.new("GeometryNodeCurvePrimitiveCircle")
    curve_circle.name = "Curve Circle"
    curve_circle.mode = 'RADIUS'
    #Resolution
    curve_circle.inputs[0].default_value = 19
    #Radius
    curve_circle.inputs[4].default_value = 0.0010000000474974513

    # Create compare nodes for Lace Profile switching
    compare_006 = lacefromcurves.nodes.new("FunctionNodeCompare")
    compare_006.name = "Compare.006"
    compare_006.data_type = 'INT'
    compare_006.operation = 'EQUAL'
    compare_006.inputs[0].default_value = 0.0
    compare_006.inputs[1].default_value = 1.0
    compare_006.inputs[2].default_value = 0.0
    # Compare against value 1 (Flat)
    compare_006.inputs[3].default_value = 1
    
    compare_007 = lacefromcurves.nodes.new("FunctionNodeCompare")
    compare_007.name = "Compare.007"
    compare_007.data_type = 'INT'
    compare_007.operation = 'EQUAL'
    compare_007.inputs[0].default_value = 0.0
    compare_007.inputs[1].default_value = 1.0
    compare_007.inputs[2].default_value = 0.0
    # Compare against value 0 (Circle)
    compare_007.inputs[3].default_value = 0

    #node Switch.004
    switch_004 = lacefromcurves.nodes.new("GeometryNodeSwitch")
    switch_004.name = "Switch.004"
    switch_004.input_type = 'GEOMETRY'

    #node Switch.005
    switch_005 = lacefromcurves.nodes.new("GeometryNodeSwitch")
    switch_005.name = "Switch.005"
    switch_005.input_type = 'GEOMETRY'

    #node Reroute
    reroute = lacefromcurves.nodes.new("NodeReroute")
    reroute.name = "Reroute"
    reroute.socket_idname = "NodeSocketInt"
    #node Reroute.001
    reroute_001 = lacefromcurves.nodes.new("NodeReroute")
    reroute_001.name = "Reroute.001"
    reroute_001.socket_idname = "NodeSocketInt"
    #node Reroute.002
    reroute_002 = lacefromcurves.nodes.new("NodeReroute")
    reroute_002.name = "Reroute.002"
    reroute_002.socket_idname = "NodeSocketFloatDistance"
    #node Reroute.003
    reroute_003 = lacefromcurves.nodes.new("NodeReroute")
    reroute_003.name = "Reroute.003"
    reroute_003.socket_idname = "NodeSocketFloatAngle"
    #node Reroute.004
    reroute_004 = lacefromcurves.nodes.new("NodeReroute")
    reroute_004.name = "Reroute.004"
    reroute_004.socket_idname = "NodeSocketInt"
    #node Reroute.005
    reroute_005 = lacefromcurves.nodes.new("NodeReroute")
    reroute_005.name = "Reroute.005"
    reroute_005.socket_idname = "NodeSocketInt"
    #node Reroute.006
    reroute_006 = lacefromcurves.nodes.new("NodeReroute")
    reroute_006.name = "Reroute.006"
    reroute_006.socket_idname = "NodeSocketGeometry"
    #node Reroute.007
    reroute_007 = lacefromcurves.nodes.new("NodeReroute")
    reroute_007.name = "Reroute.007"
    reroute_007.socket_idname = "NodeSocketGeometry"
    #node Reroute.008
    reroute_008 = lacefromcurves.nodes.new("NodeReroute")
    reroute_008.name = "Reroute.008"
    reroute_008.socket_idname = "NodeSocketInt"




    #Set locations
    group_input_001.location = (-888.1896362304688, 1756.08251953125)
    group_output_001.location = (1145.59326171875, 779.2630615234375)
    resample_curve_001.location = (-499.40673828125, 2107.26318359375)
    curve_to_mesh_001.location = (765.59326171875, 779.2630615234375)
    quadrilateral_001.location = (-499.40673828125, 653.2630615234375)
    set_shade_smooth_001.location = (955.59326171875, 779.2630615234375)
    set_curve_normal_003.location = (145.59323120117188, 1444.9296875)
    set_curve_tilt_001.location = (-69.40673828125, 1254.596435546875)
    set_curve_normal_004.location = (348.09326171875, 947.9297485351562)
    set_curve_normal_005.location = (145.59326171875, 1196.9296875)
    switch_002.location = (348.09326171875, 1377.596435546875)
    compare_004.location = (145.59327697753906, 1637.596435546875)
    compare_005.location = (348.09326171875, 1695.596435546875)
    switch_003.location = (563.09326171875, 967.2630615234375)
    set_curve_radius.location = (-296.90673828125, 2039.9296875)
    object_info.location = (-499.40673828125, 905.2630615234375)
    curve_circle.location = (-296.90673828125, 685.2630615234375)
    compare_006.location = (-499.4067687988281, 1859.2630615234375)
    compare_007.location = (-296.90673828125, 2232.596435546875)
    switch_004.location = (-296.90673828125, 873.2630615234375)
    switch_005.location = (-69.40673828125, 779.2630615234375)
    reroute.location = (-499.40673828125, 2232.596435546875)
    reroute_001.location = (-359.40673828125, 2232.596435546875)
    reroute_002.location = (-499.40673828125, 1940.023681640625)
    reroute_003.location = (-499.40673828125, 1154.6260986328125)
    reroute_004.location = (-499.40673828125, 1695.596435546875)
    reroute_005.location = (70.59326171875, 1695.596435546875)
    reroute_006.location = (145.59326171875, 867.0772094726562)
    reroute_007.location = (703.09326171875, 746.0640869140625)
    reroute_008.location = (285.59326171875, 1695.596435546875)

    #Set dimensions
    group_input_001.width, group_input_001.height = 140.0, 100.0
    group_output_001.width, group_output_001.height = 140.0, 100.0
    resample_curve_001.width, resample_curve_001.height = 140.0, 100.0
    curve_to_mesh_001.width, curve_to_mesh_001.height = 140.0, 100.0
    quadrilateral_001.width, quadrilateral_001.height = 140.0, 100.0
    set_shade_smooth_001.width, set_shade_smooth_001.height = 140.0, 100.0
    set_curve_normal_003.width, set_curve_normal_003.height = 140.0, 100.0
    set_curve_tilt_001.width, set_curve_tilt_001.height = 140.0, 100.0
    set_curve_normal_004.width, set_curve_normal_004.height = 140.0, 100.0
    set_curve_normal_005.width, set_curve_normal_005.height = 140.0, 100.0
    switch_002.width, switch_002.height = 140.0, 100.0
    compare_004.width, compare_004.height = 140.0, 100.0
    compare_005.width, compare_005.height = 140.0, 100.0
    switch_003.width, switch_003.height = 140.0, 100.0
    set_curve_radius.width, set_curve_radius.height = 140.0, 100.0
    object_info.width, object_info.height = 140.0, 100.0
    curve_circle.width, curve_circle.height = 140.0, 100.0
    compare_006.width, compare_006.height = 140.0, 100.0
    compare_007.width, compare_007.height = 140.0, 100.0
    switch_004.width, switch_004.height = 140.0, 100.0
    switch_005.width, switch_005.height = 140.0, 100.0
    reroute.width, reroute.height = 14.5, 100.0
    reroute_001.width, reroute_001.height = 14.5, 100.0
    reroute_002.width, reroute_002.height = 14.5, 100.0
    reroute_003.width, reroute_003.height = 14.5, 100.0
    reroute_004.width, reroute_004.height = 14.5, 100.0
    reroute_005.width, reroute_005.height = 14.5, 100.0
    reroute_006.width, reroute_006.height = 14.5, 100.0
    reroute_007.width, reroute_007.height = 14.5, 100.0
    reroute_008.width, reroute_008.height = 14.5, 100.0

    #initialize lacefromcurves links
    #set_shade_smooth_001.Geometry -> group_output_001.Geometry
    lacefromcurves.links.new(set_shade_smooth_001.outputs[0], group_output_001.inputs[0])
    #set_curve_radius.Curve -> set_curve_tilt_001.Curve
    lacefromcurves.links.new(set_curve_radius.outputs[0], set_curve_tilt_001.inputs[0])
    #set_curve_tilt_001.Curve -> set_curve_normal_005.Curve
    lacefromcurves.links.new(set_curve_tilt_001.outputs[0], set_curve_normal_005.inputs[0])
    #set_curve_tilt_001.Curve -> set_curve_normal_003.Curve
    lacefromcurves.links.new(set_curve_tilt_001.outputs[0], set_curve_normal_003.inputs[0])
    #compare_004.Result -> switch_002.Switch
    lacefromcurves.links.new(compare_004.outputs[0], switch_002.inputs[0])
    #group_input_001.Resample  -> resample_curve_001.Count
    lacefromcurves.links.new(group_input_001.outputs[3], resample_curve_001.inputs[2])
    #group_input_001.Geometry -> resample_curve_001.Curve
    lacefromcurves.links.new(group_input_001.outputs[0], resample_curve_001.inputs[0])
    #resample_curve_001.Curve -> set_curve_radius.Curve
    lacefromcurves.links.new(resample_curve_001.outputs[0], set_curve_radius.inputs[0])
    #compare_005.Result -> switch_003.Switch
    lacefromcurves.links.new(compare_005.outputs[0], switch_003.inputs[0])
    #switch_002.Output -> switch_003.False
    lacefromcurves.links.new(switch_002.outputs[0], switch_003.inputs[1])
    #set_curve_normal_003.Curve -> switch_002.False
    lacefromcurves.links.new(set_curve_normal_003.outputs[0], switch_002.inputs[1])
    #set_curve_normal_005.Curve -> switch_002.True
    lacefromcurves.links.new(set_curve_normal_005.outputs[0], switch_002.inputs[2])
    #set_curve_normal_004.Curve -> switch_003.True
    lacefromcurves.links.new(set_curve_normal_004.outputs[0], switch_003.inputs[2])
    #switch_003.Output -> curve_to_mesh_001.Curve
    lacefromcurves.links.new(switch_003.outputs[0], curve_to_mesh_001.inputs[0])
    #group_input_001.Custom Profile -> object_info.Object
    lacefromcurves.links.new(group_input_001.outputs[6], object_info.inputs[0])
    #curve_to_mesh_001.Mesh -> set_shade_smooth_001.Geometry
    lacefromcurves.links.new(curve_to_mesh_001.outputs[0], set_shade_smooth_001.inputs[0])
    
    # Connect Shade Smooth input to the set_shade_smooth node
    lacefromcurves.links.new(group_input_001.outputs[7], set_shade_smooth_001.inputs[2])
    #switch_004.Output -> switch_005.False
    lacefromcurves.links.new(switch_004.outputs[0], switch_005.inputs[1])
    #compare_007.Result -> switch_005.Switch
    lacefromcurves.links.new(compare_007.outputs[0], switch_005.inputs[0])
    #curve_circle.Curve -> switch_005.True
    lacefromcurves.links.new(curve_circle.outputs[0], switch_005.inputs[2])
    #group_input_001.Scale -> compare_006.B
    lacefromcurves.links.new(group_input_001.outputs[2], compare_006.inputs[3])
    #compare_006.Result -> switch_004.Switch
    lacefromcurves.links.new(compare_006.outputs[0], switch_004.inputs[0])
    #object_info.Geometry -> switch_004.False
    lacefromcurves.links.new(object_info.outputs[4], switch_004.inputs[1])
    #quadrilateral_001.Curve -> switch_004.True
    lacefromcurves.links.new(quadrilateral_001.outputs[0], switch_004.inputs[2])
    #group_input_001.Lace Profile -> reroute.Input
    lacefromcurves.links.new(group_input_001.outputs[1], reroute.inputs[0])
    #reroute.Output -> reroute_001.Input
    lacefromcurves.links.new(reroute.outputs[0], reroute_001.inputs[0])
    #group_input_001.Lace Profile -> compare_007.B (Lace Profile = 0 check)
    lacefromcurves.links.new(group_input_001.outputs[1], compare_007.inputs[3])
    #group_input_001.Lace Profile -> compare_006.B (Lace Profile = 1 check)
    lacefromcurves.links.new(group_input_001.outputs[1], compare_006.inputs[3])
    #group_input_001.Scale -> reroute_002.Input
    lacefromcurves.links.new(group_input_001.outputs[2], reroute_002.inputs[0])
    #reroute_002.Output -> set_curve_radius.Radius
    lacefromcurves.links.new(reroute_002.outputs[0], set_curve_radius.inputs[2])
    #group_input_001.Tilt -> reroute_003.Input
    lacefromcurves.links.new(group_input_001.outputs[4], reroute_003.inputs[0])
    #reroute_003.Output -> set_curve_tilt_001.Tilt
    lacefromcurves.links.new(reroute_003.outputs[0], set_curve_tilt_001.inputs[2])
    #group_input_001.Normal Mode -> reroute_004.Input
    lacefromcurves.links.new(group_input_001.outputs[5], reroute_004.inputs[0])
    #reroute_004.Output -> reroute_005.Input
    lacefromcurves.links.new(reroute_004.outputs[0], reroute_005.inputs[0])
    #group_input_001.Normal Mode -> compare_004.B (Normal Mode = 1 check)
    lacefromcurves.links.new(group_input_001.outputs[5], compare_004.inputs[3])
    #group_input_001.Normal Mode -> compare_005.B (Normal Mode = 2 check)
    lacefromcurves.links.new(group_input_001.outputs[5], compare_005.inputs[3])
    #set_curve_tilt_001.Curve -> reroute_006.Input
    lacefromcurves.links.new(set_curve_tilt_001.outputs[0], reroute_006.inputs[0])
    #reroute_006.Output -> set_curve_normal_004.Curve
    lacefromcurves.links.new(reroute_006.outputs[0], set_curve_normal_004.inputs[0])
    #switch_005.Output -> reroute_007.Input
    lacefromcurves.links.new(switch_005.outputs[0], reroute_007.inputs[0])
    #reroute_007.Output -> curve_to_mesh_001.Profile Curve
    lacefromcurves.links.new(reroute_007.outputs[0], curve_to_mesh_001.inputs[1])
    
    # Return the node group
    return lacefromcurves


class OBJECT_OT_add_lace_modifier(bpy.types.Operator):
    """Add or update a LaceFromCurves modifier to the selected curve object"""
    bl_idname = "object.add_lace_modifier"
    bl_label = "Apply Lace Geometry"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        # Only allow this operator on curve objects
        return context.active_object and context.active_object.type == 'CURVE'
    
    def set_modifier_inputs(self, modifier, context):
        """Set modifier inputs from scene properties"""
        scene = context.scene
        
        # Direct mapping by socket index (more reliable than name mapping)
        # Socket 0: Geometry (auto-handled by Blender)
        # Socket 1: Lace Profile (int)
        # Socket 2: Scale (float)
        # Socket 3: Resample (int)
        # Socket 4: Tilt (float)
        # Socket 5: Normal Mode (int)
        # Socket 6: Custom Profile (object)
        # Socket 7: Shade Smooth (bool)
        
        try:
            if hasattr(scene, 'spp_lace_profile'):
                modifier["Input_1"] = int(scene.spp_lace_profile)
            if hasattr(scene, 'spp_lace_scale'):
                modifier["Input_2"] = scene.spp_lace_scale
            if hasattr(scene, 'spp_lace_resample'):
                modifier["Input_3"] = scene.spp_lace_resample
            if hasattr(scene, 'spp_lace_tilt'):
                modifier["Input_4"] = scene.spp_lace_tilt
            if hasattr(scene, 'spp_lace_normal_mode'):
                modifier["Input_5"] = int(scene.spp_lace_normal_mode)
            if hasattr(scene, 'spp_lace_custom_profile'):
                modifier["Input_6"] = scene.spp_lace_custom_profile
            if hasattr(scene, 'spp_lace_shade_smooth'):
                modifier["Input_7"] = scene.spp_lace_shade_smooth
        except Exception as e:
            self.report({'WARNING'}, f"Error setting modifier inputs: {str(e)}")
    
    def execute(self, context):
        # Get the active object
        obj = context.active_object
        
        # Check if the LaceFromCurves node group exists, if not create it
        node_group = bpy.data.node_groups.get("LaceFromCurves")
        if not node_group:
            node_group = lacefromcurves_node_group()
        
        # Check if the object already has a Lace modifier
        modifier = None
        for mod in obj.modifiers:
            if mod.type == 'NODES' and mod.name.startswith("Lace"):
                modifier = mod
                # Update the node group in case it changed
                if mod.node_group != node_group:
                    mod.node_group = node_group
                break
        
        # If no modifier exists, create a new one
        if not modifier:
            modifier = obj.modifiers.new(name="Lace", type='NODES')
            modifier.node_group = node_group
        
        # Set modifier inputs from scene properties
        self.set_modifier_inputs(modifier, context)
        
        self.report({'INFO'}, f"{'Updated' if modifier else 'Added'} Lace modifier on {obj.name}")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(OBJECT_OT_add_lace_modifier)
    
    # Register the properties
    bpy.types.Scene.spp_lace_profile = bpy.props.EnumProperty(
        name="Lace Profile",
        description="Shape profile to use for the lace",
        items=[
            ('0', "Circle", "Circular lace profile"),
            ('1', "Flat", "Flat rectangular lace profile"),
            ('2', "Custom", "Custom profile from another object")
        ],
        default='0'
    )
    
    bpy.types.Scene.spp_lace_scale = bpy.props.FloatProperty(
        name="Scale",
        description="Size of the lace profile",
        default=0.005,
        min=0.0001,
        max=0.1,
        precision=4,
        subtype='DISTANCE'
    )
    
    bpy.types.Scene.spp_lace_resample = bpy.props.IntProperty(
        name="Resample",
        description="Number of points to resample the curve with",
        default=110,
        min=1,
        max=1000
    )
    
    bpy.types.Scene.spp_lace_tilt = bpy.props.FloatProperty(
        name="Tilt",
        description="Rotation around the curve tangent",
        default=-0.11344639211893082,
        subtype='ANGLE'
    )
    
    bpy.types.Scene.spp_lace_normal_mode = bpy.props.EnumProperty(
        name="Normal Mode",
        description="Method to calculate normals along the curve",
        items=[
            ('0', "Minimum Twist", "Use minimum twist for curve normals"),
            ('1', "Z Up", "Align normals with Z-up direction"),
            ('2', "Free", "Free normal direction")
        ],
        default='0'
    )
    
    bpy.types.Scene.spp_lace_custom_profile = bpy.props.PointerProperty(
        name="Custom Profile",
        description="Object to use as custom profile (only used when Lace Profile is set to Custom)",
        type=bpy.types.Object
    )
    
    bpy.types.Scene.spp_lace_shade_smooth = bpy.props.BoolProperty(
        name="Shade Smooth",
        description="Apply smooth shading to the generated mesh",
        default=True
    )
    
    bpy.types.Scene.spp_show_lace_options = bpy.props.BoolProperty(
        name="Show Lace Options",
        description="Show or hide lace generation options",
        default=False
    )

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_add_lace_modifier)
    
    # Unregister properties
    if hasattr(bpy.types.Scene, "spp_lace_profile"):
        del bpy.types.Scene.spp_lace_profile
    if hasattr(bpy.types.Scene, "spp_lace_scale"):
        del bpy.types.Scene.spp_lace_scale
    if hasattr(bpy.types.Scene, "spp_lace_resample"):
        del bpy.types.Scene.spp_lace_resample
    if hasattr(bpy.types.Scene, "spp_lace_tilt"):
        del bpy.types.Scene.spp_lace_tilt
    if hasattr(bpy.types.Scene, "spp_lace_normal_mode"):
        del bpy.types.Scene.spp_lace_normal_mode
    if hasattr(bpy.types.Scene, "spp_lace_custom_profile"):
        del bpy.types.Scene.spp_lace_custom_profile
    if hasattr(bpy.types.Scene, "spp_lace_shade_smooth"):
        del bpy.types.Scene.spp_lace_shade_smooth
    if hasattr(bpy.types.Scene, "spp_show_lace_options"):
        del bpy.types.Scene.spp_show_lace_options

# The lacefromcurves_node_group function will be called only when needed by the operator

