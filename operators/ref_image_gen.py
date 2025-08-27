# Blender 4.4+ — Profile Projection: Auto Clone Transfer (Tester, simplified)
# Run in Scripting (Alt+P). N-panel: View3D > "ProfileProj"

import bpy
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, EnumProperty, PointerProperty, IntProperty, FloatProperty
from mathutils import Vector
from bpy_extras import view3d_utils

# -------------------------
# Helpers
# -------------------------
def get_shell(context):
    o = context.active_object
    return o if (o and o.type == 'MESH') else None

def load_or_get_image(path):
    if not path:
        return None
    abspath = bpy.path.abspath(path)
    for img in bpy.data.images:
        try:
            if img.filepath and bpy.path.abspath(img.filepath) == abspath:
                return img
        except Exception:
            pass
    return bpy.data.images.load(abspath)

def ensure_uv_layer(obj, name):
    me = obj.data
    uv = me.uv_layers.get(name)
    if uv is None:
        uv = me.uv_layers.new(name=name)
    me.uv_layers.active = uv
    return uv

def get_or_active_main_uv(obj, name_hint):
    me = obj.data
    uv = me.uv_layers.get(name_hint) if name_hint else None
    if uv is None:
        uv = me.uv_layers.active if me.uv_layers.active else (me.uv_layers[0] if me.uv_layers else None)
    return uv.name if uv else None

def ensure_reference_material_on_main_uv(obj, baked_image, main_uv_name):
    """Material 'Reference Image' maps baked_image by MAIN UV into Base Color only."""
    mat = obj.active_material
    if not mat or mat.name != "Reference Image":
        mat = bpy.data.materials.get("Reference Image") or bpy.data.materials.new("Reference Image")
        obj.active_material = mat
    mat.use_nodes = True
    nt = mat.node_tree; nodes = nt.nodes; links = nt.links

    out = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None) or nodes.new("ShaderNodeOutputMaterial")
    bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None) or nodes.new("ShaderNodeBsdfPrincipled")
    out.location = (600, 0); bsdf.location = (0, 0)

    if not out.inputs['Surface'].is_linked:
        links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    uvn = nodes.get("SPP_MainUV") or nodes.new("ShaderNodeUVMap"); uvn.name = "SPP_MainUV"; uvn.uv_map = main_uv_name
    itex = nodes.get("SPP_BakedImage") or nodes.new("ShaderNodeTexImage"); itex.name = "SPP_BakedImage"; itex.image = baked_image

    # Wire baked image into Base Color using Main UV
    if itex.inputs['Vector'].is_linked:
        for l in list(itex.inputs['Vector'].links):
            nt.links.remove(l)
    links.new(uvn.outputs['UV'], itex.inputs['Vector'])
    if bsdf.inputs['Base Color'].is_linked:
        for l in list(bsdf.inputs['Base Color'].links):
            nt.links.remove(l)
    links.new(itex.outputs['Color'], bsdf.inputs['Base Color'])

    # Make the image node the active paint slot (useful if switching to Material mode later)
    for n in nodes: n.select = False
    itex.select = True
    nt.nodes.active = itex
    return mat

def find_view3d_area_region():
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            return area, region, space
    return None, None, None

def obj_screen_bounds(obj, area, region, space):
    coords = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    xs, ys = [], []
    for co in coords:
        p = view3d_utils.location_3d_to_region_2d(region, space.region_3d, co)
        if p is not None:
            xs.append(p.x); ys.append(p.y)
    if not xs or not ys:
        return None
    return (min(xs), min(ys)), (max(xs), max(ys))

def build_stroke_line(x0, y, x1, steps, size_px, pressure=1.0):
    pts = []
    if steps < 2:
        steps = 2
    dx = (x1 - x0) / (steps - 1)
    for i in range(steps):
        x = x0 + i*dx
        pts.append({
            "name": "stroke",
            "mouse": (x, y),
            "mouse_event": (x, y),
            "is_start": (i == 0),
            "pen_flip": False,
            "pressure": pressure,
            "size": size_px,
            "time": 0.0
        })
    return pts

def set_clone_context(obj, src_img, proj_uv_name, main_uv_name, brush_size=60, strength=1.0):
    # Activate Texture Paint mode
    try:
        bpy.ops.object.mode_set(mode='TEXTURE_PAINT')
    except Exception:
        pass

    me = obj.data
    if me.uv_layers.get(main_uv_name):
        me.uv_layers.active = me.uv_layers.get(main_uv_name)
    for uv in me.uv_layers:
        uv.active_clone = (uv.name == proj_uv_name)

    # Tool settings → Single Image mode targeting "Projected Design"
    ts = bpy.context.scene.tool_settings
    ip = ts.image_paint
    ip.mode = 'IMAGE'          # <-- Single Image
    ip.canvas = dest_img       # <-- Texture Slot image = Projected Design
    ip.seam_bleed = 2
    ip.clone_image = src_img   # Clone from Illustrator export

    # Switch to Clone tool (minimal override to avoid context errors)
    area, region, space = find_view3d_area_region()
    if area and region:
        override = {'area': area}
        try:
            bpy.ops.wm.tool_set_by_id(override, name="builtin.clone")
        except Exception:
            pass

    # Ensure a brush and sensible defaults
    if not ts.image_paint.brush:
        try:
            ts.image_paint.brush = bpy.data.brushes.new("SPP_Clone")
        except Exception:
            pass
    br = ts.image_paint.brush
    br.strength = 1.0
    br.size = 64  # px
    return br

# -------------------------
# Properties & UI
# -------------------------
class ProfileProjProps(PropertyGroup):
    image_path: StringProperty(name="2D Profile Image", subtype='FILE_PATH')
    projection_uv: StringProperty(name="Projection UV", default="Projection")
    main_uv: StringProperty(name="Main UV", default="UV Mesh")
    dest_size: EnumProperty(
        name="Dest Size",
        items=[('1024','1K',''), ('2048','2K',''), ('4096','4K','')],
        default='2048'
    )

# -------------------------
# Operators
# -------------------------
class PP_OT_CreateProjectionUV(Operator):
    bl_idname = "pp.create_projection_uv"
    bl_label = "1. Create 'Projection' UV + From View"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.profile_proj
        obj = get_shell(context)
        if not obj:
            self.report({'ERROR'}, "Select a mesh object")
            return {'CANCELLED'}
        if not props.image_path:
            self.report({'ERROR'}, "Pick your 2D profile image")
            return {'CANCELLED'}

        # Show the image in UV editor so the user can align
        img = load_or_get_image(props.image_path)
        for area in bpy.context.window.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                for space in area.spaces:
                    if space.type == 'IMAGE_EDITOR':
                        space.image = img

        # Create/activate Projection UV and Project From View (use current view)
        ensure_uv_layer(obj, props.projection_uv)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.project_from_view(correct_aspect=True, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode='OBJECT')

        self.report({'INFO'}, "Projection UV created from the current view. Align it in the UV Editor.")
        return {'FINISHED'}

class PP_OT_CreateDestMaterial(Operator):
    bl_idname = "pp.create_dest_and_material"
    bl_label = "2. Create Img Texture + Material"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.profile_proj
        obj = get_shell(context)
        if not obj:
            self.report({'ERROR'}, "Select a mesh object")
            return {'CANCELLED'}

        main_uv = get_or_active_main_uv(obj, props.main_uv)
        if not main_uv:
            self.report({'ERROR'}, "Mesh has no UVs. Unwrap first.")
            return {'CANCELLED'}

        size = int(props.dest_size)
        dest_img = bpy.data.images.get("Projected Design")
        if dest_img is None or dest_img.size[0] != size:
            if dest_img and dest_img.users == 0:
                bpy.data.images.remove(dest_img)
            dest_img = bpy.data.images.new("Projected Design", width=size, height=size, alpha=True)
            dest_img.generated_color = (0,0,0,0)

        ensure_reference_material_on_main_uv(obj, dest_img, main_uv)
        self.report({'INFO'}, f"Created/assigned '{dest_img.name}' and material 'Reference Image' on Main UV")
        return {'FINISHED'}

class PP_OT_AutoCloneTransfer(Operator):
    bl_idname = "pp.auto_clone_transfer"
    bl_label = "3. Transfer Image UV"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.profile_proj
        obj = get_shell(context)
        if not obj:
            self.report({'ERROR'}, "Select a mesh object")
            return {'CANCELLED'}
        src_img = load_or_get_image(props.image_path)
        if not src_img:
            self.report({'ERROR'}, "Pick your 2D profile image")
            return {'CANCELLED'}

        proj_uv = ensure_uv_layer(obj, props.projection_uv).name
        main_uv = get_or_active_main_uv(obj, props.main_uv)
        if not main_uv:
            self.report({'ERROR'}, "Mesh has no UVs. Unwrap first.")
            return {'CANCELLED'}

        # Ensure destination image + material and set Texture Paint Single Image targeting it
        size = int(props.dest_size)
        dest_img = bpy.data.images.get("Projected Design") or bpy.data.images.new("Projected Design", width=size, height=size, alpha=True)
        dest_img.generated_color = (0,0,0,0)
        ensure_reference_material_on_main_uv(obj, dest_img, main_uv)

        # Prepare clone context (Single Image mode + canvas=Projected Design + clone_image=src)
        set_clone_context(obj, src_img, proj_uv, main_uv, dest_img)

        # Find a 3D view to paint into
        area, region, space = find_view3d_area_region()
        if not area:
            self.report({'ERROR'}, "No 3D View area found")
            return {'CANCELLED'}
        override = {'area': area, 'region': region}

        # Compute on-screen bounds of the object to sweep strokes over
        bounds = obj_screen_bounds(obj, area, region, space)
        if bounds is None:
            self.report({'ERROR'}, "Cannot compute screen bounds for object")
            return {'CANCELLED'}
        (x0, y0), (x1, y1) = bounds

        # Use conservative defaults (no UI knobs): 28 rows, 80 samples, 64px brush, full strength
        rows, samples, size_px, pressure = 28, 80, 64, 1.0
        dy = (y1 - y0) / (rows + 1)
        for i in range(1, rows+1):
            y = y0 + i*dy
            stroke = build_stroke_line(x0, y, x1, steps=samples, size_px=size_px, pressure=pressure)
            try:
                bpy.ops.paint.image_paint(override, stroke=stroke, mode='NORMAL')
            except Exception:
                pass

        self.report({'INFO'}, "Auto Clone Transfer complete for current view. Repeat from the opposite side if needed.")
        return {'FINISHED'}

# -------------------------
# Register
# -------------------------
classes = (
    ProfileProjProps,
    PP_OT_CreateProjectionUV,
    PP_OT_CreateDestMaterial,
    PP_OT_AutoCloneTransfer,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.profile_proj = PointerProperty(type=ProfileProjProps)

def unregister():
    del bpy.types.Scene.profile_proj
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
