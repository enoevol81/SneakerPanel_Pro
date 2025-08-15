# -------------------------------------------------------------------------
# Tooltip audit utility
# -------------------------------------------------------------------------

import bpy
import inspect


def run(verbose: bool = True) -> dict:
    missing_ops = []
    missing_props = {}
    total = 0

    for name in dir(bpy.types):
        cls = getattr(bpy.types, name, None)
        if (
            isinstance(cls, type)
            and issubclass(cls, bpy.types.Operator)
            and hasattr(cls, "bl_idname")
            and hasattr(cls, "bl_label")
        ):
            total += 1
            desc = getattr(cls, "bl_description", "")
            if not isinstance(desc, str) or not desc.strip():
                missing_ops.append(name)

            ann = getattr(cls, "__annotations__", {}) or {}
            props_missing = []
            for pname in ann:
                try:
                    pval = getattr(cls, pname, None)
                    d = getattr(pval, "description", None)
                    if isinstance(d, str) and len(d.strip()) == 0:
                        props_missing.append(pname)
                except Exception:
                    pass
            if props_missing:
                missing_props[name] = props_missing

    if verbose:
        print("=== Tooltip Audit Report ===")
        print(f"Operators checked: {total}")
        print(f"Missing bl_description: {len(missing_ops)}")
        for op in missing_ops:
            print(f"  - {op}")
        print("Operators with properties missing description:", len(missing_props))
        for op, props in missing_props.items():
            print(f"  - {op}: {', '.join(props)}")
        print("=== End Report ===")

    return {
        "operators_missing_bl_description": missing_ops,
        "properties_missing_description": missing_props,
        "total_operators_checked": total,
    }


class SPP_OT_RunTooltipAudit(bpy.types.Operator):
    bl_idname = "spp.run_tooltip_audit"
    bl_label = "Run Tooltip Audit"
    bl_description = "Scan registered operators for missing hover tooltips and property descriptions"

    def execute(self, context):
        run(verbose=True)
        self.report({'INFO'}, "Tooltip audit complete. See Console for report.")
        return {'FINISHED'}


classes = (SPP_OT_RunTooltipAudit,)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
