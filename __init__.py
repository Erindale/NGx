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
from bpy.types import Operator, Panel, Menu, PropertyGroup
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, FloatProperty, PointerProperty

#=============================================================================== FUNCTIONS

def open_file(filename):
    '''Open file in default application for the platform'''
    if sys.platform == "win32":
        os.startfile(filename)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, filename])


#=============================================================================== OPERATORS

class NGX_OT_reveal_in_explorer(Operator):
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
    
class NGX_OT_selected_wire_display(Operator):
    bl_idname = "wm.ngx_selected_wire_display"
    bl_label = "Selected as Wire"
    bl_description = "Draw selected as wire"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                obj.display_type = 'WIRE'
        return {'FINISHED'}

class NGX_OT_join_split_normals(Operator):
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

class NGX_OT_save_relative(Operator):
    bl_idname = "wm.ngx_save_relative"
    bl_label = "Save Relative"
    bl_description = "Save Relative"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        if bpy.data.filepath == "":
            cls.poll_message_set("Save the file!")
            return False    
        return True
    
    def execute(self, context):
        bpy.ops.file.make_paths_relative()
        bpy.ops.wm.save_mainfile()
        return {'FINISHED'}

class NGX_OT_reload_linked_libraries(Operator):
    bl_idname = "wm.ngx_reload_linked_libraries"
    bl_label = "Reload Linked Libraries"
    bl_description = "Reload Linked Libraries"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        for lib in bpy.data.libraries:
            if lib.filepath:
                try:
                    lib.reload()
                except:
                    pass
        return {'FINISHED'}

class NGX_OT_shapekey_to_attribute(Operator):
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


class NGX_Properties(PropertyGroup):
    target_object: PointerProperty(
        type=bpy.types.Object,
        name="Target Object",
        description="Objects within this group will be set as target for the modifier"
    )
    modifier_label: bpy.props.StringProperty(
        name="Name", 
        description="Modifier Label", 
        default="" 
    )

class NGX_OT_NewNodeGroup(Operator):
    bl_idname = "wm.ngx_new_node_group"
    bl_label = "New Node Group"
    bl_description = "Create a new Node Group"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ng = bpy.data.node_groups.new(context.window_manager.ngx.modifier_label, "GeometryNodeTree")
        input_node = ng.nodes.new("NodeGroupInput")
        output_node = ng.nodes.new("NodeGroupOutput")
        input_node.location = (-300, 0)
        output_node.location = (300, 0)
        ng.inputs.new("NodeSocketGeometry", "Geometry")
        ng.outputs.new("NodeSocketGeometry", "Geometry")
        ng.links.new(input_node.outputs[0], output_node.inputs[0])
        return {'FINISHED'}


class NGX_OT_multi_add_modifier(Operator):
    bl_idname = "wm.ngx_multi_add_modifier"
    bl_label = "Multi Modifier"
    bl_description = "Add Modifier to all selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    modifier_name: EnumProperty(
        items=[
            ("", "Modify", "", "", 0),
            ("DATA_TRANSFER", "Data Transfer", "Data Transfer", "MOD_DATA_TRANSFER", 1),
            ("MESH_CACHE", "Mesh Cache", "Mesh Cache", "MOD_MESHDEFORM", 2),
            ("MESH_SEQUENCE_CACHE", "Mesh Sequence Cache", "Mesh Sequence Cache", "MOD_MESHDEFORM", 3),
            ("NORMAL_EDIT", "Normal Edit", "Normal Edit", "MOD_NORMALEDIT", 4),
            ("WEIGHTED_NORMAL", "Weighted Normal", "Weighted Normal", "MOD_NORMALEDIT", 5),
            ("UV_PROJECT", "UV Project", "UV Project", "MOD_UVPROJECT", 6),
            ("UV_WARP", "UV Warp", "UV Warp", "MOD_UVPROJECT", 7),
            ("VERTEX_WEIGHT_EDIT", "Vertex Weight Edit", "Vertex Weight Edit", "MOD_VERTEX_WEIGHT", 8),
            ("VERTEX_WEIGHT_MIX", "Vertex Weight Mix", "Vertex Weight Mix", "MOD_VERTEX_WEIGHT", 9),
            ("VERTEX_WEIGHT_PROXIMITY", "Vertex Weight Proximity", "Vertex Weight Proximity", "MOD_VERTEX_WEIGHT", 10),
            ("", "Generate", "", "", 11),
            ("ARRAY", "Array", "Array", "MOD_ARRAY", 12),
            ("BEVEL", "Bevel", "Bevel", "MOD_BEVEL", 13),
            ("BOOLEAN", "Boolean", "Boolean", "MOD_BOOLEAN", 14),
            ("BUILD", "Build", "Build", "MOD_BUILD", 15),
            ("DECIMATE", "Decimate", "Decimate", "MOD_DECIM", 16),
            ("EDGE_SPLIT", "Edge Split", "Edge Split, Edge Split", "MOD_EDGESPLIT", 17),
            ("NODES", "Geometry Nodes", "Geometry Nodes", "GEOMETRY_NODES", 18),
            ("MASK", "Mask", "Mask", "MOD_MASK", 19),
            ("MIRROR", "Mirror", "Mirror", "MOD_MIRROR", 20),
            ("MULTIRES", "Multiresolution", "Multiresolution", "MOD_MULTIRES", 21),
            ("REMESH", "Remesh", "Remesh", "MOD_REMESH", 22),
            ("SCREW", "Screw", "Screw", "MOD_SCREW", 23),
            ("SOLIDIFY", "Solidify", "Solidify", "MOD_SOLIDIFY", 24),
            ("SKIN", "Skin", "Skin", "MOD_SKIN", 25),
            ("SUBSURF", "Subdivision Surface", "Subdivision Surface", "MOD_SUBSURF", 26),
            ("TRIANGULATE", "Triangulate", "Triangulate", "MOD_TRIANGULATE", 27),
            ("VOLUME_TO_MESH", "Volume to Mesh", "Volume to Mesh", "VOLUME_DATA", 28),
            ("WELD", "Weld", "Weld", "AUTOMERGE_OFF", 29),
            ("WIREFRAME", "Wireframe", "Wireframe", "MOD_WIREFRAME", 30),
            ("", "Deform", "", "", 31),
            ("ARMATURE", "Armature", "Armature", "MOD_ARMATURE", 32),
            ("CAST", "Cast", "Cast", "MOD_CAST", 33),
            ("CURVE", "Curve", "Curve", "MOD_CURVE", 34),
            ("DISPLACE", "Displace", "Displace", "MOD_DISPLACE", 35),
            ("HOOK", "Hook", "Hook", "HOOK", 36),
            ("LAPLACIANDEFORM", "Laplacian Deform", "Laplacian Deform", "MOD_LATTICE", 37),
            ("LATTICE", "Lattice", "Lattice", "MOD_LATTICE", 38),
            ("MESH_DEFORM", "Mesh Deform", "Mesh Deform", "MOD_MESHDEFORM", 39),
            ("SHRINKWRAP", "Shrinkwrap", "Shrinkwrap", "MOD_SHRINKWRAP", 40),
            ("SIMPLE_DEFORM", "Simple Deform", "Simple Deform", "MOD_SIMPLEDEFORM", 41),
            ("SMOOTH", "Smooth", "Smooth", "MOD_SMOOTH", 42),
            ("SMOOTH_CORRECTIVE", "Smooth Corrective", "Smooth Corrective", "MOD_SMOOTH", 43),
            ("LAPLACIANSMOOTH", "Laplacian Smooth", "Laplacian Smooth", "MOD_SMOOTH", 44),
            ("SURFACE_DEFORM", "Surface Deform", "Surface Deform", "MOD_MESHDEFORM", 45),
            ("WARP", "Warp", "Warp", "MOD_WARP", 46),
            ("WAVE", "Wave", "Wave", "MOD_WAVE", 47),
            ("", "Simulate", "", "", 48),
            ("CLOTH", "Cloth", "Cloth", "MOD_CLOTH", 49),
            ("COLLISION", "Collision", "Collision", "MOD_PHYSICS", 50),
            ("DYNAMIC_PAINT", "Dynamic Paint", "Dynamic Paint", "MOD_DYNAMICPAINT", 51),
            ("EXPLODE", "Explode", "Explode", "MOD_EXPLODE", 52),
            ("FLUID", "Fluid", "Fluid", "MOD_FLUIDSIM", 53),
            ("OCEAN", "Ocean", "Ocean", "MOD_OCEAN", 54),
            ("PARTICLE_INSTANCE", "Particle Instance", "Particle Instance", "MOD_PARTICLE_INSTANCE", 55),
            ("PARTICLE_SYSTEM", "Particle System", "Particle System", "MOD_PARTICLES", 56),
            ("SOFT_BODY", "Soft Body", "Soft Body", "MOD_SOFT", 57)
        ],
        name="",
        description="Select a Modifier from the list",
        default="BEVEL",
    )

    def populate_node_group_enum(self, context):
        enum_items = [(n.name, n.name, f"Select {n.name}") for n in bpy.data.node_groups]
        return enum_items

    node_group_enum: EnumProperty(
        items=populate_node_group_enum,
        name="Node Group",
        description="Select a Node Group from the list",
    )

    is_deleting: EnumProperty(
        items=[
            ("ADD", "Add", "Add", "ZOOMIN", 0),
            ("REMOVE", "Remove", "Remove", "ZOOMOUT", 1),
        ],
        name="Add / Remove",
        description="Add or Remove Modifier",
    )

    def get_objects(self, context):
        items = [(obj.name, obj.name, "") for obj in bpy.data.objects]
        items.insert(0, ("None", "None", ""))
        return items

    target_object: EnumProperty(
        items=get_objects,
        name="Target Object",
        description="Select an object"
    )

    modifier_float: FloatProperty(
        name="Distance",
        description="Distance",
        default=0.1,
        unit='LENGTH',
    )

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type in ["MESH", "CURVE"]:
                if self.is_deleting == "REMOVE":
                    for modifier in obj.modifiers:
                        if modifier.name == context.window_manager.ngx.modifier_label:
                            obj.modifiers.remove(modifier)
                            break
                else:
                    try:
                        modifier = obj.modifiers.new(context.window_manager.ngx.modifier_label, self.modifier_name)
                        if self.modifier_name == "NODES":
                            modifier.node_group = bpy.data.node_groups.get(self.node_group_enum)
                        if self.modifier_name in ["DATA_TRANSFER", "BOOLEAN", "LATTICE", "MESH_DEFORM"] and obj != context.window_manager.ngx.target_object:
                            modifier.object = context.window_manager.ngx.target_object
                        if self.modifier_name == "SCREW":
                            modifier.angle = 0
                            modifier.screw_offset = self.modifier_float
                            modifier.steps = 1
                            modifier.render_steps = 1
                        if self.modifier_name == "SOLIDIFY":
                            modifier.thickness = self.modifier_float
                        if self.modifier_name == "BEVEL":
                            modifier.width = self.modifier_float
                            modifier.segments = 1
                        if self.modifier_name == "ARRAY":
                            modifier.use_relative_offset = False
                            modifier.use_constant_offset = True
                    except Exception as e:
                        print(e)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        if bpy.context.selected_objects:
            layout.prop(self, "is_deleting", expand=True)
            if self.is_deleting == "ADD":
                layout.prop(self, "modifier_name")
            layout.prop(context.window_manager.ngx, "modifier_label")
            if self.is_deleting == "ADD":
                if self.modifier_name == "NODES":
                    if not self.node_group_enum:
                        layout.operator("wm.ngx_new_node_group")
                    else:
                        layout.prop(self, "node_group_enum")
                if self.modifier_name in ["DATA_TRANSFER", "BOOLEAN", "LATTICE", "MESH_DEFORM"]:
                    layout.prop(context.window_manager.ngx, "target_object")
                if self.modifier_name in ["BEVEL", "SOLIDIFY", "SCREW"]:
                    layout.prop(self, "modifier_float")
        else:
            layout.label(text="Select an object", icon='ERROR')


    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)



#====================================================================#


class NGX_MT_object_tools(Menu):
    bl_label = "Object"

    def draw(self, context):
        layout = self.layout
        layout.operator("wm.ngx_selected_wire_display", icon='SHADING_WIRE')
        layout.operator("wm.ngx_join_split_normals", icon='MOD_NORMALEDIT')
        layout.operator("wm.ngx_multi_add_modifier", icon='MODIFIER')

class NGX_MT_data_tools(Menu):
    bl_label = "Data"

    def draw(self, context):
        layout = self.layout
        layout.operator("wm.ngx_shapekey_to_attribute", icon='SHAPEKEY_DATA')

class NGX_MT_notion_utils(Menu):
    bl_label = "Notion"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Notion Utils", icon='EVENT_N')

#=================#

class NGX_MT_main_menu(Menu):
    bl_label = "NGx"

    def menu_draw(self, context):
        self.layout.menu("NGX_MT_main_menu")

    def draw(self, context):
        layout = self.layout
        layout.operator("wm.test_op", icon="FILE_TICK")
        layout.operator("wm.ngx_save_relative", icon='FILE_TICK')
        layout.operator("wm.ngx_reveal_in_explorer", icon='FILE_FOLDER')
        layout.operator("wm.ngx_reload_linked_libraries", icon='FILE_REFRESH')
        layout.menu("NGX_MT_object_tools", icon='OBJECT_DATA')
        layout.menu("NGX_MT_data_tools", icon='OUTLINER_DATA_MESH')
        layout.separator()
        layout.menu("NGX_MT_notion_utils", icon='EVENT_N')


#=============================================================================== REGISTRATION


classes = [
    NGX_OT_reveal_in_explorer,
    NGX_OT_selected_wire_display,
    NGX_OT_join_split_normals,
    NGX_OT_save_relative,
    NGX_OT_reload_linked_libraries,
    NGX_OT_shapekey_to_attribute,
    NGX_Properties,
    NGX_OT_NewNodeGroup,
    NGX_OT_multi_add_modifier,

    NGX_MT_object_tools,
    NGX_MT_data_tools,
    NGX_MT_notion_utils,
    NGX_MT_main_menu,
]

def register():
    from bpy.utils import register_class
    for cls in classes:
        try:
            register_class(cls)
        except Exception as e:
            print(f"Error registering {cls}")
    bpy.types.TOPBAR_MT_editor_menus.append(NGX_MT_main_menu.menu_draw)
    bpy.types.WindowManager.ngx = PointerProperty(type=NGX_Properties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.WindowManager.ngx
    bpy.types.TOPBAR_MT_editor_menus.remove(NGX_MT_main_menu.menu_draw)