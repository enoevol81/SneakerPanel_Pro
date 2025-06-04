import bpy
from bpy.props import BoolProperty, IntProperty
from mathutils import Vector

# --- Helper Functions ---
def subdivide_cubic_bezier(p1, p2, p3, p4, t):
    """Subdivides a cubic Bezier curve at parameter t."""
    # Calculate intermediate points for De Casteljau's algorithm
    p12 = (p2 - p1) * t + p1
    p23 = (p3 - p2) * t + p2
    p34 = (p4 - p3) * t + p3
    p123 = (p23 - p12) * t + p12
    p234 = (p34 - p23) * t + p23
    p1234 = (p234 - p123) * t + p123
    # Return the points that define the two new Bezier segments
    return [p12, p123, p1234, p234, p34]

# --- Utility Functions ---
def get_selected_curves():
    """Returns a list of selected curve objects."""
    rv_list = []
    for obj in bpy.context.selected_objects:
        try:
            if obj.type == "CURVE":
                rv_list.append(obj)
        except:
            # Handle potential errors if object properties are not accessible
            pass
    return rv_list

def selected_1_or_more_curves():
    """Checks if at least one curve object is selected and active."""
    try:
        if len(get_selected_curves()) > 0:
            # Ensure the active object is also a curve
            return (bpy.context.active_object.type == "CURVE")
    except:
        # Handle potential errors
        pass
    return False

# --- Core Surface Conversion Function ---
def surface_from_bezier(surfacedata, points, center):
    """
    Converts a single Bezier spline's points to a set of NURBS splines
    that form a surface patch.

    Args:
        surfacedata: The curve data object for the new surface.
        points: The collection of bpy.types.BezierSplinePoint from the input Bezier spline.
        center: Boolean, whether to create central guiding splines.
    """
    len_points = len(points) - 1 # Number of segments if cyclic, or points-1 if not

    # If the original Bezier spline has an even number of control points (implying an odd number of segments
    # for an open curve, or if it's just an even number for a cyclic one that needs adjustment for this algorithm),
    # subdivide the segment connecting the last and first points to make the effective number of points odd.
    # This algorithm seems to work by pairing points from opposite sides, so an odd number of points
    # (and thus an even number of segments for the purpose of pairing) is expected.
    if len_points % 2 == 0:
        # Subdivide the "closing" segment (last to first)
        # The h array contains:
        # h[0]: new handle for points[len_points] (right handle)
        # h[1]: new handle for the new point (left handle)
        # h[2]: coordinate of the new point
        # h[3]: new handle for the new point (right handle)
        # h[4]: new handle for points[0] (left handle)
        h = subdivide_cubic_bezier(
            points[len_points].co, points[len_points].handle_right,
            points[0].handle_left, points[0].co, 0.5 # Subdivide at the midpoint
        )
        points.add(1) # Add a new BezierSplinePoint
        len_points = len(points) - 1 # Update count

        # Adjust handles and coordinate for the newly created point and its neighbors
        points[len_points - 1].handle_right = h[0] # Old last point's right handle
        points[len_points].handle_left = h[1]      # New point's left handle
        points[len_points].co = h[2]               # New point's coordinate
        points[len_points].handle_right = h[3]     # New point's right handle
        points[0].handle_left = h[4]               # Original first point's left handle
    
    # 'half' determines how many pairs of construction splines will be created from the sides
    half = round((len_points + 1)/2) - 1
    
    # --- Create Vertical NURBS Splines ---
    # These splines run along the "height" or "profile" of the original Bezier curve shape.

    # Spline 1: Connects the first Bezier point, its left handle, the last point's right handle, and the last point.
    # This forms the "outer edge" on one side.
    surfacespline1 = surfacedata.splines.new(type='NURBS')
    surfacespline1.points.add(3) # NURBS splines need 4 points for a cubic segment
    surfacespline1.points[0].co = [points[0].co.x, points[0].co.y, points[0].co.z, 1]
    surfacespline1.points[1].co = [points[0].handle_left.x, points[0].handle_left.y, points[0].handle_left.z, 1]
    surfacespline1.points[2].co = [points[len_points].handle_right.x, points[len_points].handle_right.y, points[len_points].handle_right.z, 1]
    surfacespline1.points[3].co = [points[len_points].co.x, points[len_points].co.y, points[len_points].co.z, 1]
    for p_nurbs in surfacespline1.points: # Select points for 'make_segment' later
        p_nurbs.select = True
    surfacespline1.use_endpoint_u = True # Makes the spline touch its endpoints
    surfacespline1.use_endpoint_v = True

    # Loop to create pairs of splines moving inwards from the edges
    for i in range(0, half):
        if center:
            # Spline 2 (Optional): Connects Bezier point 'i', a midpoint, another midpoint, and point 'len_points - i'.
            # This creates a central rib if 'center' is True.
            surfacespline2 = surfacedata.splines.new(type='NURBS')
            surfacespline2.points.add(3)
            surfacespline2.points[0].co = [points[i].co.x, points[i].co.y, points[i].co.z, 1]
            surfacespline2.points[1].co = [(points[i].co.x + points[len_points - i].co.x)/2,
                                          (points[i].co.y + points[len_points - i].co.y)/2,
                                          (points[i].co.z + points[len_points - i].co.z)/2, 1]
            surfacespline2.points[2].co = [(points[len_points - i].co.x + points[i].co.x)/2,
                                          (points[len_points - i].co.y + points[i].co.y)/2,
                                          (points[len_points - i].co.z + points[i].co.z)/2, 1]
            surfacespline2.points[3].co = [points[len_points - i].co.x, points[len_points - i].co.y, points[len_points - i].co.z, 1]
            for p_nurbs in surfacespline2.points:
                p_nurbs.select = True
            surfacespline2.use_endpoint_u = True
            surfacespline2.use_endpoint_v = True
        
        # Spline 3: Connects the right handle of point 'i', a midpoint between handles,
        # another midpoint, and the left handle of point 'len_points - i'.
        # This uses the Bezier handles to guide the surface shape.
        surfacespline3 = surfacedata.splines.new(type='NURBS')
        surfacespline3.points.add(3)
        surfacespline3.points[0].co = [points[i].handle_right.x, points[i].handle_right.y, points[i].handle_right.z, 1]
        surfacespline3.points[1].co = [(points[i].handle_right.x + points[len_points - i].handle_left.x)/2,
                                      (points[i].handle_right.y + points[len_points - i].handle_left.y)/2,
                                      (points[i].handle_right.z + points[len_points - i].handle_left.z)/2, 1]
        surfacespline3.points[2].co = [(points[len_points - i].handle_left.x + points[i].handle_right.x)/2,
                                      (points[len_points - i].handle_left.y + points[i].handle_right.y)/2,
                                      (points[len_points - i].handle_left.z + points[i].handle_right.z)/2, 1]
        surfacespline3.points[3].co = [points[len_points - i].handle_left.x, points[len_points - i].handle_left.y, points[len_points - i].handle_left.z, 1]
        for p_nurbs in surfacespline3.points:
            p_nurbs.select = True
        surfacespline3.use_endpoint_u = True
        surfacespline3.use_endpoint_v = True
        
        # Spline 4: Similar to Spline 3 but for the next set of points inward (i+1).
        # Connects left handle of point 'i+1' and right handle of point 'len_points - i - 1'.
        # Ensure indices are valid before creating.
        if i + 1 <= half and len_points - i - 1 >= half + 1:
            surfacespline4 = surfacedata.splines.new(type='NURBS')
            surfacespline4.points.add(3)
            surfacespline4.points[0].co = [points[i + 1].handle_left.x, points[i + 1].handle_left.y, points[i + 1].handle_left.z, 1]
            surfacespline4.points[1].co = [(points[i + 1].handle_left.x + points[len_points - i - 1].handle_right.x)/2,
                                          (points[i + 1].handle_left.y + points[len_points - i - 1].handle_right.y)/2,
                                          (points[i + 1].handle_left.z + points[len_points - i - 1].handle_right.z)/2, 1]
            surfacespline4.points[2].co = [(points[len_points - i - 1].handle_right.x + points[i + 1].handle_left.x)/2,
                                          (points[len_points - i - 1].handle_right.y + points[i + 1].handle_left.y)/2,
                                          (points[len_points - i - 1].handle_right.z + points[i + 1].handle_left.z)/2, 1]
            surfacespline4.points[3].co = [points[len_points - i - 1].handle_right.x, points[len_points - i - 1].handle_right.y, points[len_points - i - 1].handle_right.z, 1]
            for p_nurbs in surfacespline4.points:
                p_nurbs.select = True
            surfacespline4.use_endpoint_u = True
            surfacespline4.use_endpoint_v = True
        
        if center:
            # Spline 5 (Optional): Similar to Spline 2 but for point 'i+1' and 'len_points - i - 1'.
            # Another central rib if 'center' is True.
            if i + 1 <= half and len_points - i - 1 >= half + 1: 
                surfacespline5 = surfacedata.splines.new(type='NURBS')
                surfacespline5.points.add(3)
                surfacespline5.points[0].co = [points[i + 1].co.x, points[i + 1].co.y, points[i + 1].co.z, 1]
                surfacespline5.points[1].co = [(points[i + 1].co.x + points[len_points - i - 1].co.x)/2,
                                              (points[i + 1].co.y + points[len_points - i - 1].co.y)/2,
                                              (points[i + 1].co.z + points[len_points - i - 1].co.z)/2, 1]
                surfacespline5.points[2].co = [(points[len_points - i - 1].co.x + points[i + 1].co.x)/2,
                                              (points[len_points - i - 1].co.y + points[i + 1].co.y)/2,
                                              (points[len_points - i - 1].co.z + points[i + 1].co.z)/2, 1]
                surfacespline5.points[3].co = [points[len_points - i - 1].co.x, points[len_points - i - 1].co.y, points[len_points - i - 1].co.z, 1]
                for p_nurbs in surfacespline5.points:
                    p_nurbs.select = True
                surfacespline5.use_endpoint_u = True
                surfacespline5.use_endpoint_v = True
    
    # Spline 6: Connects the very central Bezier point ('half'), its right handle,
    # the next point's ('half+1') left handle, and the next point ('half+1').
    # This forms the centermost vertical spline of the surface.
    surfacespline6 = surfacedata.splines.new(type='NURBS')
    surfacespline6.points.add(3)
    surfacespline6.points[0].co = [points[half].co.x, points[half].co.y, points[half].co.z, 1]
    surfacespline6.points[1].co = [points[half].handle_right.x, points[half].handle_right.y, points[half].handle_right.z, 1]
    surfacespline6.points[2].co = [points[half+1].handle_left.x, points[half+1].handle_left.y, points[half+1].handle_left.z, 1]
    surfacespline6.points[3].co = [points[half+1].co.x, points[half+1].co.y, points[half+1].co.z, 1]
    for p_nurbs in surfacespline6.points:
        p_nurbs.select = True
    surfacespline6.use_endpoint_u = True
    surfacespline6.use_endpoint_v = True
    
    # --- Create Horizontal Connections ---
    # After defining all "vertical" NURBS splines, switch to Edit Mode.
    # The 'make_segment' operator then connects the selected points of these
    # NURBS splines to form the other direction (U or V) of the surface.
    # All NURBS points were selected during their creation.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.make_segment() # This skins the surface across the created splines.
    
    # Set final surface properties (resolution and order) for each NURBS spline.
    # Order 4 means cubic NURBS.
    for s_nurbs in surfacedata.splines:
        s_nurbs.resolution_u = 4 # Default U resolution for each patch
        s_nurbs.resolution_v = 4 # Default V resolution for each patch
        if hasattr(s_nurbs, 'order_u'): # For newer Blender versions
            s_nurbs.order_u = 4
            s_nurbs.order_v = 4
        elif hasattr(s_nurbs, 'degree_u'): # For older Blender versions (degree = order - 1)
            s_nurbs.degree_u = 3 
            s_nurbs.degree_v = 3
        for p_nurbs in s_nurbs.points: # Deselect points after operation
            p_nurbs.select = False

# --- Operator Definition ---
class SP_OT_ConvertBezierToSurface(bpy.types.Operator):
    """Converts a selected Bezier curve into a NURBS surface""" # Operator Docstring
    bl_idname = "spp.convert_bezier_to_surface" # Unique identifier
    bl_label = "Convert Bezier to Surface"      # Name in operator search
    bl_description = "Convert selected Bezier curve to a NURBS surface" # Tooltip
    bl_options = {'REGISTER', 'UNDO'}          # Enable Undo for the operator
    
    # Operator Property: Center
    center: BoolProperty(
        name="Center",
        description="Consider center points when creating the surface. Matches original addon's 'Center' option.",
        default=False # CHANGED: Default set to False to match original curve_tools operator
    )
    
    # Operator Property: Resolution U
    Resolution_U: IntProperty(
        name="Resolution U",
        description="Surface resolution in the U direction",
        default=4,
        min=1, # Minimum resolution
        soft_max=64 # Soft maximum, user can input higher
    )
    
    # Operator Property: Resolution V
    Resolution_V: IntProperty(
        name="Resolution V",
        description="Surface resolution in the V direction",
        default=4,
        min=1,
        soft_max=64
    )
    
    def draw(self, context):
        """Draws the operator's properties in the UI (e.g., Redo Last panel)."""
        layout = self.layout
        col = layout.column()
        col.prop(self, 'center')
        col.prop(self, 'Resolution_U')
        col.prop(self, 'Resolution_V')
    
    @classmethod
    def poll(cls, context):
        """
        Checks if the operator can run in the current context.
        Requires at least one selected curve object.
        """
        return selected_1_or_more_curves()
    
    def execute(self, context):
        """Main execution logic of the operator."""
        # Ensure Object Mode to safely access and modify object data
        bpy.ops.object.mode_set(mode='OBJECT')
        active_object = context.active_object # The curve to convert
        curvedata = active_object.data
        
        # Create new curve data for the NURBS surface
        surfacedata = bpy.data.curves.new('Surface', type='SURFACE')
        
        # Add a new object to the scene with the surface data
        from bpy_extras import object_utils # Utility for adding objects
        surfaceobject = object_utils.object_data_add(context, surfacedata)
        
        # Copy transformations from the original curve object to the new surface object
        surfaceobject.matrix_world = active_object.matrix_world
        surfaceobject.rotation_euler = active_object.rotation_euler # Explicitly copy rotation
        
        # Set basic properties for the new surface
        surfacedata.dimensions = '3D'
        surfaceobject.show_wire = True      # Display wireframe
        surfaceobject.show_in_front = True  # Make it visible through other objects
        
        # Process each Bezier spline within the selected curve object
        for spline in curvedata.splines:
            if spline.type == 'BEZIER': # Ensure it's a Bezier spline
                # Call the core function to generate NURBS splines from this Bezier spline
                surface_from_bezier(surfacedata, spline.bezier_points, self.center)
        
        # Post-processing for the generated NURBS splines (point selection and overall resolution)
        # This loop and its logic are taken directly from the original curve_tools operator
        for spline_nurbs in surfacedata.splines: # Iterate over newly created NURBS splines
            len_p = len(spline_nurbs.points)
            # These divisions are specific to the original algorithm's point selection logic
            len_devide_4 = round(len_p / 4) + 1 
            len_devide_2 = round(len_p / 2)     
            
            # Must be in Edit Mode to select points
            bpy.context.view_layer.objects.active = surfaceobject # Ensure the new surface is active
            bpy.ops.object.mode_set(mode='EDIT')
            
            # Select a specific range of points on each NURBS spline
            # This selection doesn't alter geometry but might be for user feedback or subsequent ops
            for point_index in range(len_devide_4, len_p - len_devide_4):
                if point_index != len_devide_2 and point_index != len_devide_2 - 1:
                    spline_nurbs.points[point_index].select = True
            
            # Set the overall surface resolution based on operator properties.
            # This applies to the entire 'surfacedata' (all NURBS splines collectively).
            # Note: This is inside the loop in the original, so it gets set multiple times.
            # It effectively sets the resolution for the *entire surface object* based on the last spline processed,
            # or rather, it sets the global surface data property.
            surfacedata.resolution_u = self.Resolution_U
            surfacedata.resolution_v = self.Resolution_V
        
        bpy.ops.object.mode_set(mode='OBJECT') # Return to object mode
        return {'FINISHED'} # Indicate successful execution

# --- Registration ---
classes = [SP_OT_ConvertBezierToSurface]

def register():
    """Registers the operator class with Blender."""
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    """Unregisters the operator class from Blender."""
    for cls in reversed(classes): # Unregister in reverse order
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
