import bpy

class OBJECT_PT_SolidifyPanel(bpy.types.Panel):
    bl_label = "Finalize"
    bl_idname = "OBJECT_PT_solidify_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        scene = context.scene

        # Solidify button if no modifier exists
        if not obj.modifiers.get('Solidify'):
            layout.operator("object.solidify_panel", text="Solidify", icon='MODIFIER')
            return

        # Parameters box
        box = layout.box()
        box.label(text="Solidify Parameters:", icon='MODIFIER')
        
        # Thickness
        row = box.row()
        row.prop(scene, "spp_solidify_thickness", text="Thickness")

        # Offset
        row = box.row()
        row.prop(scene, "spp_solidify_offset", text="Offset")

        # Even thickness
        row = box.row()
        row.prop(scene, "spp_solidify_even_thickness", text="Even Thickness")

        # Rim options
        col = box.column()
        row = col.row()
        row.prop(scene, "spp_solidify_rim", text="Fill Rim")
        if scene.spp_solidify_rim:
            row = col.row()
            row.prop(scene, "spp_solidify_rim_only", text="Only Rim")

        # Apply button
        layout.operator("object.apply_solidify", text="Apply", icon='CHECKMARK')

# Registration
classes = [OBJECT_PT_SolidifyPanel]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
