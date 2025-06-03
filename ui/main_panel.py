import bpy

class OBJECT_PT_SneakerPanelProMain(bpy.types.Panel):
    bl_label = "Sneaker Panel Pro"
    bl_idname = "OBJECT_PT_sneaker_panel_pro_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'
    
    def draw(self, context):
        layout = self.layout
        
        # Panel number and name (global settings)
        box = layout.box()
        box.label(text="Panel Settings", icon="SETTINGS")
        
        row = box.row()
        row.label(text="Panel Number:")
        row.prop(context.scene, "spp_panel_count", text="")
        
        row = box.row()
        row.label(text="Panel Name:")
        row.prop(context.scene, "spp_panel_name", text="")
        
        box.prop_search(context.scene, "spp_shell_object", bpy.data, "objects", text="Shell Object")
        
     
# Registration
classes = [OBJECT_PT_SneakerPanelProMain]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
