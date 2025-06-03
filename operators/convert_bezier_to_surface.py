import bpy
from bpy.props import BoolProperty, IntProperty
from mathutils import Vector

# --- Helper Functions ---
def subdivide_cubic_bezier(p1, p2, p3, p4, t):
    """Subdivides a cubic Bezier curve at parameter t."""
    p12 = (p2 - p1) * t + p1
    p23 = (p3 - p2) * t + p2
    p34 = (p4 - p3) * t + p3
    p123 = (p23 - p12) * t + p12
    p234 = (p34 - p23) * t + p23
    p1234 = (p234 - p123) * t + p123
    return [p12, p123, p1234, p234, p34]

# --- Utility Functions ---
def get_selected_curves():
    rv_list = []
    for obj in bpy.context.selected_objects:
        try:
            if obj.type == "CURVE":
                rv_list.append(obj)
        except:
            pass
    return rv_list

def selected_1_or_more_curves():
    try:
        if len(get_selected_curves()) > 0:
            return (bpy.context.active_object.type == "CURVE")
    except:
        pass
    return False

# --- Core Surface Conversion Function ---
def surface_from_bezier(surfacedata, points, center):
    """Convert Bezier points to NURBS surface splines."""
    len_points = len(points) - 1
    
    # If even number of points, add a subdivision point to make it odd
    if len_points % 2 == 0:
        h = subdivide_cubic_bezier(
            points[len_points].co, points[len_points].handle_right,
            points[0].handle_left, points[0].co, 0.5
        )
        points.add(1)
        len_points = len(points) - 1
        points[len_points - 1].handle_right = h[0]
        points[len_points].handle_left = h[1]
        points[len_points].co = h[2]
        points[len_points].handle_right = h[3]
        points[0].handle_left = h[4]
    
    half = round((len_points + 1)/2) - 1
    
    # Create spline 1 (first vertical spline)
    surfacespline1 = surfacedata.splines.new(type='NURBS')
    surfacespline1.points.add(3)
    surfacespline1.points[0].co = [points[0].co.x, points[0].co.y, points[0].co.z, 1]
    surfacespline1.points[1].co = [points[0].handle_left.x, points[0].handle_left.y, points[0].handle_left.z, 1]
    surfacespline1.points[2].co = [points[len_points].handle_right.x, points[len_points].handle_right.y, points[len_points].handle_right.z, 1]
    surfacespline1.points[3].co = [points[len_points].co.x, points[len_points].co.y, points[len_points].co.z, 1]
    for p in surfacespline1.points:
        p.select = True
    surfacespline1.use_endpoint_u = True
    surfacespline1.use_endpoint_v = True
    
    # Create intermediate splines
    for i in range(0, half):
        if center:
            # Create spline 2 (center spline)
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
            for p in surfacespline2.points:
                p.select = True
            surfacespline2.use_endpoint_u = True
            surfacespline2.use_endpoint_v = True
        
        # Create spline 3 (handle spline)
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
        for p in surfacespline3.points:
            p.select = True
        surfacespline3.use_endpoint_u = True
        surfacespline3.use_endpoint_v = True
        
        # Create spline 4 (handle spline for opposite side)
        if i + 1 <= half and len_points - i - 1 >= half + 1:  # Ensure indices are valid
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
            for p in surfacespline4.points:
                p.select = True
            surfacespline4.use_endpoint_u = True
            surfacespline4.use_endpoint_v = True
        
        if center:
            # Create spline 5 (center spline for next point)
            if i + 1 <= half and len_points - i - 1 >= half + 1:  # Ensure indices are valid
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
                for p in surfacespline5.points:
                    p.select = True
                surfacespline5.use_endpoint_u = True
                surfacespline5.use_endpoint_v = True
    
    # Create spline 6 (middle point spline)
    surfacespline6 = surfacedata.splines.new(type='NURBS')
    surfacespline6.points.add(3)
    surfacespline6.points[0].co = [points[half].co.x, points[half].co.y, points[half].co.z, 1]
    surfacespline6.points[1].co = [points[half].handle_right.x, points[half].handle_right.y, points[half].handle_right.z, 1]
    surfacespline6.points[2].co = [points[half+1].handle_left.x, points[half+1].handle_left.y, points[half+1].handle_left.z, 1]
    surfacespline6.points[3].co = [points[half+1].co.x, points[half+1].co.y, points[half+1].co.z, 1]
    for p in surfacespline6.points:
        p.select = True
    surfacespline6.use_endpoint_u = True
    surfacespline6.use_endpoint_v = True
    
    # Now create the horizontal connections between vertical splines
    # This is done in EDIT mode using bpy.ops.curve.make_segment()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.make_segment()
    
    # Set resolution and other properties for all splines
    for s in surfacedata.splines:
        s.resolution_u = 4
        s.resolution_v = 4
        # Set order/degree using the correct attribute names
        if hasattr(s, 'order_u'):
            s.order_u = 4
            s.order_v = 4
        elif hasattr(s, 'degree_u'):
            s.degree_u = 3  # Degree is order-1 (cubic = degree 3)
            s.degree_v = 3
        for p in s.points:
            p.select = False

# --- Operator Definition ---
class SP_OT_ConvertBezierToSurface(bpy.types.Operator):
    bl_idname = "spp.convert_bezier_to_surface"
    bl_label = "Convert Bezier to Surface"
    bl_description = "Convert Bezier to Surface"
    bl_options = {'REGISTER', 'UNDO'}
    
    center: BoolProperty(
        name="Center",
        description="Create center splines",
        default=True
    )
    
    Resolution_U: IntProperty(
        name="Resolution U",
        description="Resolution in U direction",
        default=4,
        min=1,
        soft_max=64
    )
    
    Resolution_V: IntProperty(
        name="Resolution V",
        description="Resolution in V direction",
        default=4,
        min=1,
        soft_max=64
    )
    
    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, 'center')
        col.prop(self, 'Resolution_U')
        col.prop(self, 'Resolution_V')
    
    @classmethod
    def poll(cls, context):
        return selected_1_or_more_curves()
    
    def execute(self, context):
        # Store original mode to restore later
        original_mode = context.object.mode if context.object else 'OBJECT'
        
        # Switch to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        active_object = context.active_object
        curvedata = active_object.data
        
        # Create new surface data and object
        surfacedata = bpy.data.curves.new('Surface', type='SURFACE')
        surfaceobject = bpy.data.objects.new(f"{active_object.name}_Surface", surfacedata)
        context.collection.objects.link(surfaceobject)
        
        # Copy transform from original
        surfaceobject.matrix_world = active_object.matrix_world
        surfaceobject.rotation_euler = active_object.rotation_euler
        
        # Set surface properties
        surfacedata.dimensions = '3D'
        surfaceobject.show_wire = True
        surfaceobject.show_in_front = True
        
        # Deselect all objects
        for obj in context.selected_objects:
            obj.select_set(False)
        
        # Select and make the new surface active
        surfaceobject.select_set(True)
        context.view_layer.objects.active = surfaceobject
        
        # Process each spline in the curve
        for spline in curvedata.splines:
            if spline.type == 'BEZIER':
                surface_from_bezier(surfacedata, spline.bezier_points, self.center)
        
        # Set resolution
        for spline in surfacedata.splines:
            len_p = len(spline.points)
            len_divide_4 = round(len_p / 4) + 1
            len_divide_2 = round(len_p / 2)
            
            # Select specific points (middle section)
            bpy.ops.object.mode_set(mode='EDIT')
            for point_index in range(len_divide_4, len_p - len_divide_4):
                if point_index != len_divide_2 and point_index != len_divide_2 - 1:
                    spline.points[point_index].select = True
        
        # Set resolution
        surfacedata.resolution_u = self.Resolution_U
        surfacedata.resolution_v = self.Resolution_V
        
        # Set order/degree using the correct attribute names
        if hasattr(surfacedata, 'order_u'):
            surfacedata.order_u = 4
            surfacedata.order_v = 4
        elif hasattr(surfacedata, 'degree_u'):
            surfacedata.degree_u = 3  # Degree is order-1 (cubic = degree 3)
            surfacedata.degree_v = 3
        
        # Create and assign a material
        mat_name = f"{active_object.name}_Surface_Material"
        if mat_name in bpy.data.materials:
            mat = bpy.data.materials[mat_name]
        else:
            mat = bpy.data.materials.new(name=mat_name)
            mat.diffuse_color = (0.8, 0.8, 0.8, 1.0)  # Light gray with full opacity
            mat.use_nodes = True
        
        # Assign material to the surface object
        if surfaceobject.data.materials:
            surfaceobject.data.materials[0] = mat
        else:
            surfaceobject.data.materials.append(mat)
        
        # Restore original mode if needed
        if original_mode != 'OBJECT':
            if active_object and active_object.name in bpy.data.objects:
                context.view_layer.objects.active = active_object
                bpy.ops.object.mode_set(mode=original_mode)
            else:
                context.view_layer.objects.active = surfaceobject
        
        self.report({'INFO'}, f"Converted '{active_object.name}' to '{surfaceobject.name}'")
        return {'FINISHED'}

# --- Registration ---
classes = [SP_OT_ConvertBezierToSurface]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
