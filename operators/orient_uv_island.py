"""
Orients UV islands to make the toe point upward.

This operator rotates and scales the UV island of a mesh to make the toe area
point upward (in a upside-down V shape). It uses the toe marker to determine
the orientation and scales the UV to fit the entire width of the UV grid.
"""
import bpy
import bmesh
from bpy.types import Operator
from mathutils import Vector
import math

class OBJECT_OT_OrientUVIsland(Operator):
    """Orient UV island to make the toe point upward.
    
    This operator rotates the UV island of the active mesh so that the toe area
    (as defined by the Toe_Marker empty) points upward. It also scales the UV
    to fit the entire width of the UV grid with proper aspect ratio.
    
    Prerequisites:
    - The mesh must have UVs (unwrapped)
    - A Toe_Marker empty must exist (created with 'Define Toe' operator)
    """
    bl_idname = "object.orient_uv_island"
    bl_label = "Orient UV Island"
    bl_description = "Orient the UV island to make the toe point upward"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        """Check if the active object is a mesh with UVs."""
        obj = context.active_object
        return (obj and obj.type == 'MESH' and 
                obj.data.uv_layers.active is not None and
                bpy.data.objects.get("Toe_Marker") is not None)
    
    def execute(self, context):
        # Add undo checkpoint
        bpy.ops.ed.undo_push(message="Orient UV Island")
        
        # Get the active object
        obj = context.active_object
        marker_name = "Toe_Marker"
        marker = bpy.data.objects.get(marker_name)
        
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object")
            return {'CANCELLED'}
            
        if not marker:
            self.report({'ERROR'}, f"Toe marker '{marker_name}' not found. Please use 'Define Toe' first.")
            return {'CANCELLED'}
        
        # Store the current mode
        original_mode = obj.mode
        
        # Make sure we're in object mode for consistent mesh access
        if original_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        # Access mesh and UVs
        mesh = obj.data
        if not mesh.uv_layers:
            self.report({'ERROR'}, "No UVs found. Please unwrap first.")
            bpy.ops.object.mode_set(mode=original_mode)
            return {'CANCELLED'}

        uv_layer = mesh.uv_layers.active
        
        try:
            # Create a new bmesh to work with
            bm = bmesh.new()
            bm.from_mesh(mesh)
            uv_layer_bm = bm.loops.layers.uv.active

            # Map each vertex to its world coordinates
            world_coords = [(v.index, obj.matrix_world @ v.co) for v in bm.verts]
            marker_pos = marker.location

            # Find closest vertex to marker
            closest_index = min(world_coords, key=lambda x: (x[1] - marker_pos).length)[0]

            # Find average UV position for that vertex
            toe_uvs = []
            for face in bm.faces:
                for loop in face.loops:
                    if loop.vert.index == closest_index:
                        toe_uvs.append(loop[uv_layer_bm].uv.copy())

            if not toe_uvs:
                self.report({'ERROR'}, "Couldn't find UVs for closest vertex to toe marker.")
                bm.free()
                bpy.ops.object.mode_set(mode=original_mode)
                return {'CANCELLED'}

            # Average UV position of toe vertex
            toe_uv = sum(toe_uvs, Vector((0, 0))) / len(toe_uvs)

            # Get UV centroid of all UVs
            all_uvs = [loop[uv_layer_bm].uv.copy() for face in bm.faces for loop in face.loops]
            center = sum(all_uvs, Vector((0, 0))) / len(all_uvs)

            # Compute rotation angle to make toe point up
            vec = toe_uv - center
            angle = math.atan2(vec.y, vec.x)
            desired_angle = math.pi/2  # 90 degrees - pointing straight up
            rotation = desired_angle - angle

            cos_a = math.cos(rotation)
            sin_a = math.sin(rotation)

            # Apply rotation to all UVs
            for face in bm.faces:
                for loop in face.loops:
                    uv = loop[uv_layer_bm].uv
                    offset = uv - center
                    rotated = Vector((
                        offset.x * cos_a - offset.y * sin_a,
                        offset.x * sin_a + offset.y * cos_a
                    ))
                    loop[uv_layer_bm].uv = center + rotated
            
            # Recalculate bounds after rotation
            all_uvs = [loop[uv_layer_bm].uv.copy() for face in bm.faces for loop in face.loops]
            min_u = min(uv.x for uv in all_uvs)
            max_u = max(uv.x for uv in all_uvs)
            min_v = min(uv.y for uv in all_uvs)
            max_v = max(uv.y for uv in all_uvs)
            
            # Calculate current dimensions
            width = max_u - min_u
            height = max_v - min_v
            
            # Calculate the center of the UV island
            island_center = Vector(((min_u + max_u) / 2, (min_v + max_v) / 2))
            
            # Find the toe UV position after rotation
            toe_uvs_after_rotation = []
            for face in bm.faces:
                for loop in face.loops:
                    if loop.vert.index == closest_index:
                        toe_uvs_after_rotation.append(loop[uv_layer_bm].uv.copy())
            
            toe_uv_rotated = sum(toe_uvs_after_rotation, Vector((0, 0))) / len(toe_uvs_after_rotation)
            
            # Center the UV island at (0.5, 0.5) first
            center_target = Vector((0.5, 0.5))
            translation_to_center = center_target - island_center
            
            # Apply centering translation
            for face in bm.faces:
                for loop in face.loops:
                    loop[uv_layer_bm].uv += translation_to_center
            
            # Now maximize the scale to fill the UV space (similar to unwrap behavior)
            # Recalculate bounds after centering
            all_uvs_centered = [loop[uv_layer_bm].uv.copy() for face in bm.faces for loop in face.loops]
            min_u_centered = min(uv.x for uv in all_uvs_centered)
            max_u_centered = max(uv.x for uv in all_uvs_centered)
            min_v_centered = min(uv.y for uv in all_uvs_centered)
            max_v_centered = max(uv.y for uv in all_uvs_centered)
            
            # Calculate dimensions after centering
            centered_width = max_u_centered - min_u_centered
            centered_height = max_v_centered - min_v_centered
            
            # Calculate scale to maximize UV space usage (like unwrap does)
            # Use a very small margin to match unwrap behavior
            margin = 0.001  # Same small margin as unwrap operation
            max_scale = min(
                (1.0 - 2 * margin) / centered_width if centered_width > 0 else 1.0,
                (1.0 - 2 * margin) / centered_height if centered_height > 0 else 1.0
            )
            
            # Apply maximizing scale around the center (0.5, 0.5)
            for face in bm.faces:
                for loop in face.loops:
                    uv = loop[uv_layer_bm].uv
                    # Scale around center to maximize UV space usage
                    uv_from_center = uv - center_target
                    uv_scaled = uv_from_center * max_scale
                    loop[uv_layer_bm].uv = center_target + uv_scaled

            # Apply changes to the mesh
            bm.to_mesh(mesh)
            mesh.update()
            
            self.report({'INFO'}, "UV island oriented with toe at the top")
            
        except Exception as e:
            self.report({'ERROR'}, f"Error orienting UV island: {str(e)}")
            return {'CANCELLED'}
        finally:
            # Clean up bmesh
            if 'bm' in locals():
                bm.free()
            
            # Return to original mode
            bpy.ops.object.mode_set(mode=original_mode)
        
        return {'FINISHED'}

# Registration
classes = [OBJECT_OT_OrientUVIsland]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
