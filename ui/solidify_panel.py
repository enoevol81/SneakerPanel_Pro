import bpy

class OBJECT_PT_SolidifyPanel(bpy.types.Panel):
    bl_label = "Finalize"
    bl_idname = "OBJECT_PT_solidify_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Solidify Panel Tools:")
        layout.operator("object.solidify_panel", icon='MODIFIER')

# Registration
classes = [OBJECT_PT_SolidifyPanel]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
