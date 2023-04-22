# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "NGx",
    "author": "Erindale @ Nodegroup.xyz",
    "description": "Collection of utilities and workflow tools for Blender",
    "version": (0, 1, 0),
    "blender": (3, 4, 0),
    "location": "Topmenu bar > NGx",
    "warning": "",
    "doc_url": "https://www.nodegroup.xyz/",
    "category": "3D View",
}

import bpy, os, sys
from bpy.types import Operator, Panel, Menu

#=============================================================================== FUNCTIONS

def open_file(filename):
    '''Open file in default application for the platform'''
    if sys.platform == "win32":
        os.startfile(filename)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, filename])


#=============================================================================== OPERATORS

class ngx_OT_reveal_in_explorer(Operator):
    bl_idname = "wm.ngx_reveal_in_explorer"
    bl_label = "Reveal in Explorer"
    bl_description = "Reveal in Explorer"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if bpy.data.filepath == "":
            cls.poll_message_set("Save the file!")
            return False    
        return True

    def execute(self, context):
        asset_dir = os.path.dirname(bpy.data.filepath)

        if os.path.exists(asset_dir):
            # os.startfile(asset_dir)
            open_file(asset_dir)
        else:
            show_message_box("Asset not found!", "Error", 'ERROR')
        return {'FINISHED'}
    
class ngx_OT_selected_wire_display(Operator):
    bl_idname = "wm.ngx_selected_wire_display"
    bl_label = "Selected as Wire"
    bl_description = "Draw selected as wire"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                obj.display_type = 'WIRE'
        return {'FINISHED'}

class ngx_OT_join_split_normals(Operator):
    bl_idname = "wm.ngx_join_split_normals"
    bl_label = "Join Split Normals"
    bl_description = "Join Split Normals"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        objs = context.selected_objects.copy()
        active = context.active_object
        bpy.ops.object.convert(target='MESH')

        bpy.ops.object.select_all(action='DESELECT')

        for obj in objs:
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.mesh.customdata_custom_splitnormals_add()
        
        bpy.context.view_layer.objects.active = active
        bpy.ops.object.join()
        active.data.use_auto_smooth = True
        return {'FINISHED'}

class ngx_OT_save_relative(Operator):
    bl_idname = "wm.ngx_save_relative"
    bl_label = "Save Relative"
    bl_description = "Save Relative"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bpy.ops.file.make_paths_relative()
        bpy.ops.wm.save_mainfile()
        return {'FINISHED'}

class ngx_OT_reload_linked_libraries(Operator):
    bl_idname = "wm.ngx_reload_linked_libraries"
    bl_label = "Reload Linked Libraries"
    bl_description = "Reload Linked Libraries"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        for lib in bpy.data.libraries:
            if lib.filepath:
                lib.reload()
        return {'FINISHED'}

class ngx_OT_shapekey_to_attribute(Operator):
    bl_idname = "wm.ngx_shapekey_to_attribute"
    bl_label = "Shape Keys to Attributes"
    bl_description = "Convert shape keys to vec3 point domain attributes"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                mesh_data = obj.data
                if mesh_data.shape_keys is not None:
                    key_blocks = mesh_data.shape_keys.key_blocks
                    attributes = mesh_data.attributes
                    for sk in key_blocks:
                        sk_name = sk.name
                        if sk_name in attributes:
                            attributes.remove(attributes[sk_name])
                        new_attribute = attributes.new(name=sk_name, type='FLOAT_VECTOR', domain='POINT')
                        sk_data = key_blocks[sk_name].data
                        for i, vertex in enumerate(sk_data):
                            new_attribute.data[i].vector = vertex.co
        return {'FINISHED'}

#=============================================================================== PANELS

class ngx_MT_object_tools(Menu):
    bl_label = "Object"

    def draw(self, context):
        layout = self.layout
        layout.operator("wm.ngx_selected_wire_display", icon='SHADING_WIRE')
        layout.operator("wm.ngx_join_split_normals", icon='MOD_NORMALEDIT')

class ngx_MT_data_tools(Menu):
    bl_label = "Data"

    def draw(self, context):
        layout = self.layout
        layout.operator("wm.ngx_shapekey_to_attribute", icon='SHAPEKEY_DATA')


#=================#

class ngx_MT_main_menu(Menu):
    bl_label = "NGx"

    def menu_draw(self, context):
        self.layout.menu("ngx_MT_main_menu")

    def draw(self, context):
        layout = self.layout
        layout.operator("wm.ngx_save_relative", icon='FILE_TICK')
        layout.operator("wm.ngx_reveal_in_explorer", icon='FILE_FOLDER')
        layout.operator("wm.ngx_reload_linked_libraries", icon='FILE_REFRESH')
        layout.menu("ngx_MT_object_tools", icon='OBJECT_DATA')
        layout.menu("ngx_MT_data_tools", icon='OUTLINER_DATA_MESH')


#=============================================================================== REGISTRATION


classes = [
    ngx_OT_reveal_in_explorer,
    ngx_OT_selected_wire_display,
    ngx_OT_join_split_normals,
    ngx_OT_save_relative,
    ngx_OT_reload_linked_libraries,
    ngx_OT_shapekey_to_attribute,
    ngx_MT_object_tools,
    ngx_MT_data_tools,
    ngx_MT_main_menu,
]

def register():
    from bpy.utils import register_class
    for cls in classes:
        try:
            register_class(cls)
        except Exception as e:
            print(f"Error registering {cls}")
    bpy.types.TOPBAR_MT_editor_menus.append(ngx_MT_main_menu.menu_draw)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    bpy.types.TOPBAR_MT_editor_menus.remove(ngx_MT_main_menu.menu_draw)