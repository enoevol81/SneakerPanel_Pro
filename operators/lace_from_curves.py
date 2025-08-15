import bpy
from ..utils.collections import add_object_to_panel_collection

class OBJECT_OT_GPToCurveAlt(bpy.types.Operator):
    bl_idname = "object.gp_to_curve_alt"
    bl_label = "GP To Curve (Alt)"
    bl_description = "Alternative GP to Curve conversion with panel workflow integration"

    def execute(self, context):
        bpy.ops.ed.undo_push(message="Convert GP to Curve")
        bpy.ops.object.gpto_simple_curve_convert()
        curve_obj = bpy.context.object
        curve_data = curve_obj.data

        panel_count = context.scene.spp_panel_count if hasattr(context.scene, "spp_panel_count") else 1
        panel_name = context.scene.spp_panel_name if hasattr(context.scene, "spp_panel_name") else "Panel"

        if panel_name and panel_name.strip():
            curve_obj.name = f"{panel_name}_Curve_{panel_count}"
        else:
            curve_obj.name = f"Curve_{panel_count}"

        add_object_to_panel_collection(curve_obj, panel_count, panel_name)

        for spline in curve_data.splines:
            spline.type = 'BEZIER'
            spline.use_cyclic_u = True
            for bp in spline.bezier_points:
                bp.handle_left_type = 'AUTO'
                bp.handle_right_type = 'AUTO'

        bpy.ops.object.editmode_toggle()
        bpy.context.tool_settings.use_snap = True
        bpy.context.tool_settings.snap_elements = {'FACE_NEAREST'}
        bpy.context.tool_settings.snap_target = 'CLOSEST'

        bpy.ops.curve.select_all(action='SELECT')
        bpy.ops.transform.translate(
            value=(0, 0, 0),
            orient_type='GLOBAL',
            orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
            orient_matrix_type='GLOBAL',
            mirror=False,
            use_proportional_edit=False,
            proportional_edit_falloff='SMOOTH',
            proportional_size=1,
            use_proportional_connected=False,
            use_proportional_projected=False,
            snap=True,
            snap_elements={'FACE_NEAREST'},
            use_snap_project=False,
            snap_target='CLOSEST',
            use_snap_self=True,
            use_snap_edit=True,
            use_snap_nonedit=True,
            use_snap_selectable=False
        )

        self.report({'INFO'}, f"Grease Pencil converted to cyclic Bezier Curve '{curve_obj.name}'. Edit as needed.")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(OBJECT_OT_GPToCurveAlt)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_GPToCurveAlt)
