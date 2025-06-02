import bpy
from bpy.props import BoolProperty, IntProperty

# Utility stubs (replace with actual implementations if available)
class util:
    @staticmethod
    def Selected1OrMoreCurves():
        obj = bpy.context.active_object
        return obj and obj.type == 'CURVE'

class object_utils:
    @staticmethod
    def object_data_add(context, curve_data):
        obj = bpy.data.objects.new(curve_data.name, curve_data)
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        return obj

# Operator: Convert Bezier to Surface
class ConvertBezierToSurface(bpy.types.Operator):
    bl_idname = "curvetools.convert_bezier_to_surface"
    bl_label = "Convert Bezier to Surface"
    bl_description = "Convert Bezier to Surface"
    bl_options = {'REGISTER', 'UNDO'}

    Center = BoolProperty(
        name="Center",
        default=False,
        description="Consider center points"
    )

    Resolution_U = IntProperty(
        name="Resolution_U",
        default=4,
        min=1, max=64,
        soft_min=1,
        description="Surface resolution U"
    )

    Resolution_V = IntProperty(
        name="Resolution_V",
        default=4,
        min=1, max=64,
        soft_min=1,
        description="Surface resolution V"
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, 'Center')
        col.prop(self, 'Resolution_U')
        col.prop(self, 'Resolution_V')

    @classmethod
    def poll(cls, context):
        return util.Selected1OrMoreCurves()

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        active_object = context.active_object
        curvedata = active_object.data

        surfacedata = bpy.data.curves.new('Surface', type='SURFACE')
        surfaceobject = object_utils.object_data_add(context, surfacedata)
        surfaceobject.matrix_world = active_object.matrix_world
        surfaceobject.rotation_euler = active_object.rotation_euler
        surfacedata.dimensions = '3D'
        surfaceobject.show_wire = True
        surfaceobject.show_in_front = True

        for spline in curvedata.splines:
            # Define or import SurfaceFromBezier before using it
            def SurfaceFromBezier(surfacedata, bezier_points, center):
                # Placeholder implementation: add your logic here
                # For now, just print to avoid errors
                print("SurfaceFromBezier called with", surfacedata, bezier_points, center)
            SurfaceFromBezier(surfacedata, spline.bezier_points, self.Center)

        for spline in surfacedata.splines:
            len_p = len(spline.points)
            len_devide_4 = round(len_p / 4) + 1
            len_devide_2 = round(len_p / 2)
            bpy.ops.object.mode_set(mode='EDIT')
            for point_index in range(len_devide_4, len_p - len_devide_4):
                if point_index != len_devide_2 and point_index != len_devide_2 - 1:
                    spline.points[point_index].select = True

            surfacedata.resolution_u = self.Resolution_U
            surfacedata.resolution_v = self.Resolution_V

        return {'FINISHED'}

# Registration
classes = [ConvertBezierToSurface]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
