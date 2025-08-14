import math

import bmesh
import bpy
import mathutils


def hermite_3d(p1, p2, p3, p4, mu, tension, bias):
    def h1d(y0, y1, y2, y3, mu):
        mu2 = mu * mu
        mu3 = mu2 * mu
        m0 = (y1 - y0) * (1 - tension) * 0.5 + (y2 - y1) * (1 - tension) * 0.5
        m1 = (y2 - y1) * (1 - tension) * 0.5 + (y3 - y2) * (1 - tension) * 0.5
        a0 = 2 * mu3 - 3 * mu2 + 1
        a1 = mu3 - 2 * mu2 + mu
        a2 = mu3 - mu2
        a3 = -2 * mu3 + 3 * mu2
        return a0 * y1 + a1 * m0 + a2 * m1 + a3 * y2

    x = h1d(p1.x, p2.x, p3.x, p4.x, mu)
    y = h1d(p1.y, p2.y, p3.y, p4.y, mu)
    z = h1d(p1.z, p2.z, p3.z, p4.z, mu)
    return mathutils.Vector((x, y, z))


def blend_position(original, target, blend_factor):
    return original.lerp(target, blend_factor)


def is_boundary_vert(vert):
    return any(e.is_boundary for e in vert.link_edges)


class OBJECT_OT_set_edge_flow(bpy.types.Operator):
    bl_idname = "mesh.set_edge_flow"
    bl_label = "Set Edge Flow"
    bl_options = {"REGISTER", "UNDO"}

    tension: bpy.props.FloatProperty(name="Tension", default=1.8, min=0.0, max=10.0)
    iterations: bpy.props.IntProperty(name="Iterations", default=8, min=1, max=32)
    blend_zone: bpy.props.IntProperty(name="Blend Zone", default=2, min=0, max=10)

    def execute(self, context):
        obj = context.edit_object
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()

        selected_edges = [e for e in bm.edges if e.select and not e.is_boundary]
        if not selected_edges:
            self.report({"WARNING"}, "No valid edges selected")
            return {"CANCELLED"}

        original_positions = {
            v.index: v.co.copy() for e in selected_edges for v in e.verts
        }

        for _ in range(self.iterations):
            updated_positions = {}

            for edge in selected_edges:
                for loop in edge.link_loops:
                    if not loop.face or len(loop.face.verts) != 4:
                        continue
                    try:
                        ring1 = loop.link_loop_next.link_loop_next
                        ring2 = loop.link_loop_radial_prev.link_loop_prev.link_loop_prev
                        center = edge.other_vert(loop.vert)
                        if is_boundary_vert(center):
                            continue
                        p2 = ring1.vert.co
                        p3 = ring2.link_loop_radial_next.vert.co
                        p1 = p2 - (p3 - p2)
                        p4 = p3 - (p2 - p3)
                        new_pos = hermite_3d(p1, p2, p3, p4, 0.5, -self.tension, 0)
                        updated_positions[center.index] = new_pos
                    except:
                        continue

            for vidx, new_co in updated_positions.items():
                bm.verts[vidx].co = new_co

        # Apply blending near boundaries
        for edge in selected_edges:
            loop_verts = list(
                dict.fromkeys([v for e in selected_edges for v in e.verts])
            )
            if len(loop_verts) < 2:
                continue

            for i, v in enumerate(loop_verts):
                if i < self.blend_zone:
                    blend = i / self.blend_zone
                    bm.verts[v.index].co = blend_position(
                        original_positions[v.index], v.co, blend
                    )
                elif i >= len(loop_verts) - self.blend_zone:
                    blend = (len(loop_verts) - i - 1) / self.blend_zone
                    bm.verts[v.index].co = blend_position(
                        original_positions[v.index], v.co, blend
                    )

        bmesh.update_edit_mesh(obj.data, loop_triangles=True)
        self.report({"INFO"}, f"Edge Flow applied with {self.iterations} iterations")
        return {"FINISHED"}


def register():
    bpy.utils.register_class(OBJECT_OT_set_edge_flow)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_set_edge_flow)


if __name__ == "__main__":
    register()
