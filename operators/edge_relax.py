import bpy
from bpy.types import Operator


class MESH_OT_edge_relax(Operator):
    bl_idname = "mesh.edge_relax"
    bl_label = "Edge Relax"
    bl_description = "Relax selected edge loops via LoopTools Relax tool"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        # Forward to LoopTools Relax (requires LoopTools addon enabled)
        return bpy.ops.mesh.looptools_relax("INVOKE_DEFAULT")

    def execute(self, context):
        # Fallback if called via execute
        return self.invoke(context, None)


def register():
    bpy.utils.register_class(MESH_OT_edge_relax)


def unregister():
    bpy.utils.unregister_class(MESH_OT_edge_relax)


if __name__ == "__main__":
    register()
