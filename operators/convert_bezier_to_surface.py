import bpy
from bpy.props import BoolProperty, IntProperty

from ..utils.collections import add_object_to_panel_collection


# --- Helper Functions ---
def subdivide_cubic_bezier(p1, p2, p3, p4, t):
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
        except Exception:
            pass
    return rv_list


def selected_1_or_more_curves():
    try:
        if len(get_selected_curves()) > 0:
            return bpy.context.active_object.type == "CURVE"
    except Exception:
        pass
    return False


# --- Core Surface Conversion Function ---
def surface_from_bezier(context_ref, surfacedata, points, center):
    len_points = len(points) - 1
    if len_points % 2 == 0:  # Ensure odd number of points for pairing algorithm
        h = subdivide_cubic_bezier(
            points[len_points].co,
            points[len_points].handle_right,
            points[0].handle_left,
            points[0].co,
            0.5,
        )
        points.add(1)
        len_points = len(points) - 1
        points[len_points - 1].handle_right = h[0]
        points[len_points].handle_left = h[1]
        points[len_points].co = h[2]
        points[len_points].handle_right = h[3]
        points[0].handle_left = h[4]

    half = round((len_points + 1) / 2) - 1

    # Create guiding NURBS splines and add them to surfacedata
    # (Detailed spline creation logic from your original file)
    temp_splines_for_make_segment = []  # Store newly created splines to operate on later

    surfacespline1 = surfacedata.splines.new(type="NURBS")
    temp_splines_for_make_segment.append(surfacespline1)
    surfacespline1.points.add(3)
    surfacespline1.points[0].co = [points[0].co.x, points[0].co.y, points[0].co.z, 1]
    surfacespline1.points[1].co = [
        points[0].handle_left.x,
        points[0].handle_left.y,
        points[0].handle_left.z,
        1,
    ]
    surfacespline1.points[2].co = [
        points[len_points].handle_right.x,
        points[len_points].handle_right.y,
        points[len_points].handle_right.z,
        1,
    ]
    surfacespline1.points[3].co = [
        points[len_points].co.x,
        points[len_points].co.y,
        points[len_points].co.z,
        1,
    ]
    for p_nurbs in surfacespline1.points:
        p_nurbs.select = True
    surfacespline1.use_endpoint_u = True
    surfacespline1.use_endpoint_v = True

    for i in range(0, half):
        if center:
            surfacespline2 = surfacedata.splines.new(type="NURBS")
            temp_splines_for_make_segment.append(surfacespline2)
            surfacespline2.points.add(3)
            # ... (fill points as before) ...
            surfacespline2.points[0].co = [
                points[i].co.x,
                points[i].co.y,
                points[i].co.z,
                1,
            ]
            surfacespline2.points[1].co = [
                (points[i].co.x + points[len_points - i].co.x) / 2,
                (points[i].co.y + points[len_points - i].co.y) / 2,
                (points[i].co.z + points[len_points - i].co.z) / 2,
                1,
            ]
            surfacespline2.points[2].co = [
                (points[len_points - i].co.x + points[i].co.x) / 2,
                (points[len_points - i].co.y + points[i].co.y) / 2,
                (points[len_points - i].co.z + points[i].co.z) / 2,
                1,
            ]
            surfacespline2.points[3].co = [
                points[len_points - i].co.x,
                points[len_points - i].co.y,
                points[len_points - i].co.z,
                1,
            ]
            for p_nurbs in surfacespline2.points:
                p_nurbs.select = True
            surfacespline2.use_endpoint_u = True
            surfacespline2.use_endpoint_v = True

        surfacespline3 = surfacedata.splines.new(type="NURBS")
        temp_splines_for_make_segment.append(surfacespline3)
        surfacespline3.points.add(3)
        # ... (fill points as before) ...
        surfacespline3.points[0].co = [
            points[i].handle_right.x,
            points[i].handle_right.y,
            points[i].handle_right.z,
            1,
        ]
        surfacespline3.points[1].co = [
            (points[i].handle_right.x + points[len_points - i].handle_left.x) / 2,
            (points[i].handle_right.y + points[len_points - i].handle_left.y) / 2,
            (points[i].handle_right.z + points[len_points - i].handle_left.z) / 2,
            1,
        ]
        surfacespline3.points[2].co = [
            (points[len_points - i].handle_left.x + points[i].handle_right.x) / 2,
            (points[len_points - i].handle_left.y + points[i].handle_right.y) / 2,
            (points[len_points - i].handle_left.z + points[i].handle_right.z) / 2,
            1,
        ]
        surfacespline3.points[3].co = [
            points[len_points - i].handle_left.x,
            points[len_points - i].handle_left.y,
            points[len_points - i].handle_left.z,
            1,
        ]
        for p_nurbs in surfacespline3.points:
            p_nurbs.select = True
        surfacespline3.use_endpoint_u = True
        surfacespline3.use_endpoint_v = True

        if i + 1 <= half and len_points - i - 1 >= half + 1:
            surfacespline4 = surfacedata.splines.new(type="NURBS")
            temp_splines_for_make_segment.append(surfacespline4)
            surfacespline4.points.add(3)
            # ... (fill points as before) ...
            surfacespline4.points[0].co = [
                points[i + 1].handle_left.x,
                points[i + 1].handle_left.y,
                points[i + 1].handle_left.z,
                1,
            ]
            surfacespline4.points[1].co = [
                (
                    points[i + 1].handle_left.x
                    + points[len_points - i - 1].handle_right.x
                )
                / 2,
                (
                    points[i + 1].handle_left.y
                    + points[len_points - i - 1].handle_right.y
                )
                / 2,
                (
                    points[i + 1].handle_left.z
                    + points[len_points - i - 1].handle_right.z
                )
                / 2,
                1,
            ]
            surfacespline4.points[2].co = [
                (
                    points[len_points - i - 1].handle_right.x
                    + points[i + 1].handle_left.x
                )
                / 2,
                (
                    points[len_points - i - 1].handle_right.y
                    + points[i + 1].handle_left.y
                )
                / 2,
                (
                    points[len_points - i - 1].handle_right.z
                    + points[i + 1].handle_left.z
                )
                / 2,
                1,
            ]
            surfacespline4.points[3].co = [
                points[len_points - i - 1].handle_right.x,
                points[len_points - i - 1].handle_right.y,
                points[len_points - i - 1].handle_right.z,
                1,
            ]
            for p_nurbs in surfacespline4.points:
                p_nurbs.select = True
            surfacespline4.use_endpoint_u = True
            surfacespline4.use_endpoint_v = True

        if center:
            if i + 1 <= half and len_points - i - 1 >= half + 1:
                surfacespline5 = surfacedata.splines.new(type="NURBS")
                temp_splines_for_make_segment.append(surfacespline5)
                surfacespline5.points.add(3)
                # ... (fill points as before) ...
                surfacespline5.points[0].co = [
                    points[i + 1].co.x,
                    points[i + 1].co.y,
                    points[i + 1].co.z,
                    1,
                ]
                surfacespline5.points[1].co = [
                    (points[i + 1].co.x + points[len_points - i - 1].co.x) / 2,
                    (points[i + 1].co.y + points[len_points - i - 1].co.y) / 2,
                    (points[i + 1].co.z + points[len_points - i - 1].co.z) / 2,
                    1,
                ]
                surfacespline5.points[2].co = [
                    (points[len_points - i - 1].co.x + points[i + 1].co.x) / 2,
                    (points[len_points - i - 1].co.y + points[i + 1].co.y) / 2,
                    (points[len_points - i - 1].co.z + points[i + 1].co.z) / 2,
                    1,
                ]
                surfacespline5.points[3].co = [
                    points[len_points - i - 1].co.x,
                    points[len_points - i - 1].co.y,
                    points[len_points - i - 1].co.z,
                    1,
                ]
                for p_nurbs in surfacespline5.points:
                    p_nurbs.select = True
                surfacespline5.use_endpoint_u = True
                surfacespline5.use_endpoint_v = True

    surfacespline6 = surfacedata.splines.new(type="NURBS")
    temp_splines_for_make_segment.append(surfacespline6)
    surfacespline6.points.add(3)
    surfacespline6.points[0].co = [
        points[half].co.x,
        points[half].co.y,
        points[half].co.z,
        1,
    ]
    surfacespline6.points[1].co = [
        points[half].handle_right.x,
        points[half].handle_right.y,
        points[half].handle_right.z,
        1,
    ]
    surfacespline6.points[2].co = [
        points[half + 1].handle_left.x,
        points[half + 1].handle_left.y,
        points[half + 1].handle_left.z,
        1,
    ]
    surfacespline6.points[3].co = [
        points[half + 1].co.x,
        points[half + 1].co.y,
        points[half + 1].co.z,
        1,
    ]
    for p_nurbs in surfacespline6.points:
        p_nurbs.select = True
    surfacespline6.use_endpoint_u = True
    surfacespline6.use_endpoint_v = True

    # Assumes context_ref.active_object is the surface object.
    # The calling function (SP_OT_ConvertBezierToSurface.execute) ensures this.
    original_mode = context_ref.active_object.mode
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.curve.make_segment()  # This skins the surface across the selected points of the new splines

    # Set properties for the NURBS splines that constitute the surface patch
    for s_nurbs in (
        temp_splines_for_make_segment
    ):  # Iterate over splines created in this function call
        s_nurbs.resolution_u = 4  # Default U resolution for each patch segment
        s_nurbs.resolution_v = 4  # Default V resolution for each patch segment
        if hasattr(s_nurbs, "order_u"):
            s_nurbs.order_u = 4
            s_nurbs.order_v = 4
        elif hasattr(s_nurbs, "degree_u"):
            s_nurbs.degree_u = 3
            s_nurbs.degree_v = 3
        for p_nurbs in s_nurbs.points:  # Deselect points after operation
            p_nurbs.select = False

    if context_ref.active_object.mode != original_mode:  # Usually back to 'OBJECT'
        bpy.ops.object.mode_set(mode=original_mode)


# --- Operator Definition ---
class SP_OT_ConvertBezierToSurface(bpy.types.Operator):
    bl_idname = "spp.convert_bezier_to_surface"
    bl_label = "Convert Bezier to Surface"
    bl_description = "Convert selected Bezier curve to a NURBS surface"
    bl_options = {"REGISTER", "UNDO"}

    center: BoolProperty(
        name="Center",
        description="Consider center points when creating the surface.",
        default=False,
    )
    Resolution_U: IntProperty(
        name="Resolution U",
        description="Overall surface resolution in the U direction for the final surface object",
        default=4,
        min=1,
        soft_max=64,
    )
    Resolution_V: IntProperty(
        name="Resolution V",
        description="Overall surface resolution in the V direction for the final surface object",
        default=4,
        min=1,
        soft_max=64,
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "center")
        col.prop(self, "Resolution_U")
        col.prop(self, "Resolution_V")

    @classmethod
    def poll(cls, context):
        return selected_1_or_more_curves()

    def execute(self, context):
        if context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        input_bezier_obj = context.active_object
        if not input_bezier_obj or input_bezier_obj.type != "CURVE":
            self.report({"ERROR"}, "Active object is not a Bezier curve.")
            return {"CANCELLED"}
        if (
            not input_bezier_obj.data.splines
            or input_bezier_obj.data.splines[0].type != "BEZIER"
        ):
            self.report(
                {"ERROR"}, "Active curve object does not contain Bezier splines."
            )
            return {"CANCELLED"}
        original_bezier_curvedata = input_bezier_obj.data

        panel_count_temp = getattr(context.scene, "spp_panel_count", 1)
        panel_name_temp = getattr(context.scene, "spp_panel_name", "Panel")
        base_name = (
            f"{panel_name_temp}_Surface_{panel_count_temp}"
            if panel_name_temp and panel_name_temp.strip()
            else f"PanelSurface_{panel_count_temp}"
        )

        surfacedata = bpy.data.curves.new(f"{base_name}_DataInit", type="SURFACE")

        from bpy_extras import object_utils

        surfaceobject = object_utils.object_data_add(context, surfacedata)
        surfaceobject.name = base_name

        surfaceobject.matrix_world = input_bezier_obj.matrix_world
        surfaceobject.rotation_euler = input_bezier_obj.rotation_euler

        surfacedata.dimensions = "3D"
        surfaceobject.show_wire = True
        surfaceobject.show_in_front = True

        # Ensure surfaceobject is active for surface_from_bezier operations
        bpy.context.view_layer.objects.active = surfaceobject

        for spline in original_bezier_curvedata.splines:
            if spline.type == "BEZIER":
                surface_from_bezier(
                    context, surfacedata, spline.bezier_points, self.center
                )

        # After loop, surfaceobject should be active. Set overall resolution.
        bpy.context.view_layer.objects.active = surfaceobject  # Re-ensure
        if (
            context.active_object.mode != "OBJECT"
        ):  # surface_from_bezier should leave it as it found it
            bpy.ops.object.mode_set(mode="OBJECT")

        surfacedata.resolution_u = (
            self.Resolution_U
        )  # Set overall resolution from operator props
        surfacedata.resolution_v = self.Resolution_V

        # --- Snap surface to shell ---
        # self.report({'INFO'}, f"Snapping {surfaceobject.name} to nearest surface.") # Report at the end
        bpy.ops.object.select_all(action="DESELECT")
        surfaceobject.select_set(True)
        bpy.context.view_layer.objects.active = surfaceobject

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.curve.select_all(action="SELECT")
        bpy.ops.transform.translate(
            value=(0, 0, 0),
            orient_type="GLOBAL",
            orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
            orient_matrix_type="GLOBAL",
            mirror=False,
            use_proportional_edit=False,
            proportional_edit_falloff="SMOOTH",
            proportional_size=1,
            use_proportional_connected=False,
            use_proportional_projected=False,
            snap=True,
            snap_elements={"FACE_NEAREST"},
            snap_target="CLOSEST",
            use_snap_project=False,
            use_snap_self=True,
            use_snap_edit=True,
            use_snap_nonedit=True,
            use_snap_selectable=False,
        )
        bpy.ops.object.mode_set(mode="OBJECT")
        # --- End of Snap surface to shell ---

        # --- Finalizing object: Naming, Collection, Hiding Input ---
        bpy.context.view_layer.objects.active = surfaceobject  # Ensure active
        if context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        bpy.ops.object.select_all(action="DESELECT")
        surfaceobject.select_set(True)

        panel_count = getattr(context.scene, "spp_panel_count", 1)
        panel_name_str = getattr(context.scene, "spp_panel_name", "Panel")
        if not (
            panel_name_str and panel_name_str.strip()
        ):  # Ensure panel_name_str is not empty or just whitespace
            panel_name_str = "Panel"

        final_surface_name = f"{panel_name_str}_Surface_{panel_count}"
        surfaceobject.name = final_surface_name
        surfacedata.name = f"{final_surface_name}_Data"

        add_object_to_panel_collection(surfaceobject, panel_count, panel_name_str)

        if input_bezier_obj and input_bezier_obj.name in bpy.data.objects:
            if input_bezier_obj != surfaceobject:
                input_bezier_obj.hide_viewport = True

        self.report(
            {"INFO"},
            f"Converted '{input_bezier_obj.name}' to '{surfaceobject.name}', snapped, and added to collection.",
        )
        return {"FINISHED"}


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
