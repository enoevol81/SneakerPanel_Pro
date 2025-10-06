# SPP Lace Generator - Asset-Based System

## Overview
The new lace generator system uses pre-built Geometry Node groups from `assets/spp_lace_assets.blend` instead of generating nodes programmatically. This provides better reliability, easier maintenance, and more complex lace profiles.

## Components

### 1. Asset Loader (`spp_lace_loader.py`)
- Loads geometry node groups and materials from the asset file
- Idempotent - safe to call multiple times
- Sets `use_fake_user=True` for persistence
- Auto-loads on addon registration for instant first use

### 2. Apply Operator (`spp_lace_apply.py`)
- Applies selected lace profile to curve objects
- Supports 4 profile types: Round, Oval, Flat, Custom
- Sets all parameters by name (robust to node interface changes)
- Handles material assignment and color customization

### 3. Panel UI (`spp_lace_panel.py`)
- User-friendly interface in the 3D viewport N-panel
- Dynamic controls based on selected profile type
- Real-time parameter adjustment
- Material and color customization options

## Asset File Structure

### Geometry Node Groups
- `SPP_Lace_Round` - Circular cross-section lace
- `SPP_Lace_Oval` - Oval/elliptical cross-section lace
- `SPP_Lace_Flat` - Flat ribbon-style lace
- `SPP_Lace_Custom` - Accepts custom curve profile object

### Materials
- `spp_lace_material` - Default lace material with texture support
  - Uses `spp_lace_color` attribute for color tinting
  - Includes normal mapping for detail
  - Fake user enabled for persistence

## Node Group Inputs

All lace node groups expose these inputs:

| Input Name | Type | Description | Default |
|------------|------|-------------|---------|
| Resample | Integer | Samples along curve | 110 |
| Scale | Float | Lace width scaling | 1.0 |
| Tilt | Float | Rotation along curve | 0.0 |
| Normal Mode | Integer | 0=Min Twist, 1=Z-Up, 2=Free | 0 |
| Free Normal Control | Vector | Only for Normal Mode=2 | (0,0,1) |
| Flip V | Boolean | Flip UV V coordinate | False |
| Flip Normal | Boolean | Flip face normals | False |
| Shade Smooth | Boolean | Apply smooth shading | True |
| Material | Material | Material to apply | spp_lace_material |
| Lace Color | Color | Color tinting | (0.8,0.8,0.8,1.0) |
| Custom Profile | Object | Curve object (Custom type only) | None |

## Usage Workflow

1. **Select a curve object** in the viewport
2. **Open Lace Generator panel** in the N-panel
3. **Choose profile type** (Round/Oval/Flat/Custom)
4. **Adjust parameters** as needed
5. **Set color** using the color picker
6. **Click "Apply Lace"** to generate the lace geometry

## Technical Notes

### Parameter Setting
The operator sets modifier inputs by name, not index:
```python
modifier["Scale"] = 1.0  # Correct
modifier[1] = 1.0  # Avoid - fragile to interface changes
```

### Custom Profiles
When using Custom profile type:
- Must select a valid Curve object
- The curve is processed through Object Info → Realize Instances
- Allows for complex, user-defined lace cross-sections

### UV Mapping
- U coordinate: Spline parameter along the main curve
- V coordinate: Spline parameter along the profile
- Stored as named attribute "LaceUV" (Face Corner domain)

### Color System
- Color is stored as named attribute "spp_lace_color"
- Material reads this attribute for Base Color multiplication
- Allows per-lace color customization

## Migration from Old System

The old Python-based node generation system (`lace_from_curves.py`) has been disabled. Benefits of the new system:

1. **Reliability**: Pre-built nodes are guaranteed to work
2. **Performance**: No runtime node generation overhead
3. **Complexity**: Supports more sophisticated node setups
4. **Maintenance**: Easier to update and debug in Blender
5. **Consistency**: All users get identical node setups

## Troubleshooting

### Asset File Not Found
- Ensure `assets/spp_lace_assets.blend` exists in the addon directory
- Check file permissions
- Verify the blend file contains all required node groups

### Parameters Not Updating
- Check that modifier input names match exactly
- Verify the node group has the expected inputs
- Use the Modifier Properties panel to see available inputs

### Custom Profile Issues
- Ensure selected object is a Curve type
- Check that the curve has valid geometry
- Try with a simple bezier circle first

## Future Enhancements

Potential improvements for future versions:
- Additional preset profiles (Square, Star, etc.)
- Animated lace parameters
- Multiple laces from single curve
- Lace pattern variations (twisted, braided)
- Integration with shoe last database
