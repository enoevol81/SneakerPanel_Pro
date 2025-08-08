import bpy
from bpy.types import Panel
from ..prefs import get_prefs  # we wrote this earlier

CATEGORY = 'Sneaker Panel'

class SPP_PT_NurbsToSurface(Panel):
    bl_label = "Experimental — Nurbs To Surface"
    bl_idname = "SPP_PT_nurbs_qd"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = CATEGORY
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        try:
            return bool(get_prefs(context).enable_experimental_qd)
        except Exception:
            return False

    def draw(self, context):
        sc = context.scene
        layout = self.layout

        # mini radio to switch between the two Q&D stacks
        row = layout.row(align=True)
        b = row.operator("wm.context_set_enum", text="Bezier Q&D", depress=(sc.spp_nurbs_qd_active=='QD_BEZIER'), icon='CURVE_BEZCURVE')
        b.data_path = "scene.spp_nurbs_qd_active"; b.value = 'QD_BEZIER'
        b = row.operator("wm.context_set_enum", text="UV Curve Q&D", depress=(sc.spp_nurbs_qd_active=='QD_UV_CURVE'), icon='CURVE_NCURVE')
        b.data_path = "scene.spp_nurbs_qd_active"; b.value = 'QD_UV_CURVE'

        layout.separator()

        if sc.spp_nurbs_qd_active == 'QD_BEZIER':
            box = layout.box(); box.label(text="Bezier → Surface (Q&D)", icon='SURFACE_DATA')
            # Codex: move your existing Q&D Bezier stack here (reuse operators 1:1)
        else:
            box = layout.box(); box.label(text="UV Curve → Panel (Q&D)", icon='UV')
            # Codex: move your existing UV Curve Q&D stack here (reuse operators 1:1)

classes = [SPP_PT_NurbsToSurface]

def register():
    for cls in classes:
        try: bpy.utils.register_class(cls)
        except Exception: pass

def unregister():
    for cls in reversed(classes):
        try: bpy.utils.unregister_class(cls)
        except Exception: pass
