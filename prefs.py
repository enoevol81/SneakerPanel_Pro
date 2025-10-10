import bpy
from bpy.props import BoolProperty
from bpy.types import AddonPreferences
from bpy.props import StringProperty
from .utils import license_manager


# -------------------------------------------------------------------------
ADDON_ID = __package__.split(".")[0] if __package__ else __name__.split(".")[0]


class SPPVerifyLicenseOperator(bpy.types.Operator):
    bl_idname = "spp.verify_license"
    bl_label = "Verify License"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        prefs = get_prefs()
        success, message = license_manager.validate_license(
            prefs.license_key, prefs.buyer_email
        )
        prefs.license_status = message

        # If license verification successful, enable UI panels
        if success and "verified" in message.lower():
            license_manager.enable_ui_after_license()
            self.report({"INFO"}, "License verified! UI panels enabled.")
        elif not success:
            self.report({"ERROR"}, f"License verification failed: {message}")

        return {"FINISHED"}


class SPPrefs(AddonPreferences):
    bl_idname = ADDON_ID

    license_key: StringProperty(
        name="License Key",
        description="Enter your Gumroad or offline license key",
        default="",
    )

    buyer_email: StringProperty(
        name="Buyer Email (for offline activation)",
        description="Used for offline license validation (Blender Market)",
        default="",
    )

    license_status: StringProperty(name="License Status", default="Unverified")

    enable_experimental_qd: BoolProperty(
        name="Enable Experimental: NURBS to Surface (Q&D)",
        description="Unlock experimental quick & dirty workflows panel",
        default=False,
    )

    def draw(self, context):
        layout = self.layout

        # Refresh current status from cached license if needed
        cached = license_manager.load_local_license()
        if cached and "status" in cached and self.license_status in {"", "Unverified"}:
            self.license_status = cached["status"]

        # License section
        col = layout.column()
        col.prop(self, "license_key")
        col.prop(self, "buyer_email")

        row = col.row()
        row.operator("spp.verify_license", icon="KEYINGSET")
        row.operator("spp.reset_license", icon="TRASH")

        status = self.license_status.lower()
        if "verified" in status:
            col.label(text=f"✅ {self.license_status}", icon="CHECKMARK")
        elif "offline" in status:
            col.label(text=f"🔓 {self.license_status}", icon="FILE_TICK")
        elif "trial" in status:
            col.label(text=f"🕒 {self.license_status}", icon="TIME")
        else:
            col.label(text=f"⚠ {self.license_status}", icon="ERROR")

        # Experimental features section
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Modules", icon="PREFERENCES")
        col.prop(self, "enable_experimental_qd")
        col.label(text="Experimental features may be unstable.", icon="INFO")


class SPP_OT_ResetLicense(bpy.types.Operator):
    bl_idname = "spp.reset_license"
    bl_label = "Reset License"
    bl_description = "Clear cached license and restart validation"

    def execute(self, context):
        from .utils import license_manager

        try:
            license_manager.clear_local_license()
            prefs = context.preferences.addons[__package__].preferences
            prefs.license_status = "Unverified"
            self.report(
                {"INFO"}, "License reset successfully. Restart Blender to re-activate."
            )
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Reset failed: {e}")
            return {"CANCELLED"}


def get_prefs(context=None):
    if context is None:
        context = bpy.context
    return context.preferences.addons[ADDON_ID].preferences


def register():
    bpy.utils.register_class(SPPrefs)
    bpy.utils.register_class(SPPVerifyLicenseOperator)
    bpy.utils.register_class(SPP_OT_ResetLicense)


def unregister():
    bpy.utils.unregister_class(SPPrefs)
    bpy.utils.unregister_class(SPPVerifyLicenseOperator)
    bpy.utils.unregister_class(SPP_OT_ResetLicense)
