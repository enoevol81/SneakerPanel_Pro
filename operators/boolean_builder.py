import bpy
from bpy.types import Operator
from bpy.props import StringProperty


class OBJECT_OT_BooleanBuilder(Operator):
    """Guided Boolean Builder - Step-by-step boolean operation setup"""
    bl_idname = "object.boolean_builder"
    bl_label = "Boolean Builder"
    bl_options = {'REGISTER', 'UNDO'}

    action: StringProperty(
        name="Action",
        description="Action to perform",
        default="START"
    )

    def execute(self, context):
        scene = context.scene
        
        if self.action == "START":
            # Initialize boolean builder mode
            scene.spp_boolean_state = "SELECT_MAIN"
            scene.spp_boolean_main_object = ""
            scene.spp_boolean_target_object = ""
            self.report({'INFO'}, "Boolean Builder: Select the main panel object")
            
        elif self.action == "SELECT_MAIN":
            # Set main object
            if context.active_object and context.active_object.type == 'MESH':
                scene.spp_boolean_main_object = context.active_object.name
                scene.spp_boolean_state = "SELECT_TARGET"
                
                # Highlight main object in blue (using selection)
                bpy.ops.object.select_all(action='DESELECT')
                context.active_object.select_set(True)
                context.view_layer.objects.active = context.active_object
                
                self.report({'INFO'}, f"Main object selected: {context.active_object.name}. Now select object to subtract")
            else:
                self.report({'ERROR'}, "Please select a mesh object as the main panel")
                
        elif self.action == "SELECT_TARGET":
            # Set target object
            if context.active_object and context.active_object.type == 'MESH':
                if context.active_object.name != scene.spp_boolean_main_object:
                    scene.spp_boolean_target_object = context.active_object.name
                    scene.spp_boolean_state = "READY_TO_BOOLEAN"
                    
                    # Highlight target object differently (we'll use material override for red)
                    self._highlight_target_object(context, context.active_object)
                    
                    self.report({'INFO'}, f"Target object selected: {context.active_object.name}. Ready to create boolean")
                else:
                    self.report({'ERROR'}, "Target object must be different from main object")
            else:
                self.report({'ERROR'}, "Please select a mesh object to subtract")
                
        elif self.action == "CREATE_BOOLEAN":
            # Create the boolean modifier
            main_obj_name = scene.spp_boolean_main_object
            target_obj_name = scene.spp_boolean_target_object
            
            if main_obj_name and target_obj_name:
                main_obj = bpy.data.objects.get(main_obj_name)
                target_obj = bpy.data.objects.get(target_obj_name)
                
                if main_obj and target_obj:
                    # Create boolean modifier on main object
                    bool_mod = main_obj.modifiers.new(name="Boolean_Subtract", type='BOOLEAN')
                    bool_mod.operation = 'DIFFERENCE'
                    bool_mod.object = target_obj
                    bool_mod.solver = 'EXACT'  # Use exact solver for better results
                    
                    # Select main object and make it active
                    bpy.ops.object.select_all(action='DESELECT')
                    main_obj.select_set(True)
                    context.view_layer.objects.active = main_obj
                    
                    # Clear highlighting
                    self._clear_highlighting(context)
                    
                    # Reset state
                    scene.spp_boolean_state = "NONE"
                    
                    self.report({'INFO'}, f"Boolean modifier created on {main_obj.name}")
                else:
                    self.report({'ERROR'}, "One or both objects no longer exist")
            else:
                self.report({'ERROR'}, "Main and target objects must be selected")
                
        elif self.action == "CANCEL":
            # Cancel boolean builder mode
            scene.spp_boolean_state = "NONE"
            scene.spp_boolean_main_object = ""
            scene.spp_boolean_target_object = ""
            self._clear_highlighting(context)
            self.report({'INFO'}, "Boolean Builder cancelled")
            
        return {'FINISHED'}
    
    def _highlight_target_object(self, context, obj):
        """Highlight target object in red using viewport color"""
        try:
            # Set object color to red for highlighting
            obj.color = (1.0, 0.0, 0.0, 1.0)  # Red color
            # Enable object color display in viewport
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            space.shading.color_type = 'OBJECT'
                            break
        except Exception as e:
            print(f"Could not highlight object: {e}")
    
    def _clear_highlighting(self, context):
        """Clear object highlighting"""
        try:
            # Reset object colors
            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    obj.color = (1.0, 1.0, 1.0, 1.0)  # White (default)
            
            # Reset viewport shading
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            space.shading.color_type = 'MATERIAL'
                            break
        except Exception as e:
            print(f"Could not clear highlighting: {e}")


# Registration
classes = [
    OBJECT_OT_BooleanBuilder,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass


if __name__ == "__main__":
    register()
