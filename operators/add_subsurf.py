import bpy
from bpy.types import Operator


class OBJECT_OT_add_subsurf(Operator):
    """Add a Subdivision Surface modifier to the active mesh (non-duplicating)"""
    bl_idname = "mesh.add_subsurf"
    bl_label = "Add Subdivision"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object")
            return {'CANCELLED'}

        original_mode = obj.mode
        try:
            # Ensure object mode to add modifiers
            if original_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            context.view_layer.objects.active = obj
            obj.select_set(True)

            # Check if a Subsurf modifier already exists
            existing = None
            for m in obj.modifiers:
                if m.type == 'SUBSURF':
                    existing = m
                    break
            if existing:
                self.report({'INFO'}, "Subdivision modifier already exists")
                return {'CANCELLED'}

            # Add new Subsurf modifier
            sub = obj.modifiers.new(name="Subdivision", type='SUBSURF')
            sub.levels = 2
            sub.render_levels = 2
            sub.subdivision_type = 'CATMULL_CLARK'

            self.report({'INFO'}, "Subdivision modifier added")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to add subdivision: {e}")
            return {'CANCELLED'}
        finally:
            # Restore original mode
            try:
                if original_mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode=original_mode)
            except Exception:
                pass


def register():
    bpy.utils.register_class(OBJECT_OT_add_subsurf)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_add_subsurf)


if __name__ == "__main__":
    register()
