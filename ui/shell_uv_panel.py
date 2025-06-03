import bpy

class OBJECT_PT_ShellUVCrvPanel(bpy.types.Panel):
    bl_label = "Shell UV to Panel"
    bl_idname = "OBJECT_PT_shell_uv_to_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'
    bl_parent_id = "OBJECT_PT_sneaker_panel_pro_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        
        # UV to Mesh section
        box = layout.box()
        box.label(text="1. UV to Mesh:", icon='UV')
        row = box.row()
        op = row.operator("object.uv_to_mesh", icon='MESH_DATA')
        
        # Shell UV to Panel section
        box = layout.box()
        box.label(text="2. Shell UV to Panel:", icon='MODIFIER')
        row = box.row()
        row.operator("object.shell_uv_to_panel", icon='MOD_SOLIDIFY')

# Registration
classes = [OBJECT_PT_ShellUVCrvPanel]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
