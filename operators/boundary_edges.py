import bpy
import bmesh
from bpy.types import Operator


class MESH_OT_select_boundary_edges(Operator):
    """Select only boundary edges (edges with fewer than 2 linked faces)"""
    bl_idname = "mesh.select_boundary_edges"
    bl_label = "Select Boundary Edges"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object")
            return {'CANCELLED'}

        original_mode = obj.mode
        try:
            if original_mode != 'EDIT':
                bpy.ops.object.mode_set(mode='EDIT')

            # Ensure edge select mode
            try:
                context.tool_settings.mesh_select_mode = (False, True, False)
            except Exception:
                pass

            me = obj.data
            bm = bmesh.from_edit_mesh(me)

            # Deselect everything first, then select only boundary edges
            for e in bm.edges:
                e.select = False
            for e in bm.edges:
                if len(e.link_faces) < 2:
                    e.select = True

            bmesh.update_edit_mesh(me, loop_triangles=False, destructive=False)

            self.report({'INFO'}, "Boundary edges selected")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to select boundary edges: {e}")
            return {'CANCELLED'}
        finally:
            if original_mode != 'EDIT':
                try:
                    bpy.ops.object.mode_set(mode=original_mode)
                except Exception:
                    pass

        return {'FINISHED'}


class MESH_OT_deselect_boundary_edges(Operator):
    """Deselect boundary edges, keeping interior edges selected"""
    bl_idname = "mesh.deselect_boundary_edges"
    bl_label = "Deselect Boundary Edges"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object")
            return {'CANCELLED'}

        original_mode = obj.mode
        try:
            if original_mode != 'EDIT':
                bpy.ops.object.mode_set(mode='EDIT')

            # Ensure edge select mode
            try:
                context.tool_settings.mesh_select_mode = (False, True, False)
            except Exception:
                pass

            me = obj.data
            bm = bmesh.from_edit_mesh(me)

            # Only deselect boundary edges
            any_changed = False
            for e in bm.edges:
                if len(e.link_faces) < 2 and e.select:
                    e.select = False
                    any_changed = True

            bmesh.update_edit_mesh(me, loop_triangles=False, destructive=False)

            if any_changed:
                self.report({'INFO'}, "Boundary edges deselected")
            else:
                self.report({'INFO'}, "No boundary edges were selected")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to deselect boundary edges: {e}")
            return {'CANCELLED'}
        finally:
            if original_mode != 'EDIT':
                try:
                    bpy.ops.object.mode_set(mode=original_mode)
                except Exception:
                    pass

        return {'FINISHED'}


def register():
    bpy.utils.register_class(MESH_OT_select_boundary_edges)
    bpy.utils.register_class(MESH_OT_deselect_boundary_edges)


def unregister():
    bpy.utils.unregister_class(MESH_OT_deselect_boundary_edges)
    bpy.utils.unregister_class(MESH_OT_select_boundary_edges)


if __name__ == "__main__":
    register()
