import bmesh
import bpy


def lerp(v0, v1, t):
    return v0.lerp(v1, t)


class MESH_OT_set_edge_linear(bpy.types.Operator):

    bl_idname = "mesh.set_edge_linear"
    bl_label = "Set Edge Linear"
    bl_description = "Straighten selected edges by placing vertices along a straight line between endpoints"
    bl_options = {"REGISTER", "UNDO"}

    space_evenly: bpy.props.BoolProperty(
        name="Space Evenly",
        description="Place vertices at equal intervals along the straight line",
        default=False,
    )
    blend_zone: bpy.props.IntProperty(
        name="Blend Zone",
        description="Number of vertices at each end to blend back toward original",
        default=2,
        min=0,
        max=64,
    )

    @classmethod
    def poll(cls, context):
        obj = context.edit_object
        return obj is not None and obj.type == "MESH" and context.mode == "EDIT_MESH"

    def execute(self, context):
        obj = context.edit_object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()

        # Build adjacency for the SELECTED edges only
        sel_edges = [e for e in bm.edges if e.select]
        if not sel_edges:
            self.report({"WARNING"}, "No selected edges")
            return {"CANCELLED"}

        adj = {}  # vid -> set(vid)
        sel_verts = set()
        for e in sel_edges:
            v0, v1 = e.verts[0].index, e.verts[1].index
            adj.setdefault(v0, set()).add(v1)
            adj.setdefault(v1, set()).add(v0)
            sel_verts.add(v0)
            sel_verts.add(v1)

        # Save originals for blending
        original_pos = {vid: bm.verts[vid].co.copy() for vid in sel_verts}

        # Find endpoints (degree == 1) among selected graph
        endpoints = [vid for vid, nbrs in adj.items() if len(nbrs) == 1]
        visited = set()

        def walk_path(start):

            path = [start]
            visited.add(start)
            prev = None
            cur = start
            while True:
                nbrs = [n for n in adj.get(cur, []) if n != prev]
                # choose the next unvisited neighbor if possible
                nxt = None
                for n in nbrs:
                    if n not in visited:
                        nxt = n
                        break
                if nxt is None:
                    # Either dead end or already visited; stop.
                    break
                path.append(nxt)
                visited.add(nxt)
                prev, cur = cur, nxt
            return path

        paths = []
        # First, extract all maximal open paths starting at endpoints
        for ep in endpoints:
            if ep in visited:
                continue
            p = walk_path(ep)
            if len(p) >= 2 and len(adj.get(p[-1], [])) == 1:
                paths.append(p)

        # If nothing found, selection is likely all loops/branches; bail gracefully
        if not paths:
            self.report(
                {"WARNING"},
                "No open edge paths found (closed loops or branched selections are ignored)",
            )
            return {"CANCELLED"}

        straightened = 0

        for path in paths:
            # Coordinates in order
            coords = [bm.verts[vid].co.copy() for vid in path]
            if len(coords) < 2:
                continue

            start = coords[0]
            end = coords[-1]
            line = end - start
            L = line.length
            if L <= 1e-12:
                # Degenerate path; skip
                continue

            # Compute straight positions
            if self.space_evenly:
                count = len(coords) - 1
                for i, vid in enumerate(path):
                    t = (i / count) if count > 0 else 0.0
                    bm.verts[vid].co = start + t * line
            else:
                # Preserve relative arclength along the original polyline
                cum = [0.0]
                for i in range(1, len(coords)):
                    cum.append(cum[-1] + (coords[i] - coords[i - 1]).length)
                total = cum[-1]
                if total <= 1e-12:
                    # Fallback to even spacing
                    count = len(coords) - 1
                    for i, vid in enumerate(path):
                        t = (i / count) if count > 0 else 0.0
                        bm.verts[vid].co = start + t * line
                else:
                    for vid, s in zip(path, cum):
                        t = s / total
                        bm.verts[vid].co = start + t * line

            # Blend ends back toward original, similar spirit to your edge_flow
            bz = max(0, min(self.blend_zone, len(path) // 2))
            if bz > 0:
                n = len(path)
                for i in range(bz):  # head
                    vid = path[i]
                    w = i / bz  # 0..(bz-1)/bz
                    bm.verts[vid].co = lerp(original_pos[vid], bm.verts[vid].co, w)
                for j in range(bz):  # tail
                    idx = n - 1 - j
                    vid = path[idx]
                    w = j / bz
                    bm.verts[vid].co = lerp(original_pos[vid], bm.verts[vid].co, w)

            straightened += 1

        bm.normal_update()
        bmesh.update_edit_mesh(me, loop_triangles=True)
        self.report({"INFO"}, f"Set Edge Linear: {straightened} path(s)")
        return {"FINISHED"}


def register():
    bpy.utils.register_class(MESH_OT_set_edge_linear)


def unregister():
    bpy.utils.unregister_class(MESH_OT_set_edge_linear)


if __name__ == "__main__":
    register()