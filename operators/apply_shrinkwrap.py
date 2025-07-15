import bpy
from bpy.types import Operator
from bpy.props import BoolProperty


class OBJECT_OT_apply_shrinkwrap(Operator):
    """Add shrinkwrap modifier to selected mesh using shell object"""
    bl_idname = "mesh.apply_shrinkwrap"
    bl_label = "Apply Shrinkwrap"
    bl_options = {'REGISTER', 'UNDO'}
    
    apply_modifier: BoolProperty(
        name="Apply Modifier",
        description="Apply the shrinkwrap modifier immediately",
        default=False
    )
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "apply_modifier")
        
        # Show shell object info if available
        shell = getattr(context.scene, "spp_shell_object", None)
        if shell and isinstance(shell, str):
            shell = bpy.data.objects.get(shell)
        
        if shell:
            layout.separator()
            layout.label(text=f"Shell Object: {shell.name}", icon="OUTLINER_OB_MESH")
        else:
            layout.separator()
            layout.label(text="Warning: No shell object!", icon="ERROR")
    
    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object")
            return {'CANCELLED'}
        
        # Get shell object from scene properties
        shell = getattr(context.scene, "spp_shell_object", None)
        if shell and isinstance(shell, str):
            shell = bpy.data.objects.get(shell)
        
        if not shell or shell.type != 'MESH':
            self.report({'WARNING'}, "No valid shell object found")
            return {'CANCELLED'}
        
        # Ensure object mode & active
        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        context.view_layer.objects.active = obj
        obj.select_set(True)
        
        # Add shrinkwrap modifier
        shrink_mod = obj.modifiers.new(name="Shrinkwrap_Shell", type='SHRINKWRAP')
        shrink_mod.target = shell
        shrink_mod.wrap_method = 'NEAREST_SURFACEPOINT'
        shrink_mod.wrap_mode = 'ON_SURFACE'
        shrink_mod.offset = 0.001
        
        # Apply the modifier if requested
        if self.apply_modifier:
            try:
                bpy.ops.object.modifier_apply(modifier=shrink_mod.name)
                self.report({'INFO'}, f"Applied shrinkwrap to '{shell.name}'")
            except Exception as e:
                self.report({'ERROR'}, f"Failed to apply shrinkwrap: {e}")
                return {'CANCELLED'}
        else:
            self.report({'INFO'}, f"Added shrinkwrap modifier targeting '{shell.name}'")
        
        return {'FINISHED'}


def register():
    bpy.utils.register_class(OBJECT_OT_apply_shrinkwrap)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_apply_shrinkwrap)


if __name__ == "__main__":
    register()
