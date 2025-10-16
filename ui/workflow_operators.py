import bpy


# Custom operator to toggle one workflow and close the other
class WM_OT_context_toggle_workflow(bpy.types.Operator):
    """Toggle a workflow property and close another workflow if needed"""

    bl_idname = "wm.context_toggle_workflow"
    bl_label = "Toggle Workflow"
    bl_options = {"INTERNAL"}

    toggle_prop: bpy.props.StringProperty(
        name="Toggle Property", description="The property to toggle"
    )

    other_prop: bpy.props.StringProperty(
        name="Other Property",
        description="The other property to set to False when this one is toggled on",
    )

    def execute(self, context):
        # Get the current value of the property to toggle
        current_value = getattr(context.scene, self.toggle_prop)

        # Toggle the property
        setattr(context.scene, self.toggle_prop, not current_value)

        # If we're turning this one on, turn the other one off
        if not current_value:  # We're toggling from False to True
            setattr(context.scene, self.other_prop, False)

        return {"FINISHED"}


class WM_OT_toggle_surface_step(bpy.types.Operator):
    """Toggle a Surface workflow step and collapse the others"""

    bl_idname = "wm.toggle_surface_step"
    bl_label = "Toggle Surface Step"
    bl_options = {"INTERNAL"}

    step: bpy.props.IntProperty(name="Step", default=1, min=1, max=4)

    def execute(self, context):
        wm = context.window_manager
        # Set the requested step to True and others to False
        for s in (1, 2, 3, 4):
            try:
                setattr(wm, f"spp_show_surface_step_{s}", s == self.step)
            except Exception:
                pass
        return {"FINISHED"}


# Registration
classes = [WM_OT_context_toggle_workflow, WM_OT_toggle_surface_step]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
