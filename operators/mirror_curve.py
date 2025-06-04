# File: SneakerPanel_Pro/operators/mirror_curve.py

import bpy
from bpy.props import BoolProperty, FloatProperty, EnumProperty
from bpy.types import Operator

class CURVE_OT_MirrorWithModifierAtCursor(Operator):
    """Mirror the selected curve object using a Mirror Modifier centered at the 3D cursor"""
    bl_idname = "curve.mirror_at_cursor"
    bl_label = "Mirror Curve At Cursor"
    bl_options = {'REGISTER', 'UNDO'}

    mirror_axis_items = [
        ('X', "X Axis", "Mirror across the X axis of the cursor/object origin"),
        ('Y', "Y Axis", "Mirror across the Y axis of the cursor/object origin"),
        ('Z', "Z Axis", "Mirror across the Z axis of the cursor/object origin"),
    ]
    # Using individual bools for axes as Mirror modifier supports multiple
    use_x: BoolProperty(name="Mirror X", default=True, description="Mirror across the X axis")
    use_y: BoolProperty(name="Mirror Y", default=False, description="Mirror across the Y axis")
    use_z: BoolProperty(name="Mirror Z", default=False, description="Mirror across the Z axis")

    apply_modifier: BoolProperty(
        name="Apply Modifier",
        default=True,
        description="Apply the Mirror modifier to make geometry real"
    )
    delete_mirror_empty: BoolProperty(
        name="Delete Helper Empty",
        default=True,
        description="Delete the temporary Empty used as mirror center (if modifier is applied)"
    )
    merge_threshold: FloatProperty(
        name="Merge Threshold",
        default=0.001,
        min=0.0,
        description="Vertices within this distance will be merged"
    )
    use_clip: BoolProperty(
        name="Use Clip",
        default=False,
        description="Prevent vertices from crossing the mirror plane"
    )

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'CURVE'

    
    def execute(self, context):
        if not context.active_object or context.active_object.type != 'CURVE':
            self.report({'ERROR'}, "Active object is not a Curve.")
            return {'CANCELLED'}

        curve_obj = context.active_object
        cursor_loc = context.scene.cursor.location.copy()
        
        original_active = context.view_layer.objects.active # Store for potential restore
        original_selected_objects = context.selected_objects[:] # Store for potential restore

        # --- 1. Create a temporary Empty at the 3D cursor ---
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=cursor_loc, scale=(1, 1, 1))
        mirror_empty = context.active_object
        mirror_empty.name = f"{curve_obj.name}_MirrorCenter_Temp" # Unique name
        self.report({'INFO'}, f"Created temporary mirror Empty: {mirror_empty.name}")

        # --- 2. Add and configure Mirror Modifier to the curve object ---
        bpy.ops.object.select_all(action='DESELECT')
        curve_obj.select_set(True)
        context.view_layer.objects.active = curve_obj

        mod_name = "SPP_CursorMirror" # Consistent name for the modifier
        
        existing_mod = curve_obj.modifiers.get(mod_name)
        if existing_mod:
            self.report({'INFO'}, f"Removing existing modifier: {mod_name} before adding new configuration.")
            curve_obj.modifiers.remove(existing_mod)

        mod = curve_obj.modifiers.new(name=mod_name, type='MIRROR')
        mod.mirror_object = mirror_empty
        mod.use_axis[0] = self.use_x
        mod.use_axis[1] = self.use_y
        mod.use_axis[2] = self.use_z
        mod.use_clip = self.use_clip
        mod.merge_threshold = self.merge_threshold
        
        self.report({'INFO'}, f"Added Mirror modifier to '{curve_obj.name}'. Axes: X={self.use_x}, Y={self.use_y}, Z={self.use_z}")

        # --- 3. Optionally apply the modifier ---
        if self.apply_modifier:
            self.report({'INFO'}, "Attempting to apply Mirror modifier...")
            
            # Store modifier name, as curve_obj reference might change if 'convert' creates a new object
            # though it usually converts in-place.
            
            try:
                if curve_obj.mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode='OBJECT')

                # IMPORTANT: Convert the curve to a mesh BEFORE applying the mirror modifier
                self.report({'INFO'}, f"Converting '{curve_obj.name}' to Mesh to apply Mirror modifier.")
                
                # Select only the curve object for conversion
                bpy.ops.object.select_all(action='DESELECT')
                curve_obj.select_set(True)
                context.view_layer.objects.active = curve_obj
                
                bpy.ops.object.convert(target='MESH')
                # curve_obj is now a MESH object. The modifier is still on it.
                # The variable curve_obj now refers to this mesh object.
                
                self.report({'INFO'}, f"'{curve_obj.name}' is now a Mesh. Applying modifier '{mod_name}'.")

                # Ensure the modifier still exists by that name on the (now) mesh object
                modifier_on_mesh = curve_obj.modifiers.get(mod_name)
                if not modifier_on_mesh:
                    # This case should be rare if convert() preserves modifiers
                    self.report({'ERROR'}, f"Modifier '{mod_name}' not found on '{curve_obj.name}' after conversion to mesh. Cannot apply.")
                    if self.delete_mirror_empty:
                        empty_to_delete = bpy.data.objects.get(mirror_empty.name)
                        if empty_to_delete: bpy.data.objects.remove(empty_to_delete, do_unlink=True)
                    return {'CANCELLED'}

                bpy.ops.object.modifier_apply(modifier=modifier_on_mesh.name) # Apply to the mesh
                self.report({'INFO'}, f"Successfully applied Mirror modifier to '{curve_obj.name}' (now a Mesh).")
                
                if self.delete_mirror_empty:
                    empty_to_delete = bpy.data.objects.get(mirror_empty.name)
                    if empty_to_delete:
                        bpy.data.objects.remove(empty_to_delete, do_unlink=True)
                        self.report({'INFO'}, "Deleted temporary mirror Empty.")
                    # else: self.report({'WARNING'}, f"Mirror Empty '{mirror_empty.name}' not found for deletion.") already handled

            except RuntimeError as e:
                self.report({'ERROR'}, f"Failed during apply Mirror process for '{curve_obj.name}': {e}. Check if object was already a mesh or if conversion failed.")
                # Cleanup partially added modifier or empty
                if mod_name in curve_obj.modifiers: # Check on the current curve_obj reference
                    curve_obj.modifiers.remove(curve_obj.modifiers[mod_name])
                empty_to_delete = bpy.data.objects.get(mirror_empty.name)
                if empty_to_delete:
                    bpy.data.objects.remove(empty_to_delete, do_unlink=True)
                return {'CANCELLED'}
        else:
            self.report({'INFO'}, "Mirror modifier left live on Curve object. Helper Empty retained.")
            # If not applying, and user wants to keep empty, maybe parent it for organization.
            # if not self.delete_mirror_empty: # This logic needs refinement based on desired default
            #    mirror_empty.parent = curve_obj
            #    mirror_empty.matrix_parent_inverse = curve_obj.matrix_world.inverted()


        # Ensure the (potentially modified or type-changed) curve_obj remains selected and active
        bpy.ops.object.select_all(action='DESELECT')
        curve_obj.select_set(True)
        context.view_layer.objects.active = curve_obj

        return {'FINISHED'}

def register():
    bpy.utils.register_class(CURVE_OT_MirrorWithModifierAtCursor)

def unregister():
    bpy.utils.unregister_class(CURVE_OT_MirrorWithModifierAtCursor)

if __name__ == "__main__":
    register()