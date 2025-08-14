import bpy
from bpy.props import BoolProperty
from bpy.types import AddonPreferences

ADDON_ID = __package__.split(".")[0] if __package__ else __name__.split(".")[0]


class SPPrefs(AddonPreferences):
    bl_idname = ADDON_ID
    enable_experimental_qd: BoolProperty(
        name="Enable Experimental: NURBS to Surface (Q&D)",
        description="Unlock experimental quick & dirty workflows panel",
        default=False,
    )

    def draw(self, context):
        box = self.layout.box()
        col = box.column(align=True)
        col.label(text="Modules", icon="PREFERENCES")
        col.prop(self, "enable_experimental_qd")
        col.label(text="Experimental features may be unstable.", icon="INFO")


def get_prefs(context=None):
    if context is None:
        context = bpy.context
    return context.preferences.addons[ADDON_ID].preferences


def register():
    bpy.utils.register_class(SPPrefs)


def unregister():
    bpy.utils.unregister_class(SPPrefs)
