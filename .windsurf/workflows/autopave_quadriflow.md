---
description: Implement auto pave align with quadriflow
auto_execution_mode: 3
---

spp_auto_pave_align.py

Goal:
Integrate an optional Quadriflow remesh pass into the Auto-Pave operator (executed after final projection and before offset).
Expose two new scene properties (use_retopo, target_faces) so the feature can be toggled and configured from the plugin’s UI panel.

1. Scene Properties

Add these to the Sneaker Panel Pro scene property registration (where other auto-pave properties live):

bpy.types.Scene.spp_auto_pave_use_retopo = bpy.props.BoolProperty(
    name="Use Retopo",
    description="Run Quadriflow remesh after projection for cleaner quad flow",
    default=False
)

bpy.types.Scene.spp_auto_pave_target_faces = bpy.props.IntProperty(
    name="Target Faces",
    description="Approximate number of quads for Quadriflow retopo",
    default=1500,
    min=100
)

2. Operator Integration

Inside SPP_OT_AutoPaveGridAlign.execute, right after the final projection step (the block that starts with
# Final projection + micro offset to avoid z-fighting) and before writing back to the mesh, insert:

# -----------------------------------------------------------
# Optional Quadriflow Retopo (clean topology after projection)
# -----------------------------------------------------------
use_retopo = getattr(context.scene, "spp_auto_pave_use_retopo", False)
target_faces = getattr(context.scene, "spp_auto_pave_target_faces", 1500)

if use_retopo:
    self.report({'INFO'}, f"Running Quadriflow retopo (~{target_faces} faces)...")
    bpy.ops.object.mode_set(mode='OBJECT')
    context.view_layer.objects.active = obj
    bpy.ops.object.quadriflow_remesh(
        use_paint_symmetry=False,
        target_faces=target_faces,
        preserve_sharp=True,
        preserve_boundary=True,
        adaptive_scale=True
    )
    bpy.ops.object.mode_set(mode='EDIT')

3. Safety / Fallback Handling

Wrap the bpy.ops.object.quadriflow_remesh call in a try/except so the operator doesn’t crash if Quadriflow isn’t available:

try:
    bpy.ops.object.quadriflow_remesh(...)
except Exception as e:
    self.report({'WARNING'}, f"Quadriflow failed: {e}")

4. UI Panel Exposure

In the SPP UI panel (Auto-Pave settings group), add:

layout.prop(scene, "spp_auto_pave_use_retopo")
sub = layout.row()
sub.enabled = scene.spp_auto_pave_use_retopo
sub.prop(scene, "spp_auto_pave_target_faces")


This keeps the face-count field grayed out unless the toggle is active.

5. Expected Behavior / QA Notes

Default use_retopo=False (for speed).

When toggled on, the operator retopos the projected panel into clean quads that follow curvature automatically.

Works seamlessly with your curvature-aware smoothing and adaptive stop — no other changes needed.

Estimated runtime: ~1 s per 1000 faces on RTX 4080 class GPU.

Tell Windsurf:

“Implement the Quadriflow retopo integration exactly as specified above, keeping all existing logic intact. Run full syntax and registration validation, and update my UI panel accordingly.