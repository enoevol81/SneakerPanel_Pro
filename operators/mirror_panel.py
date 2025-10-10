import bpy
from bpy.props import BoolProperty, EnumProperty
from bpy.types import Operator


class OBJECT_OT_mirror_panel(Operator):
    bl_idname = "mesh.mirror_panel"
    bl_label = "Mirror Panel"
    bl_description = (
        "Add a mirror modifier to the selected mesh object across the specified axis"
    )
    bl_options = {"REGISTER", "UNDO"}

    mirror_axis: EnumProperty(
        name="Mirror Axis",
        description="Choose the axis to mirror across",
        items=[
            ("X", "X-Axis", "Mirror across X-axis", "AXIS_SIDE", 0),
            ("Y", "Y-Axis", "Mirror across Y-axis", "AXIS_FRONT", 1),
            ("Z", "Z-Axis", "Mirror across Z-axis", "AXIS_TOP", 2),
        ],
        default="X",
    )

    apply_modifier: BoolProperty(
        name="Apply Modifier",
        description="Apply the mirror modifier immediately, or leave it as a modifier",
        default=True,
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "mirror_axis", expand=True)
        layout.separator()
        layout.prop(self, "apply_modifier")
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
        if not obj or obj.type != "MESH":
            self.report({"ERROR"}, "Please select a mesh object")
            return {"CANCELLED"}

        # fetch shell target
        shell = getattr(context.scene, "spp_shell_object", None)
        if shell and isinstance(shell, str):
            shell = bpy.data.objects.get(shell)

        # ensure object mode & active
        if obj.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        context.view_layer.objects.active = obj
        obj.select_set(True)

        # Apply all transforms before mirroring to ensure proper axes
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        # 1) add Mirror modifier
        mirror_mod = obj.modifiers.new(name="Mirror_Panel", type="MIRROR")
        # assign axes via vector property
        mirror_mod.use_axis = (
            self.mirror_axis == "X",
            self.mirror_axis == "Y",
            self.mirror_axis == "Z",
        )
        mirror_mod.use_mirror_merge = True
        mirror_mod.merge_threshold = 0.001

        # 2) add Shrinkwrap modifier (if shell)
        shrink_mod = None
        if shell and shell.type == "MESH":
            shrink_mod = obj.modifiers.new(name="Shrinkwrap_Shell", type="SHRINKWRAP")
            shrink_mod.target = shell
            shrink_mod.wrap_method = "NEAREST_SURFACEPOINT"
            shrink_mod.wrap_mode = "ON_SURFACE"
            shrink_mod.offset = 0.001

        # 3) apply modifiers in correct order (mirror first, then shrinkwrap) - only if requested
        if self.apply_modifier:
            to_apply = []
            to_apply.append(mirror_mod)  # Mirror first
            if shrink_mod:
                to_apply.append(shrink_mod)  # Shrinkwrap second

            for mod in to_apply:
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except Exception as e:
                    self.report({"WARNING"}, f"Failed to apply {mod.name}: {e}")

            self.report(
                {"INFO"},
                f"Applied mirror across {self.mirror_axis}-axis"
                + (f" and shrink-wrapped to '{shell.name}'" if shrink_mod else ""),
            )
        else:
            self.report(
                {"INFO"},
                f"Added mirror modifier across {self.mirror_axis}-axis"
                + (f" and shrinkwrap to '{shell.name}'" if shrink_mod else ""),
            )

        return {"FINISHED"}


def register():
    bpy.utils.register_class(OBJECT_OT_mirror_panel)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_mirror_panel)


if __name__ == "__main__":
    register()
