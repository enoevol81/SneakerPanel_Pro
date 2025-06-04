import bpy
from bpy.props import BoolProperty, IntProperty
from mathutils import Vector
# NEW: Import for collection management
from ..utils.collections import add_object_to_panel_collection


# --- Helper Functions --- (Copied from original, assuming these are correct)
def subdivide_cubic_bezier(p1, p2, p3, p4, t):
    """Subdivides a cubic Bezier curve at parameter t."""
    p12 = (p2 - p1) * t + p1
    p23 = (p3 - p2) * t + p2
    p34 = (p4 - p3) * t + p3
    p123 = (p23 - p12) * t + p12
    p234 = (p34 - p23) * t + p23
    p1234 = (p234 - p123) * t + p123
    return [p12, p123, p1234, p234, p34]

# --- Utility Functions --- (Copied from original)
def get_selected_curves():
    """Returns a list of selected curve objects."""
    rv_list = []
    for obj in bpy.context.selected_objects:
        try:
            if obj.type == "CURVE":
                rv_list.append(obj)
        except:
            pass
    return rv_list

def selected_1_or_more_curves():
    """Checks if at least one curve object is selected and active."""
    try:
        if len(get_selected_curves()) > 0:
            return (bpy.context.active_object.type == "CURVE")
    except:
        pass
    return False

# --- Core Surface Conversion Function --- (Copied from original, with one minor context fix)
def surface_from_bezier(context_ref, surfacedata, points, center): # Added context_ref for ops
    """
    Converts a single Bezier spline's points to a set of NURBS splines
    that form a surface patch.
    """
    len_points = len(points) - 1
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
    
    surfacespline1 = surfacedata.splines.new(type='NURBS')
    surfacespline1.points.add(3)
    surfacespline1.points[0].co = [points[0].co.x, points[0].co.y, points[0].co.z, 1]
    surfacespline1.points[1].co = [points[0].handle_left.x, points[0].handle_left.y, points[0].handle_left.z, 1]
    surfacespline1.points[2].co = [points[len_points].handle_right.x, points[len_points].handle_right.y, points[len_points].handle_right.z, 1]
    surfacespline1.points[3].co = [points[len_points].co.x, points[len_points].co.y, points[len_points].co.z, 1]
    for p_nurbs in surfacespline1.points:
        p_nurbs.select = True
    surfacespline1.use_endpoint_u = True
    surfacespline1.use_endpoint_v = True

    for i in range(0, half):
        if center:
            surfacespline2 = surfacedata.splines.new(type='NURBS')
            surfacespline2.points.add(3)
            surfacespline2.points[0].co = [points[i].co.x, points[i].co.y, points[i].co.z, 1]
            surfacespline2.points[1].co = [(points[i].co.x + points[len_points - i].co.x)/2, (points[i].co.y + points[len_points - i].co.y)/2, (points[i].co.z + points[len_points - i].co.z)/2, 1]
            surfacespline2.points[2].co = [(points[len_points - i].co.x + points[i].co.x)/2, (points[len_points - i].co.y + points[i].co.y)/2, (points[len_points - i].co.z + points[i].co.z)/2, 1]
            surfacespline2.points[3].co = [points[len_points - i].co.x, points[len_points - i].co.y, points[len_points - i].co.z, 1]
            for p_nurbs in surfacespline2.points: p_nurbs.select = True
            surfacespline2.use_endpoint_u = True; surfacespline2.use_endpoint_v = True
        
        surfacespline3 = surfacedata.splines.new(type='NURBS')
        surfacespline3.points.add(3)
        surfacespline3.points[0].co = [points[i].handle_right.x, points[i].handle_right.y, points[i].handle_right.z, 1]
        surfacespline3.points[1].co = [(points[i].handle_right.x + points[len_points - i].handle_left.x)/2, (points[i].handle_right.y + points[len_points - i].handle_left.y)/2, (points[i].handle_right.z + points[len_points - i].handle_left.z)/2, 1]
        surfacespline3.points[2].co = [(points[len_points - i].handle_left.x + points[i].handle_right.x)/2, (points[len_points - i].handle_left.y + points[i].handle_right.y)/2, (points[len_points - i].handle_left.z + points[i].handle_right.z)/2, 1]
        surfacespline3.points[3].co = [points[len_points - i].handle_left.x, points[len_points - i].handle_left.y, points[len_points - i].handle_left.z, 1]
        for p_nurbs in surfacespline3.points: p_nurbs.select = True
        surfacespline3.use_endpoint_u = True; surfacespline3.use_endpoint_v = True
        
        if i + 1 <= half and len_points - i - 1 >= half + 1:
            surfacespline4 = surfacedata.splines.new(type='NURBS')
            surfacespline4.points.add(3)
            surfacespline4.points[0].co = [points[i + 1].handle_left.x, points[i + 1].handle_left.y, points[i + 1].handle_left.z, 1]
            surfacespline4.points[1].co = [(points[i + 1].handle_left.x + points[len_points - i - 1].handle_right.x)/2, (points[i + 1].handle_left.y + points[len_points - i - 1].handle_right.y)/2, (points[i + 1].handle_left.z + points[len_points - i - 1].handle_right.z)/2, 1]
            surfacespline4.points[2].co = [(points[len_points - i - 1].handle_right.x + points[i + 1].handle_left.x)/2, (points[len_points - i - 1].handle_right.y + points[i + 1].handle_left.y)/2, (points[len_points - i - 1].handle_right.z + points[i + 1].handle_left.z)/2, 1]
            surfacespline4.points[3].co = [points[len_points - i - 1].handle_right.x, points[len_points - i - 1].handle_right.y, points[len_points - i - 1].handle_right.z, 1]
            for p_nurbs in surfacespline4.points: p_nurbs.select = True
            surfacespline4.use_endpoint_u = True; surfacespline4.use_endpoint_v = True
        
        if center:
            if i + 1 <= half and len_points - i - 1 >= half + 1: 
                surfacespline5 = surfacedata.splines.new(type='NURBS')
                surfacespline5.points.add(3)
                surfacespline5.points[0].co = [points[i + 1].co.x, points[i + 1].co.y, points[i + 1].co.z, 1]
                surfacespline5.points[1].co = [(points[i + 1].co.x + points[len_points - i - 1].co.x)/2, (points[i + 1].co.y + points[len_points - i - 1].co.y)/2, (points[i + 1].co.z + points[len_points - i - 1].co.z)/2, 1]
                surfacespline5.points[2].co = [(points[len_points - i - 1].co.x + points[i + 1].co.x)/2, (points[len_points - i - 1].co.y + points[i + 1].co.y)/2, (points[len_points - i - 1].co.z + points[i + 1].co.z)/2, 1]
                surfacespline5.points[3].co = [points[len_points - i - 1].co.x, points[len_points - i - 1].co.y, points[len_points - i - 1].co.z, 1]
                for p_nurbs in surfacespline5.points: p_nurbs.select = True
                surfacespline5.use_endpoint_u = True; surfacespline5.use_endpoint_v = True
    
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
    
    # It's better to pass context to the function if it uses bpy.ops
    # Assume context_ref is the 'context' from the operator's execute method
    # The original SP_OT_ConvertBezierToSurface calls bpy.ops without context explicitly,
    # relying on implicit context. This can sometimes be risky.
    # For now, matching original, but this is an area for potential robustness improvement.
    # The active object should be the surfaceobject before calling make_segment.
    # This is handled by the main operator.
    bpy.ops.object.mode_set(mode='EDIT') # Implicit context
    bpy.ops.curve.make_segment()         # Implicit context
    
    for s_nurbs in surfacedata.splines:
        s_nurbs.resolution_u = 4
        s_nurbs.resolution_v = 4
        if hasattr(s_nurbs, 'order_u'):
            s_nurbs.order_u = 4
            s_nurbs.order_v = 4
        elif hasattr(s_nurbs, 'degree_u'):
            s_nurbs.degree_u = 3 
            s_nurbs.degree_v = 3
        for p_nurbs in s_nurbs.points:
            p_nurbs.select = False

# --- Operator Definition ---
class SP_OT_ConvertBezierToSurface(bpy.types.Operator):
    bl_idname = "spp.convert_bezier_to_surface"
    bl_label = "Convert Bezier to Surface"
    bl_description = "Convert selected Bezier curve to a NURBS surface"
    bl_options = {'REGISTER', 'UNDO'}
    
    center: BoolProperty(
        name="Center",
        description="Consider center points when creating the surface.",
        default=False
    )
    Resolution_U: IntProperty(
        name="Resolution U",
        description="Surface resolution in the U direction",
        default=4, min=1, soft_max=64
    )
    Resolution_V: IntProperty(
        name="Resolution V",
        description="Surface resolution in the V direction",
        default=4, min=1, soft_max=64
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
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        input_bezier_obj = context.active_object # Store the input Bezier curve
        if not input_bezier_obj or input_bezier_obj.type != 'CURVE':
            self.report({'ERROR'}, "Active object is not a Bezier curve.")
            return {'CANCELLED'}
        original_bezier_curvedata = input_bezier_obj.data

        # Create new curve data for the NURBS surface
        # NEW: Better naming for the data block initially
        panel_count_temp = getattr(context.scene, "spp_panel_count", 1)
        panel_name_temp = getattr(context.scene, "spp_panel_name", "Panel")
        
        base_name = f"{panel_name_temp}_Surface_{panel_count_temp}" if panel_name_temp and panel_name_temp.strip() else f"PanelSurface_{panel_count_temp}"
        
        surfacedata = bpy.data.curves.new(f"{base_name}_Data", type='SURFACE')
        
        from bpy_extras import object_utils
        surfaceobject = object_utils.object_data_add(context, surfacedata)
        # NEW: Initial name for the object, will be finalized later
        surfaceobject.name = base_name

        surfaceobject.matrix_world = input_bezier_obj.matrix_world
        surfaceobject.rotation_euler = input_bezier_obj.rotation_euler
        
        surfacedata.dimensions = '3D'
        surfaceobject.show_wire = True
        surfaceobject.show_in_front = True
        
        # Ensure surfaceobject is active for surface_from_bezier operations
        bpy.context.view_layer.objects.active = surfaceobject
        
        for spline in original_bezier_curvedata.splines:
            if spline.type == 'BEZIER':
                # Pass context for bpy.ops calls within surface_from_bezier
                surface_from_bezier(context, surfacedata, spline.bezier_points, self.center)
        
        # Post-processing for the generated NURBS splines (overall resolution)
        # The point selection loop from original addon seems less critical for this workflow.
        # If it was important, it would go here, operating in Edit Mode on surfaceobject.
        # For now, focusing on resolution setting.
        
        bpy.context.view_layer.objects.active = surfaceobject
        if context.mode != 'OBJECT': # Ensure object mode before setting data properties if not already
             bpy.ops.object.mode_set(mode='OBJECT')

        surfacedata.resolution_u = self.Resolution_U
        surfacedata.resolution_v = self.Resolution_V
        
        # --- Finalizing object: Naming, Collection, Hiding Input ---
        
        # Ensure we are in Object Mode and the surfaceobject is selected and active
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        if bpy.context.active_object != surfaceobject:
            bpy.context.view_layer.objects.active = surfaceobject
        
        # Deselect all then reselect the new surface object
        bpy.ops.object.select_all(action='DESELECT')
        surfaceobject.select_set(True)

        panel_count = 1
        panel_name = "Panel" # Default base name
        if hasattr(context.scene, "spp_panel_count"):
            panel_count = context.scene.spp_panel_count
        if hasattr(context.scene, "spp_panel_name"):
            current_panel_name = context.scene.spp_panel_name
            if current_panel_name and current_panel_name.strip(): # Use if not empty or just whitespace
                panel_name = current_panel_name
            
        # Finalize object name
        surfaceobject.name = f"{panel_name}_Surface_{panel_count}"
        # Finalize data block name
        surfacedata.name = f"{surfaceobject.name}_Data" # surfacedata is surfaceobject.data
            
        # Add the new surface object to the designated panel collection
        add_object_to_panel_collection(surfaceobject, panel_count, panel_name)
            
        # Hide the original Bezier curve object
        if input_bezier_obj and input_bezier_obj != surfaceobject :
            input_bezier_obj.hide_viewport = True 
            # Consider input_bezier_obj.hide_set(True) for render hiding too

        self.report({'INFO'}, f"Converted '{input_bezier_obj.name}' to '{surfaceobject.name}', added to collection.")
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