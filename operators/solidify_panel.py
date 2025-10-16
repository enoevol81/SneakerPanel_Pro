import bpy
from bpy.props import FloatProperty
from bpy.types import Operator


class OBJECT_OT_SolidifyPanel(Operator):
    bl_idname = "object.solidify_panel"
    bl_label = "Solidify Panel"
    bl_description = "Add solidify modifier to the selected panel"
    bl_options = {"REGISTER", "UNDO"}

    thickness: FloatProperty(
        name="Thickness",
        description="Thickness of the panel in meters",
        default=0.002,  # 2mm default thickness
        min=0.0001,
        max=1.0,
        step=0.001,
        precision=4,
        unit="LENGTH",
    )

    @classmethod
    def poll(cls, context):
        """Check if the operator can be executed.

        Args:
            context: Blender context

        Returns:
            bool: True if active object is a mesh
        """
        obj = context.active_object
        return obj is not None and obj.type == "MESH"

    def execute(self, context):
        """Execute the solidify operation.

        Args:
            context: Blender context

        Returns:
            set: {'FINISHED'} on success, {'CANCELLED'} on error
        """
        # Add undo checkpoint
        bpy.ops.ed.undo_push(message="Add Solidify Modifier")

        try:
            obj = context.active_object
            if not obj or obj.type != "MESH":
                self.report({"ERROR"}, "Please select a mesh object")
                return {"CANCELLED"}

            # Check if solidify modifier already exists
            solidify = obj.modifiers.get("Solidify")
            if solidify:
                self.report({"INFO"}, "Solidify modifier already exists")
                return {"CANCELLED"}

            # Create new solidify modifier with optimized settings
            solidify = obj.modifiers.new(name="Solidify", type="SOLIDIFY")

            # Pull initial values from UI scene properties when available
            scn = context.scene
            thickness_val = getattr(scn, "spp_solidify_thickness", self.thickness)
            offset_val = 1.0  # Always use positive 1 as default
            even_val = getattr(scn, "spp_solidify_even_thickness", True)
            rim_val = getattr(scn, "spp_solidify_rim", True)
            rim_only_val = getattr(scn, "spp_solidify_rim_only", False)

            solidify.thickness = thickness_val
            solidify.offset = offset_val
            solidify.use_even_offset = even_val
            solidify.use_rim = rim_val
            if hasattr(solidify, "use_rim_only"):
                solidify.use_rim_only = rim_only_val
            solidify.use_quality_normals = True  # Better normal calculation

            # Sync scene UI properties to reflect the new modifier's state
            if hasattr(scn, "spp_solidify_thickness"):
                scn.spp_solidify_thickness = solidify.thickness
            if hasattr(scn, "spp_solidify_offset"):
                scn.spp_solidify_offset = solidify.offset
            if hasattr(scn, "spp_solidify_even_thickness"):
                scn.spp_solidify_even_thickness = solidify.use_even_offset
            if hasattr(scn, "spp_solidify_rim"):
                scn.spp_solidify_rim = solidify.use_rim
            if hasattr(scn, "spp_solidify_rim_only"):
                scn.spp_solidify_rim_only = getattr(solidify, "use_rim_only", False)

            self.report(
                {"INFO"},
                f"Added solidify modifier with thickness: {self.thickness:.4f}m",
            )
            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"Error adding solidify modifier: {str(e)}")
            return {"CANCELLED"}


class OBJECT_OT_ApplySolidify(Operator):
    bl_idname = "object.apply_solidify"
    bl_label = "Apply Solidify"
    bl_description = "Apply the solidify modifier to make thickness permanent"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Check if the operator can be executed.

        Args:
            context: Blender context

        Returns:
            bool: True if active object is a mesh with a solidify modifier
        """
        obj = context.active_object
        return obj is not None and obj.type == "MESH" and "Solidify" in obj.modifiers

    def execute(self, context):
        """Execute the apply solidify operation.

        Args:
            context: Blender context

        Returns:
            set: {'FINISHED'} on success, {'CANCELLED'} on error
        """
        # Add undo checkpoint
        bpy.ops.ed.undo_push(message="Apply Solidify Modifier")

        try:
            obj = context.active_object
            solidify = obj.modifiers.get("Solidify")

            if not solidify:
                self.report({"ERROR"}, "No solidify modifier found")
                return {"CANCELLED"}

            # Apply the modifier
            bpy.ops.object.modifier_apply(modifier=solidify.name)
            self.report({"INFO"}, "Solidify modifier applied successfully")
            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"Error applying solidify modifier: {str(e)}")
            return {"CANCELLED"}


# Registration
classes = [OBJECT_OT_SolidifyPanel, OBJECT_OT_ApplySolidify]


def register():
    """Register the operators."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister the operators."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
