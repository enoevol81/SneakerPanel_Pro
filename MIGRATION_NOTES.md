# Migration Notes (Blender 4.4.3 → 4.5+)

- Wrap any Grease Pencil drawing/surface placement flags through `compat.py`.
- Avoid hard-coded RNA enum strings where possible.
- When 4.5 is installed, smoke-test:
  - GP to Curve conversion
  - Surface snapping & projection
  - UI panels draw without warnings in the Console
