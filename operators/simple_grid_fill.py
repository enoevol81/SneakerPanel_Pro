"""
Simple Grid Fill operator for UV workflow.

This operator provides a straightforward approach to filling selected geometry
with grid topology. It works with whatever is currently selected and doesn't
make assumptions about boundary loops or polylines.
"""

import bmesh
import bpy
from bpy.props import BoolProperty, IntProperty
from bpy.types import Operator


class MESH_OT_SimpleGridFill(Operator):
    """Simple grid fill for selected geometry.

    This operator applies grid fill to whatever is currently selected.
    It can optionally close open edges first and balance vertex counts.
    """

    bl_idname = "mesh.simple_grid_fill"
    bl_label = "Simple Grid Fill"
    bl_description = "Fill selected geometry with grid pattern"
    bl_options = {"REGISTER", "UNDO"}

    span: IntProperty(
        name="Span",
        description="Number of grid cells in one direction",
        default=1,
        min=1,
        max=100,
    )

    close_first: BoolProperty(
        name="Close Open Edges",
        description="Connect open endpoints before grid fill",
        default=True,
    )

    smooth_after: BoolProperty(
        name="Smooth After Fill",
        description="Apply smoothing after grid fill",
        default=True,
    )

    smooth_iterations: IntProperty(
        name="Smooth Iterations",
        description="Number of smoothing iterations",
        default=2,
        min=1,
        max=10,
    )

    @classmethod
    def poll(cls, context):
        """Check if we have an active mesh object."""
        obj = context.active_object
        return obj and obj.type == "MESH"

    def find_open_endpoints(self, bm):
        """Find vertices that are endpoints (connected to only one edge)."""
        endpoints = []
        for vert in bm.verts:
            if len(vert.link_edges) == 1:
                endpoints.append(vert)
        return endpoints

    def close_open_edges(self, bm):
        """Connect open endpoints to close the shape."""
        endpoints = self.find_open_endpoints(bm)

        if len(endpoints) == 2:
            # Simple case: connect the two endpoints
            try:
                new_edge = bm.edges.new(endpoints)
                bm.edges.ensure_lookup_table()
                self.report({"INFO"}, "Connected 2 endpoints")
                return True
            except:
                self.report({"WARNING"}, "Could not connect endpoints")
                return False
        elif len(endpoints) > 2:
            # Multiple endpoints - connect them in a chain
            try:
                for i in range(len(endpoints) - 1):
                    bm.edges.new([endpoints[i], endpoints[i + 1]])
                # Close the loop by connecting last to first
                bm.edges.new([endpoints[-1], endpoints[0]])
                bm.edges.ensure_lookup_table()
                self.report({"INFO"}, f"Connected {len(endpoints)} endpoints in a loop")
                return True
            except:
                self.report({"WARNING"}, "Could not connect all endpoints")
                return False

        return False

    def execute(self, context):
        # Context-agnostic execution - automatically switch to required mode
        obj = context.active_object
        if not obj or obj.type != "MESH":
            self.report({"ERROR"}, "No active mesh object")
            return {"CANCELLED"}

        # Store original mode for restoration
        original_mode = obj.mode

        # Switch to Edit Mode if not already there
        if context.mode != "EDIT_MESH":
            try:
                bpy.ops.object.mode_set(mode="EDIT")
            except Exception as e:
                self.report({"ERROR"}, f"Could not switch to Edit Mode: {str(e)}")
                return {"CANCELLED"}

        try:
            bm = bmesh.from_edit_mesh(obj.data)

            # Report initial state
            self.report(
                {"INFO"},
                f"Starting: {len(bm.verts)} verts, {len(bm.edges)} edges, {len(bm.faces)} faces",
            )

            # Close open edges if requested
            if self.close_first:
                endpoints = self.find_open_endpoints(bm)
                if endpoints:
                    self.report({"INFO"}, f"Found {len(endpoints)} open endpoints")
                    self.close_open_edges(bm)
                    bmesh.update_edit_mesh(obj.data)
                else:
                    self.report({"INFO"}, "No open endpoints found")

            # Store original selection mode
            select_mode = context.tool_settings.mesh_select_mode[:]

            # Select all edges for grid fill
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.select_mode(type="EDGE")

            # Try grid fill
            try:
                bpy.ops.mesh.fill_grid(span=self.span)
                self.report({"INFO"}, f"Grid fill successful with span={self.span}")
                success = True
            except Exception as e:
                self.report({"ERROR"}, f"Grid fill failed: {str(e)}")
                # Try alternative: triangle fill then convert to quads
                try:
                    self.report({"INFO"}, "Trying triangle fill as fallback...")
                    bpy.ops.mesh.fill()
                    bpy.ops.mesh.tris_convert_to_quads()
                    self.report({"INFO"}, "Triangle fill + quad conversion successful")
                    success = True
                except Exception as e2:
                    self.report({"ERROR"}, f"Triangle fill also failed: {str(e2)}")
                    success = False

            # Apply smoothing if requested and fill was successful
            if success and self.smooth_after:
                try:
                    # Get fresh bmesh instance after fill operations
                    obj = context.active_object
                    bm = bmesh.from_edit_mesh(obj.data)
                    bm.faces.ensure_lookup_table()
                    bm.edges.ensure_lookup_table()
                    bm.verts.ensure_lookup_table()

                    # Identify boundary vertices to preserve
                    boundary_verts = set()
                    for edge in bm.edges:
                        if edge.is_boundary:
                            boundary_verts.update(edge.verts)

                    # Get interior vertices only
                    interior_verts = [v for v in bm.verts if v not in boundary_verts]

                    if interior_verts:
                        self.report(
                            {"INFO"},
                            f"Smoothing {len(interior_verts)} interior vertices, preserving {len(boundary_verts)} boundary vertices",
                        )

                        # Apply smoothing iterations to interior vertices only
                        for iteration in range(self.smooth_iterations):
                            new_positions = {}

                            for vert in interior_verts:
                                if len(vert.link_edges) == 0:
                                    continue

                                # Calculate average position of connected vertices
                                connected_positions = []
                                for edge in vert.link_edges:
                                    other_vert = edge.other_vert(vert)
                                    connected_positions.append(other_vert.co.copy())

                                if connected_positions:
                                    avg_pos = sum(
                                        connected_positions, vert.co * 0
                                    ) / len(connected_positions)
                                    # Blend between original and average position
                                    new_pos = vert.co.lerp(avg_pos, 0.5)
                                    new_positions[vert] = new_pos

                            # Apply new positions
                            for vert, new_pos in new_positions.items():
                                vert.co = new_pos

                        # Update the mesh
                        bmesh.update_edit_mesh(obj.data)
                        obj.data.update()
                        self.report(
                            {"INFO"},
                            f"Applied {self.smooth_iterations} smoothing iterations",
                        )
                    else:
                        self.report(
                            {"INFO"},
                            "No interior vertices to smooth - all vertices are on boundary",
                        )

                except Exception as e:
                    self.report(
                        {"WARNING"}, f"Boundary-preserving smoothing failed: {str(e)}"
                    )

            # Restore original selection mode
            bpy.ops.mesh.select_mode(
                type="VERT" if select_mode[0] else "EDGE" if select_mode[1] else "FACE"
            )

            # Restore original mode if it was different
            if original_mode != "EDIT":
                try:
                    bpy.ops.object.mode_set(mode=original_mode)
                except:
                    pass  # Don't fail if mode restoration fails

            return {"FINISHED"} if success else {"CANCELLED"}

        except Exception as e:
            # Restore original mode on error
            if original_mode != "EDIT":
                try:
                    bpy.ops.object.mode_set(mode=original_mode)
                except:
                    pass
            self.report({"ERROR"}, f"Simple grid fill failed: {str(e)}")
            return {"CANCELLED"}


# Registration
classes = [MESH_OT_SimpleGridFill]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
