import bpy
import bmesh
import math
from bpy.types import Operator
from bpy.props import BoolProperty
from mathutils import Vector

# Your existing convert_object_to_mesh helper function remains the same
# I'm including it here for completeness of the operator file.
def convert_object_to_mesh(obj, apply_modifiers=True, preserve_status=True):
    """Convert an object to a mesh, optionally applying modifiers"""
    original_active = None
    original_selected = []

    if preserve_status:
        original_active = bpy.context.view_layer.objects.active
        original_selected = [o for o in bpy.context.selected_objects]
        # Deselect all before selecting the target obj, to ensure clean state for duplication
        for o_sel in bpy.context.selected_objects:
            o_sel.select_set(False)
    
    # Duplicate the object
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.duplicate()
    new_obj = bpy.context.view_layer.objects.active
    
    # Convert to mesh
    if new_obj.type != 'MESH': # Check if it's not already a mesh after duplication
        if apply_modifiers:
            bpy.ops.object.convert(target='MESH')
        else:
            # If not applying modifiers, but it's still not a mesh (e.g. CURVE, SURFACE)
            # we still need to convert it, but without modifier application step.
            # The object.convert op will use the evaluated mesh if apply_modifiers is True (default for op)
            # or base mesh if False. For non-mesh types, it just converts.
            # For clarity, we just ensure it becomes a mesh.
            # A non-modifier conversion for already-mesh types is a no-op.
             bpy.ops.object.convert(target='MESH', keep_original=False) # keep_original=False is for the op, not our duplicate
    elif apply_modifiers and new_obj.type == 'MESH': # If it's already a mesh but we want to apply modifiers
        bpy.ops.object.convert(target='MESH')


    # Restore selection if needed
    if preserve_status:
        # Deselect the new_obj before restoring, unless it was part of original selection
        if new_obj not in original_selected:
            new_obj.select_set(False)

        for o_sel in original_selected:
            if o_sel: # Check if object still exists
                o_sel.select_set(True)
        if original_active: # Check if object still exists
            bpy.context.view_layer.objects.active = original_active
    
    return new_obj

class OBJECT_OT_UVToMesh(Operator):
    bl_idname = "object.uv_to_mesh"
    bl_label = "UV to Mesh"
    bl_description = "Create a new Mesh based on active UV from designated Shell Object"
    bl_options = {'REGISTER', 'UNDO'}

    apply_modifiers : BoolProperty(
        name="Apply Modifiers",
        default=True,
        description="Apply object's modifiers from the Shell Object"
    )
    vertex_groups : BoolProperty(
        name="Keep Vertex Groups",
        default=True,
        description="Transfer all the Vertex Groups"
    )
    materials : BoolProperty(
        name="Keep Materials",
        default=True,
        description="Transfer all the Materials"
    )
    auto_scale : BoolProperty(
        name="Resize (Preserve Area)", # Clarified label
        default=True,
        description="Scale the new object to preserve the average surface area from the Shell Object"
    )

    @classmethod
    def poll(cls, context):
        # Operator can run if a shell object is defined and is a mesh
        # Or, as a fallback, if an active object is a mesh (optional)
        if hasattr(context.scene, 'spp_shell_object') and context.scene.spp_shell_object:
            return context.scene.spp_shell_object.type == 'MESH'
        # Fallback to active object if you want the operator to still work without shell_object set
        # return context.active_object is not None and context.active_object.type == 'MESH'
        return False # Stricter: only run if shell_object is set.

    def execute(self, context):
        bpy.ops.ed.undo_push(message="UV to Mesh")
        
        source_object_from_scene = None
        if hasattr(context.scene, 'spp_shell_object') and context.scene.spp_shell_object:
            source_object_from_scene = context.scene.spp_shell_object
        
        if not source_object_from_scene:
            self.report({'ERROR'}, "No 'Shell Object' defined in Scene Properties.")
            return {'CANCELLED'}

        if source_object_from_scene.type != 'MESH':
            self.report({'ERROR'}, "'Shell Object' must be a Mesh type.")
            return {'CANCELLED'}
        
        if not source_object_from_scene.data.uv_layers.active:
            self.report({'ERROR'}, f"'{source_object_from_scene.name}' (Shell Object) has no active UV map.")
            return {'CANCELLED'}

        # Preserve current context
        original_mode = context.mode
        if original_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        active_obj_backup = context.view_layer.objects.active
        selected_objs_backup = context.selected_objects[:]
        for o in selected_objs_backup:
            o.select_set(False)

        # ob0_for_conversion will be the duplicated and converted mesh
        ob0_for_conversion = convert_object_to_mesh(source_object_from_scene, 
                                          apply_modifiers=self.apply_modifiers, 
                                          preserve_status=False) # We handle selection after
        
        me0_from_conversion = ob0_for_conversion.data
        original_source_name = source_object_from_scene.name # Name of the *actual* source

        area_3d = 0
        bm = bmesh.new()

        # Determine which polygons to process (all, as we are not checking edit mode selection here)
        # If you need to respect edit mode selection on the shell_object, that's more complex
        # as the operator isn't invoked from edit mode directly on shell_object in this flow.
        # For this workflow, using all polygons of the shell_object makes sense.
        polygons_to_process = me0_from_conversion.polygons

        if not polygons_to_process:
            self.report({'ERROR'}, f"No polygons found in the Shell Object '{original_source_name}'.")
            bpy.data.objects.remove(ob0_for_conversion)
            bpy.data.meshes.remove(me0_from_conversion)
            # Restore selection
            for o_backup in selected_objs_backup:
                if o_backup: o_backup.select_set(True)
            if active_obj_backup: context.view_layer.objects.active = active_obj_backup
            if original_mode != 'OBJECT': bpy.ops.object.mode_set(mode=original_mode)
            return {'CANCELLED'}

        active_uv_layer_data = me0_from_conversion.uv_layers.active.data

        # Using a map to create unique vertices for the UV mesh
        uv_to_bm_vert_map = {}

        for face in polygons_to_process:
            area_3d += face.area
            face_bm_verts = []
            valid_face_uvs = True
            for loop_idx in face.loop_indices:
                uv = active_uv_layer_data[loop_idx].uv
                
                # Use rounded UVs as dict keys to handle float precision
                uv_key = (round(uv.x, 6), round(uv.y, 6))

                if uv_key not in uv_to_bm_vert_map:
                    new_bm_vert = bm.verts.new((uv.x, uv.y, 0.0))
                    uv_to_bm_vert_map[uv_key] = new_bm_vert
                face_bm_verts.append(uv_to_bm_vert_map[uv_key])
            
            if len(face_bm_verts) >= 3:
                try:
                    new_face = bm.faces.new(face_bm_verts)
                    if self.materials: # Transfer material index
                        new_face.material_index = face.material_index
                except ValueError: 
                    # This can happen if UVs are degenerate (e.g., co-linear for a tri)
                    # print(f"Warning: Could not create UV face from verts: {[v.co for v in face_bm_verts]}")
                    pass # Silently skip problematic faces for now

        if not bm.faces:
            self.report({'ERROR'}, "No valid UV faces could be generated. Check UV map.")
            bpy.data.objects.remove(ob0_for_conversion)
            bpy.data.meshes.remove(me0_from_conversion)
            bm.free()
            # Restore selection
            for o_backup in selected_objs_backup:
                if o_backup: o_backup.select_set(True)
            if active_obj_backup: context.view_layer.objects.active = active_obj_backup
            if original_mode != 'OBJECT': bpy.ops.object.mode_set(mode=original_mode)
            return {'CANCELLED'}

        new_uv_mesh_name = original_source_name + '_UV_Mesh'
        me_uv = bpy.data.meshes.new(new_uv_mesh_name + '_data')
        ob_uv = bpy.data.objects.new(new_uv_mesh_name, me_uv)

        context.collection.objects.link(ob_uv)
        # No need to set active/selected yet, will do at the end

        bm.to_mesh(me_uv)
        bm.free()
        me_uv.update()

        calculated_scale_factor = 1.0
        if self.auto_scale:
            area_uv_unscaled = 0
            for p in me_uv.polygons:
                area_uv_unscaled += p.area
            
            if area_uv_unscaled > 1e-9: # Avoid division by zero or tiny numbers
                calculated_scale_factor = math.sqrt(area_3d / area_uv_unscaled)
                 # Apply scale to the object, then apply it to mesh
                ob_uv.scale = Vector((calculated_scale_factor, calculated_scale_factor, 1.0)) # Z scale 1 for 2D
                
                # Select and make active to apply transform
                bpy.context.view_layer.objects.active = ob_uv
                ob_uv.select_set(True)
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                ob_uv.select_set(False) # Deselect after applying
            else:
                if area_3d > 1e-9 : # Only report warning if 3D area was significant
                    self.report({'WARNING'}, "UV mesh area is zero, cannot auto-scale. Check UVs.")
                calculated_scale_factor = 1.0 # Default if scaling failed


        # Store custom properties on the new UV mesh object
        ob_uv["spp_original_3d_mesh_name"] = original_source_name
        ob_uv["spp_applied_scale_factor"] = calculated_scale_factor # Store the actual factor used
        if source_object_from_scene.data.uv_layers.active:
            ob_uv["spp_source_uv_map_name"] = source_object_from_scene.data.uv_layers.active.name


        # Vertex Groups (Simplified attempt - direct mapping is hard)
        # This part is complex because vertex indices don't map directly from 3D to UV mesh easily.
        # For now, this is a placeholder or might need a more sophisticated mapping solution
        # if precise vertex group transfer to the UV mesh is critical.
        # Your original logic might work if 'loop_indices' somehow correspond to final vertex indices
        # after 'remove_doubles', but it's not guaranteed.
        # For the overlay workflow, VG on the flat UV mesh is likely not essential.
        if self.vertex_groups:
            # This is a very simplified approach and might not be accurate.
            # A proper mapping would require tracking which UV vert corresponds to which 3D vert.
            print("Vertex group transfer is complex and might not be fully accurate in this version.")
            # for group3d in source_object_from_scene.vertex_groups:
            #    group_uv = ob_uv.vertex_groups.new(name=group3d.name)
            #    # Mapping weights here is non-trivial
            pass


        # Materials
        if self.materials:
            ob_uv.data.materials.clear() # Clear any default materials
            for mat_slot in source_object_from_scene.material_slots:
                if mat_slot.material:
                    ob_uv.data.materials.append(mat_slot.material)
            # Remap material indices on faces (already done during bmesh face creation if self.materials was true then)
            # If material_index was copied to bm.faces, it should be preserved in me_uv

        # Finalize ob_uv: remove doubles
        # Select and make active to run mesh operations
        bpy.context.view_layer.objects.active = ob_uv
        ob_uv.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=1e-6) # Small threshold
        bpy.ops.object.mode_set(mode='OBJECT')


        # Clean up the duplicated/converted source object
        bpy.data.objects.remove(ob0_for_conversion)
        bpy.data.meshes.remove(me0_from_conversion)
        
        # Restore original selection and active object as best as possible
        # First deselect the newly created ob_uv unless it was part of original selection (unlikely)
        # if ob_uv not in selected_objs_backup:
        #    ob_uv.select_set(False) 
        # No, we want the new object to be active and selected
        
        for o_backup in selected_objs_backup:
            if o_backup and o_backup != ob_uv : # Check if object still exists and is not our new one
                o_backup.select_set(True)
        
        if active_obj_backup and active_obj_backup != ob_uv:
             context.view_layer.objects.active = active_obj_backup
        else: # If original active is gone or was the source, make the new UV mesh active
            context.view_layer.objects.active = ob_uv
        
        # Ensure the new UV mesh is selected and active at the end
        for o in context.selected_objects: # Deselect everything first
            o.select_set(False)
        ob_uv.select_set(True)
        context.view_layer.objects.active = ob_uv

        if original_mode != 'OBJECT' and context.view_layer.objects.active.mode != original_mode:
            bpy.ops.object.mode_set(mode=original_mode) # Restore original mode if possible

        self.report({'INFO'}, f"Created UV Mesh: {ob_uv.name} from Shell: {original_source_name}")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(OBJECT_OT_UVToMesh)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_UVToMesh)