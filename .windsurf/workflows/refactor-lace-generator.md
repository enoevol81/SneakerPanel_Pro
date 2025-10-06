---
description: Im scrapping the current execution of the lace generator - Ive now included a blend file set up with 4 different geometry nodes representing each of the lace options along with their profiles and a custom material
auto_execution_mode: 1
---

### A) Asset loader utility (append-once)

1. Create `operators/spp_lace_loader.py` with a small utility that:
    - Resolves add-on dir → `assets/spp_lace_assets.blend`.
    - Appends (not links) **GN node groups** and **`spp_lace_material`** if missing.
    - Sets `use_fake_user=True` on appended datablocks so they persist.
2. Make it idempotent (safe to call multiple times).

### B) Apply operator (per user action)

1. Create `operators/spp_lace_apply.py` with an operator that:
    - Ensures assets via the loader.
    - Validates selection is a **Curve**.
    - Enum `lace_type`: `ROUND`, `OVAL`, `FLAT`, `CUSTOM` → maps to `SPP_Lace_Round/Oval/Flat/Custom`.
    - Adds a **Geometry Nodes** modifier and assigns the chosen group.
    - Sets common inputs by **name** (robust to interface order).
    - Shows **Custom Profile** picker only when `CUSTOM` is chosen.
    - Material default: if checkbox “Use default material” is on, set the **Material** input to `spp_lace_material`; otherwise allow a user override.
    - Passes the picked **color** to the group’s `Lace Color` input (GN stores it to `spp_lace_color`).

### C) Lace Generator Panel UI

1. Create `operators/spp_lace_panel.py` with a Panel:
    - Profile selector enum: **Round / Oval / Flat / Custom**
    - If **Custom** → show `Custom Profile` object picker.
    - Controls mirrored to GN: `Resample`, `Scale`, `Tilt`, `Normal Mode` (dropdown), `Flip V`, `Flip Normal`, `Shade Smooth`
    - **Color picker** (maps to `Lace Color`)
    - Material section:
        - Toggle “Use default spp_lace_material”
        - If off → Material picker
    - Button: **Apply Lace** (calls the operator).
2. Keep the **same control naming** as the GN sockets so you can set modifier inputs by **name** (Windsurf should implement name-based writes, not index-based).

### D) Register / Clean up

1. In `__init__.py`:
    - Import and register the loader, apply operator, and panel.
    - (Optional) on `register()`, pre-load assets so first click in UI is instant.
2. Remove/disable any old code that tried to **build GN with Python** for laces.
3. Update the add-on preferences/help text to mention the asset file approach.

### F) QA checklist

- Test all four profiles on various curves (closed/open, varying tilt).
- Confirm `Flip V` and `Flip Normal` behave.
- Confirm `Lace Color` drives tint in the material across all profiles.
- Confirm default material is applied; override works.
- Save, reopen file → assets persist (fake user set).

---

# Internal Node Requirements

| Socket Name | Type | Notes |
| --- | --- | --- |
| `Resample` | Integer | Number of samples along curve. Default = `110`. |
| `Scale` | Float | Lace width scaling. Default = `1` |
| `Tilt` | Float | Angle subtype. Tilt along curve. Default = `0`. |
| `Normal Mode` | Integer | 0 = Min Twist, 1 = Z Up, 2 = Free. |
| Free Normal Control | Vector | Conditionally available only if Normal Mode =2 (Free) is seclected |
| `Flip V` | Boolean | UV vertical flip. Default = `False`. |
| `Flip Normal` | Boolean | Flip Faces node selection. Default = `False`. |
| `Shade Smooth` | Boolean | Toggle smoothing. Default = `True`. |
| `Material` | Material | Default set to `spp_lace_material`. |
| `Lace Color` | Color | Exposed to user. Stored as `spp_lace_color` (Face Corner, Color). |
| *(Custom only)* `Custom Profile` | Object | Curve object. Must run `Object Info → Realize Instances`. |
1. **Custom Profile branch (SPP_Lace_Custom only):**
    - `Object Info (As Instance OFF)` → `Realize Instances` before feeding into Curve to Mesh.
2. **UVs:**
    - Use `Spline Parameter (Factor)` from path as U.
    - Use `Spline Parameter (Factor)` from profile as V.
    - Add `Flip V` toggle (`Mix` node with `1-V`).
    - Store as **Named Attribute `"LaceUV"`** → Domain = Face Corner, Data Type = Vector.
3. **Flip Faces:**
    - `Flip Faces` node included.
    - `Flip Normal` (bool input) → Selection.
4. **Material:**
    - `Set Material` at the end.
    - `Material` input socket default = `spp_lace_material`.
5. **Color:**
    - `Lace Color` (Color input) stored as **Named Attribute `"spp_lace_color"`** → Domain = Face Corner, Data Type = Color.
    - `spp_lace_material` must have an **Attribute** node named `"spp_lace_color"` plugged into Base Color.

---

## Material: `spp_lace_material`

- Exists inside `spp_lace_assets.blend`.
- Uses packed textures for normals (Non-Color), with Strength boosted (2.0 recommended).
- Attribute node `"spp_lace_color"` multiplies or overrides Base Color.
- Fake user enabled.

---

## Loader Contract

- Loader in `operators/spp_lace_loader.py` must:
    - Append node groups (`SPP_Lace_*`) and `spp_lace_material` if missing.
    - Set `use_fake_user=True` for persistence.
- Append, don’t link, for editability.

---

## Plugin/Panel Contract

- Enum in UI → maps to groups:
    - `ROUND` → `SPP_Lace_Round`
    - `OVAL` → `SPP_Lace_Oval`
    - `FLAT` → `SPP_Lace_Flat`
    - `CUSTOM` → `SPP_Lace_Custom` (+ object picker)
- Operator sets modifier inputs by **name** (not index).
- Expose all sockets listed above in the panel, including **Color Picker** (`Lace Color`) and Material override.
- **Always set modifier inputs by name**: `mod["Scale"] = 0.005`, not positional indexes.
- Ensure your **enum → int** mapping for `Normal Mode` matches the GN compare nodes (0=min twist, 1=z-up, 2=free).
- For **Custom Profile**, validate the picked object is a **Curve**; if not, error out gracefully.
- The loader must handle **appending multiple datablock types in one go** (node_groups, materials, objects if you include helper curves).
- Keep the asset path relative to the add-on root: `os.path.join(addon_dir, "assets", "spp_lace_assets.blend")`.