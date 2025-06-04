import bpy
import bmesh
import math
from bpy.types import Operator
from bpy.props import BoolProperty
from mathutils import Vector

# Your existing convert_object_to_mesh helper function remains the same
# (Keep the convert_object_to_mesh function as is in your file)
def convert_object_to_mesh(obj, apply_modifiers=True, preserve_status=True):
    """Convert an object to a mesh, optionally applying modifiers"""
    original_active = None
    original_selected = []

    if preserve_status:
        original_active = bpy.context.view_layer.objects.active
        original_selected = [o for o in bpy.context.selected_objects]
        if bpy.context.mode != 'OBJECT': # Ensure object mode for selection operations
            bpy.ops.object.mode_set(mode='OBJECT')
        for o_sel in bpy.context.selected_objects:
            o_sel.select_set(False)
    
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.duplicate()
    new_obj = bpy.context.view_layer.objects.active
    
    if new_obj.type != 'MESH': 
        if apply_modifiers:
            bpy.ops.object.convert(target='MESH')
        else:
             bpy.ops.object.convert(target='MESH', keep_original=False) 
    elif apply_modifiers and new_obj.type == 'MESH': 
        # This case might be simplified; if it's already a mesh, 
        # applying modifiers directly (if any) or just using it might be enough.
        # However, object.convert can also apply modifiers.
        bpy.ops.object.convert(target='MESH')


    if preserve_status:
        if new_obj not in original_selected:
            new_obj.select_set(False)
        for o_sel in original_selected:
            if o_sel and o_sel.name in bpy.data.objects: 
                o_sel.select_set(True)
        if original_active and original_active.name in bpy.data.objects: 
            bpy.context.view_layer.objects.active = original_active
    
    return new_obj


class OBJECT_OT_UVToMesh(Operator):
    bl_idname = "object.uv_to_mesh"
    bl_label = "UV to Mesh"
    bl_description = "Create a new Mesh based on active UV from designated Shell Object, then isolate and frame it."
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
        name="Resize (Preserve Area)", 
        default=True,
        description="Scale the new object to preserve the average surface area from the Shell Object"
    )

    @classmethod
    def poll(cls, context):
        if hasattr(context.scene, 'spp_shell_object') and context.scene.spp_shell_object:
            return context.scene.spp_shell_object.type == 'MESH'
        return False

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
        
        if not source_object_from_scene.data.uv_layers or not source_object_from_scene.data.uv_layers.active:
            self.report({'ERROR'}, f"'{source_object_from_scene.name}' (Shell Object) has no active UV map.")
            return {'CANCELLED'}

        original_mode = context.mode
        if original_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        active_obj_backup = context.view_layer.objects.active
        selected_objs_backup = context.selected_objects[:]
        if selected_objs_backup: # Deselect all only if there's a selection
            bpy.ops.object.select_all(action='DESELECT')

        # ob0_for_conversion will be the duplicated and converted mesh
        ob0_for_conversion = convert_object_to_mesh(source_object_from_scene, 
                                          apply_modifiers=self.apply_modifiers, 
                                          preserve_status=False) 
        
        me0_from_conversion = ob0_for_conversion.data
        original_source_name = source_object_from_scene.name

        area_3d = 0
        bm = bmesh.new()
        polygons_to_process = me0_from_conversion.polygons

        if not polygons_to_process:
            self.report({'ERROR'}, f"No polygons in Shell Object '{original_source_name}'.")
            bpy.data.objects.remove(ob0_for_conversion)
            bpy.data.meshes.remove(me0_from_conversion)
            # (Restore selection and mode as in your original error handling)
            return {'CANCELLED'}

        active_uv_layer_data = me0_from_conversion.uv_layers.active.data
        uv_to_bm_vert_map = {}

        for face in polygons_to_process:
            area_3d += face.area
            face_bm_verts = []
            for loop_idx in face.loop_indices:
                uv = active_uv_layer_data[loop_idx].uv
                uv_key = (round(uv.x, 6), round(uv.y, 6))
                if uv_key not in uv_to_bm_vert_map:
                    new_bm_vert = bm.verts.new((uv.x, uv.y, 0.0))
                    uv_to_bm_vert_map[uv_key] = new_bm_vert
                face_bm_verts.append(uv_to_bm_vert_map[uv_key])
            if len(face_bm_verts) >= 3:
                try:
                    new_face = bm.faces.new(face_bm_verts)
                    if self.materials: 
                        new_face.material_index = face.material_index
                except ValueError: pass 

        if not bm.faces:
            self.report({'ERROR'}, "No valid UV faces generated. Check UV map.")
            bpy.data.objects.remove(ob0_for_conversion); bpy.data.meshes.remove(me0_from_conversion); bm.free()
            # (Restore selection and mode)
            return {'CANCELLED'}

        new_uv_mesh_name = original_source_name + '_UV_Mesh'
        me_uv = bpy.data.meshes.new(new_uv_mesh_name + '_data')
        ob_uv = bpy.data.objects.new(new_uv_mesh_name, me_uv)
        
        # Link to scene collection temporarily, will move to dedicated collection later
        context.collection.objects.link(ob_uv)

        bm.to_mesh(me_uv); bm.free(); me_uv.update()

        calculated_scale_factor = 1.0
        if self.auto_scale:
            area_uv_unscaled = sum(p.area for p in me_uv.polygons)
            if area_uv_unscaled > 1e-9:
                calculated_scale_factor = math.sqrt(area_3d / area_uv_unscaled)
                ob_uv.scale = Vector((calculated_scale_factor, calculated_scale_factor, 1.0))
                bpy.context.view_layer.objects.active = ob_uv
                ob_uv.select_set(True)
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                ob_uv.select_set(False) 
            elif area_3d > 1e-9:
                self.report({'WARNING'}, "UV mesh area is zero, cannot auto-scale.")
        
        ob_uv["spp_original_3d_mesh_name"] = original_source_name
        ob_uv["spp_applied_scale_factor"] = calculated_scale_factor
        if source_object_from_scene.data.uv_layers.active:
            ob_uv["spp_source_uv_map_name"] = source_object_from_scene.data.uv_layers.active.name

        if self.materials:
            ob_uv.data.materials.clear()
            for mat_slot in source_object_from_scene.material_slots:
                if mat_slot.material: ob_uv.data.materials.append(mat_slot.material)

        bpy.context.view_layer.objects.active = ob_uv
        ob_uv.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=1e-6)
        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.data.objects.remove(ob0_for_conversion); bpy.data.meshes.remove(me0_from_conversion)
        
        # Restore original selection (excluding the new ob_uv for now)
        for o_backup in selected_objs_backup:
            if o_backup and o_backup.name in bpy.data.objects and o_backup != ob_uv: 
                o_backup.select_set(True)
        if active_obj_backup and active_obj_backup.name in bpy.data.objects and active_obj_backup != ob_uv:
             context.view_layer.objects.active = active_obj_backup
        else: # If original active is gone or was the source, make the new UV mesh active
            context.view_layer.objects.active = ob_uv
        
        # Ensure the new UV mesh is selected and active at the end of core logic
        bpy.ops.object.select_all(action='DESELECT')
        ob_uv.select_set(True)
        context.view_layer.objects.active = ob_uv

        # --- NEW: Viewport, Collection, and Isolation Enhancements ---
        self.report({'INFO'}, "Configuring view and isolation for UV mesh.")

        # 1. Move to a dedicated collection
        spp_uv_collection_name = "SPP_UV_Patterns" # SneakerPanelPro UV Patterns
        spp_uv_collection = bpy.data.collections.get(spp_uv_collection_name)
        if not spp_uv_collection:
            spp_uv_collection = bpy.data.collections.new(spp_uv_collection_name)
            # Link it to the scene's master collection if it's not already a child
            if spp_uv_collection_name not in context.scene.collection.children:
                 context.scene.collection.children.link(spp_uv_collection)
        
        # Unlink from all current collections and link to the dedicated one
        current_collections = [col for col in ob_uv.users_collection]
        for col in current_collections:
            col.objects.unlink(ob_uv)
        if ob_uv.name not in spp_uv_collection.objects: # Avoid linking if already there (e.g. rerun)
            spp_uv_collection.objects.link(ob_uv)
        
        # 2. Set Top Orthographic View and Frame Selected
        area_3d = None
        region_3d_window = None
        for area_iter in context.screen.areas: # Renamed 'area' to 'area_iter' to avoid conflict
            if area_iter.type == 'VIEW_3D':
                area_3d = area_iter
                for region_iter in area_iter.regions: # Renamed 'region' to 'region_iter'
                    if region_iter.type == 'WINDOW':
                        # Find the largest window region if multiple exist (though usually one main one)
                        if region_3d_window is None or \
                           (region_iter.width * region_iter.height > region_3d_window.width * region_3d_window.height):
                            region_3d_window = region_iter
                break 
        
        if area_3d and region_3d_window:
            space_data = area_3d.spaces.active
            if space_data.type == 'VIEW_3D': # Ensure it's actually a 3D space
                space_data.region_3d.view_perspective = 'ORTHO'
                
                override_context = context.copy()
                override_context['area'] = area_3d
                override_context['region'] = region_3d_window
                # Some ops might need screen, window, scene as well if they are complex
                override_context['screen'] = context.screen
                override_context['window'] = context.window
                # override_context['scene'] = context.scene # Already in context.copy()

                with context.temp_override(**override_context):
                    bpy.ops.view3d.view_axis(type='TOP')
                    bpy.ops.view3d.view_selected(use_all_regions=False)
                
                # 3. Enter Local View for the new UV mesh
                # Ensure ob_uv is the only selected object
                bpy.ops.object.select_all(action='DESELECT') # Deselect all first
                ob_uv.select_set(True) # Select only our UV mesh
                context.view_layer.objects.active = ob_uv # Re-ensure active
                
                with context.temp_override(**override_context):
                    bpy.ops.view3d.localview()
                self.report({'INFO'}, "Switched to Top Ortho, framed selection, and entered Local View.")
            else:
                self.report({'WARNING'}, "Active space in 3D View area is not of type 'VIEW_3D'.")
        else:
            self.report({'WARNING'}, "Could not find suitable 3D View area/region to set view.")
        # --- END OF NEW ENHANCEMENTS ---

        if original_mode != 'OBJECT' and context.view_layer.objects.active.mode != original_mode:
             # Attempt to restore original mode if it makes sense and object supports it
            try:
                if context.view_layer.objects.active.type == 'MESH': # Only for mesh objects usually
                    bpy.ops.object.mode_set(mode=original_mode)
            except RuntimeError:
                 self.report({'WARNING'}, f"Could not restore original mode '{original_mode}'.")


        self.report({'INFO'}, f"Created and isolated UV Mesh: {ob_uv.name} from Shell: {original_source_name}")
        return {'FINISHED'}

classes = [OBJECT_OT_UVToMesh]        

def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
            print(f"Successfully registered class: {cls.__name__} with id: {cls.bl_idname}") # Added print
        except Exception as e:
            print(f"ERROR registering class {cls.__name__}: {e}") # Report error
            # Optionally, re-raise the exception if you want registration to halt addon enabling
            # raise e 

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
            print(f"Successfully unregistered class: {cls.__name__}") # Added print
        except RuntimeError as e: # Catch the specific error you're seeing
            print(f"ERROR unregistering class {cls.__name__} (likely was not properly registered): {e}")
        except Exception as e:
            print(f"UNEXPECTED ERROR unregistering class {cls.__name__}: {e}")
