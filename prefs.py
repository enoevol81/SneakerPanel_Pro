import bpy

class SPPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__

    def shell_object_poll(obj):
        return obj.type == 'MESH'
    
        shell_object: bpy.props.PointerProperty(
            name="Shell Object",
            type=bpy.types.Object,
            poll=shell_object_poll
        )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Global Settings")
        layout.prop(self, "shell_object", text="Shell (Target Mesh)")


def get_shell_object():
    prefs = bpy.context.preferences.addons[__package__].preferences
    return prefs.shell_object


def register():
    bpy.utils.register_class(SPPrefs)


def unregister():
    bpy.utils.unregister_class(SPPrefs)
