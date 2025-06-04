import bpy
from ..utils.collections import get_panel_collection

class OBJECT_OT_SolidifyPanel(bpy.types.Operator):
    bl_idname = "object.solidify_panel"
    bl_label = "Solidify Panel"
    bl_description = "Add solidify modifier to the selected panel"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object")
            return {'CANCELLED'}

        # Check if solidify modifier already exists
        solidify = obj.modifiers.get('Solidify')
        if not solidify:
            solidify = obj.modifiers.new(name='Solidify', type='SOLIDIFY')

        # Apply settings from scene properties
        solidify.thickness = context.scene.spp_solidify_thickness
        solidify.offset = context.scene.spp_solidify_offset
        solidify.use_even_offset = context.scene.spp_solidify_even_thickness
        solidify.use_rim = context.scene.spp_solidify_rim
        solidify.use_rim_only = context.scene.spp_solidify_rim_only

        return {'FINISHED'}

class OBJECT_OT_ApplySolidify(bpy.types.Operator):
    bl_idname = "object.apply_solidify"
    bl_label = "Apply Solidify"
    bl_description = "Apply the solidify modifier to the mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object")
            return {'CANCELLED'}

        solidify = obj.modifiers.get('Solidify')
        if not solidify:
            self.report({'ERROR'}, "No solidify modifier found")
            return {'CANCELLED'}

        # Apply the modifier
        bpy.ops.object.modifier_apply(modifier=solidify.name)
        self.report({'INFO'}, "Solidify modifier applied successfully")

        return {'FINISHED'}

# Registration
classes = [OBJECT_OT_SolidifyPanel, OBJECT_OT_ApplySolidify]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
