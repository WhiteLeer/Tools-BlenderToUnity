import os
import re
from collections import defaultdict
from mathutils import Vector

import bpy
import json

# =================================================
bl_info = {
    "name": "My Test Plugin",
    "blender": (3, 3, 20),
    "category": "3D View"
}

# =================================================
my_size_dict = {}
tree_path = []
tree_root = None
if_sync0 = False
if_sync1 = False
now_name = ""

interp_x = 0.5
interp_y = 0.5
interp_z = 0.5


# ======================================================================================================================
# 树形结构
class TreeNode:
    def __init__(self, value):
        self.value = value
        self.children = []

    def add_child(self, node):
        self.children.append(node)


# ======================================================================================================================
# 检查 JSON 文件格式
def parse_json_to_tree(json_data):
    if not isinstance(json_data, list) or not json_data:
        raise ValueError("JSON 数据为空或无法读取")

    naming_config = json_data[0].get("title", {})
    if naming_config != "命名配置表":
        raise ValueError(f"Json 文件的第一个 title 应该是 '命名配置表',但获取到的是 '{naming_config}'")

    root = TreeNode(naming_config)
    topics = json_data[0].get("topics", [])

    build_base_tree(root, topics, "")

    if not root:
        raise ValueError(f"构建树失败，请检查错误")
    return root


# 构建树并存储字典
def build_base_tree(parent_node, topics, nowname):
    for topic in topics:
        if topic["title"] != "Bound":
            node = TreeNode(topic["title"])
            parent_node.add_child(node)

            thisname = re.sub(r'[^a-zA-Z0-9]', '', topic["title"]) + "_"
            if "topics" in topic and topic["topics"]:
                build_base_tree(node, topic["topics"], nowname+thisname)
        else:
            array0 = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
            array1 = [str(i).zfill(2) for i in range(10)]
            for value0 in array0:
                node0 = TreeNode(value0)
                parent_node.add_child(node0)
                for value1 in array1:
                    node1 = TreeNode(value1)
                    node0.add_child(node1)
                    my_size_dict[nowname+value0+"_"+value1] = topic["topics"][0].get("title", {})


# 输出树的所有路径 DFS
def dfs(node, current_path):
    if not node:
        return
    current_path.append(node.value)
    if not node.children:
        tree_path.append(list(current_path))
    else:
        for child in node.children:
            dfs(child, current_path)
    current_path.pop()


# ======================================================================================================================
# 更新显示 UI
def update_visibility(context):
    global now_name

    tool = context.scene.my_tool
    now_name = ""

    # ================================================
    # 设置显示名称
    for i in range(6):
        prop = f"prefix_{i}"
        if getattr(tool, prop) != "":
            selected_value = getattr(tool, prop)
            cleaned = re.sub(r'[^a-zA-Z0-9]', '', selected_value)
            if cleaned != "":
                now_name += cleaned + "_"

    now_name = now_name[:-1]

    # ================================================
    # 隐藏所有超过当前层级的属性
    for i in range(6):
        prop = f"prefix_{i}"
        enum_items_fn = get_dynamic_enum_items(i)
        valid_options = {item[0] for item in enum_items_fn(tool, context)}
        if "" in valid_options:
            setattr(tool, prop, "")

    context.area.tag_redraw()


# 根据动态层级获取枚举值
def get_dynamic_enum_items(level):
    def enum_items_fn(self, context):
        # ================================================
        current_node = tree_root
        for i in range(level):
            selected_value = getattr(context.scene.my_tool, f"prefix_{i}", "")
            current_node = next((child for child in current_node.children if child.value == selected_value), None)
            if not current_node:
                return []

        # ================================================
        items = [(child.value, child.value, "") for child in current_node.children]
        return items

    return enum_items_fn


# 计算下一个命名
def set_next_name(nowname):
    # 找到最后一个下划线的位置
    last_underscore_index = nowname.rfind('_')

    # 提取前缀和数字部分
    prefix = nowname[:last_underscore_index + 1]
    number_part = nowname[last_underscore_index + 1:]
    next_number = int(number_part) + 1

    # 拼接结果字符串
    next_string = f"{prefix}{next_number:02d}"

    return next_string


# ======================================================================================================================
# 确定保存路径
def create_path_from_name(obj_name, folder_type):
    path_parts = obj_name.split('_')

    # 如果名称中没有下划线，就直接使用该名称作为文件夹名称和子目录
    if len(path_parts) == 1:
        sub_dir = ''
        folder_name = obj_name
    else:
        sub_dir = os.path.join(*path_parts[:-1])
        folder_name = '_'.join(path_parts[:-1])

    full_path = os.path.join(
        sub_dir, folder_name, folder_type
    )

    if not os.path.exists(full_path):
        os.makedirs(full_path)

    return full_path


# ======================================================================================================================
# 在设置命名时是否同步
def update_judge0():
    global if_sync0

    if_sync0 = not if_sync0


# 在设置中心时是否同步
def update_judge1():
    global if_sync1

    if_sync1 = not if_sync1


# ======================================================================================================================
# 自定义属性组
class MyProperties(bpy.types.PropertyGroup):
    # ==================================================================================================================
    # 同步功能 0
    func0: bpy.props.BoolProperty(
        name="func0",
        default=False,
        update=lambda self, context: update_judge0()
    )

    # 同步功能 1
    func1: bpy.props.BoolProperty(
        name="func1",
        default=False,
        update=lambda self, context: update_judge1()
    )

    # X 插值
    interp_x: bpy.props.FloatProperty(
        name="X 插值",
        description="Interpolation factor for X axis",
        default=0.5,
        min=0.0,
        max=1.0
    )

    # Y 插值
    interp_y: bpy.props.FloatProperty(
        name="Y 插值",
        description="Interpolation factor for Y axis",
        default=0.5,
        min=0.0,
        max=1.0
    )

    # Z 插值
    interp_z: bpy.props.FloatProperty(
        name="Z 插值",
        description="Interpolation factor for Z axis",
        default=0.5,
        min=0.0,
        max=1.0
    )
    # ==================================================================================================================

    prefix_0: bpy.props.EnumProperty(
        name="Prefix-0",
        items=get_dynamic_enum_items(0),
        update=lambda self, context: update_visibility(context)
    )

    prefix_1: bpy.props.EnumProperty(
        name="Prefix-1",
        items=get_dynamic_enum_items(1),
        update=lambda self, context: update_visibility(context)
    )

    prefix_2: bpy.props.EnumProperty(
        name="Prefix-2",
        items=get_dynamic_enum_items(2),
        update=lambda self, context: update_visibility(context)
    )

    prefix_3: bpy.props.EnumProperty(
        name="Prefix-3",
        items=get_dynamic_enum_items(3),
        update=lambda self, context: update_visibility(context)
    )

    prefix_4: bpy.props.EnumProperty(
        name="Prefix-4",
        items=get_dynamic_enum_items(4),
        update=lambda self, context: update_visibility(context)
    )

    prefix_5: bpy.props.EnumProperty(
        name="Prefix-5",
        items=get_dynamic_enum_items(5),
        update=lambda self, context: update_visibility(context)
    )


# ======================================================================================================================
# 加载文件
class JsonLoader(bpy.types.Operator):
    bl_label = "加载 Json"
    bl_idname = "object.load_json"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        global tree_root, tree_path

        if not self.filepath:
            self.report({'ERROR'}, "未选中物体")
            return {'CANCELLED'}

        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                self.report({'INFO'}, "JSON 文件导入成功")

                tree_root = parse_json_to_tree(json_data)
                # dfs(tree_root, [])
                # self.report({'INFO'}, f"{tree_path}")

                update_visibility(context)

        except Exception as e:
            self.report({'ERROR'}, f"Failed to load JSON file: {e}")
            return {'CANCELLED'}

        return {'FINISHED'}

    def invoke(self, context, event):
        self.filepath = ""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


# 设置命名
class NameSetter(bpy.types.Operator):
    bl_label = "设置名字"
    bl_idname = "object.set_name"

    def execute(self, context):
        global now_name, if_sync0

        selected_objects = context.selected_objects

        if not selected_objects:
            self.report({'WARNING'}, "未选中物体")
            return {'CANCELLED'}

        # 设置同名物体
        if if_sync0:
            name_groups = defaultdict(list)
            # 遍历所有物体，获取基础名字
            for obj in bpy.data.objects:
                base_name = re.split(r'\.\d{3}', obj.name)[0]
                name_groups[base_name].append(obj)

            # 遍历选中物体，设置同名物体
            for selected_object in selected_objects:
                base_name = re.split(r'\.\d{3}', selected_object.name)[0]

                # 获取具有相同基名的所有物体
                same_base_objects = name_groups.get(base_name, [])

                nowname = now_name
                for obj in same_base_objects:
                    if obj not in selected_objects:
                        nowname = set_next_name(nowname)
                        obj.name = nowname

        # 设置选中物体
        for obj in selected_objects:
            obj.name = now_name

        return {'FINISHED'}


# 创建集合
class CollectionCreator(bpy.types.Operator):
    bl_label = "为选中物体创建集合"
    bl_idname = "object.create_collection"

    def get_unique_name(self, base_name):
        if base_name not in bpy.data.collections:
            return base_name
        counter = 1
        while f"{base_name}_V{counter}" in bpy.data.collections:
            counter += 1
        return f"{base_name}_V{counter}"

    def execute(self, context):
        global now_name

        tool = context.scene.my_tool
        prop = f"prefix_{0}"
        basename = getattr(tool, prop) + "_" + now_name
        unique_name = self.get_unique_name(basename)

        # 创建指定名称的集合
        collection = bpy.data.collections.new(unique_name)
        context.scene.collection.children.link(collection)

        # 将选中的所有对象移动到新集合中
        for obj in context.selected_objects:
            for parent_collection in obj.users_collection:
                parent_collection.objects.unlink(obj)
            collection.objects.link(obj)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


# 设置中心
class CenterSetter(bpy.types.Operator):
    bl_label = "设置选中物体中心"
    bl_idname = "object.set_center"

    def execute(self, context):
        # 初始化
        props = context.scene.my_tool

        my_interp_x = props.interp_x
        my_interp_y = props.interp_y
        my_interp_z = props.interp_z

        selected_objects = context.selected_objects

        if not selected_objects:
            self.report({'WARNING'}, "未选中物体")
            return {'CANCELLED'}

        if len(selected_objects) != 1:
            self.report({'WARNING'}, "只能选中一个物体")
            return {'CANCELLED'}

        selected_object = selected_objects[0]

        # 计算偏移量
        bbox_corners = []
        for corner in selected_object.bound_box:
            corner = selected_object.matrix_world @ Vector(corner)
            bbox_corners.append(corner)

        min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
        max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')

        for corner in bbox_corners:
            min_x, min_y, min_z = min(min_x, corner.x), min(min_y, corner.y), min(min_z, corner.z)
            max_x, max_y, max_z = max(max_x, corner.x), max(max_y, corner.y), max(max_z, corner.z)

        center_x = min_x + my_interp_x * (max_x - min_x)
        center_y = min_y + my_interp_y * (max_y - min_y)
        center_z = min_z + my_interp_z * (max_z - min_z)

        new_origin = Vector((center_x, center_y, center_z))
        world_offset_base = new_origin - selected_object.location

        # 设置同名物体
        global if_sync1
        if if_sync1:
            name_groups = defaultdict(list)
            # 遍历所有物体，获取基础名字
            for obj in bpy.data.objects:
                base_name = re.split(r'\.\d{3}', obj.name)[0]
                name_groups[base_name].append(obj)

            # 获取具有相同基名的所有物体
            this_name = re.split(r'\.\d{3}', selected_object.name)[0]
            same_base_objects = name_groups.get(this_name, [])

            for same_obj in same_base_objects:
                if same_obj != selected_object:
                    bpy.context.scene.cursor.location = same_obj.location + world_offset_base

                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.context.view_layer.objects.active = same_obj
                    same_obj.select_set(True)

                    # 设置原点
                    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

        # 设置选中物体
        bpy.context.scene.cursor.location = selected_object.location + world_offset_base

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = selected_object
        selected_object.select_set(True)

        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

        return {'FINISHED'}


# 导出物体
class FbxOutput(bpy.types.Operator):
    bl_label = "选择 Unity 项目文件夹"
    bl_idname = "object.output_fbx"

    filepath: bpy.props.StringProperty(subtype="DIR_PATH")
    export_dirpath = None

    def execute(self, context):
        global tree_root

        # 错误检查
        if not tree_root:
            self.report({'ERROR'}, "未选择 JSON 文件")
            return {'CANCELLED'}

        if not self.filepath and not FbxOutput.export_dirpath:
            self.report({'ERROR'}, "导出路径错误")
            return {'CANCELLED'}

        # 存储路径
        if self.filepath:
            FbxOutput.export_dirpath = self.filepath

        # 获取真名
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'ERROR'}, "未选中物体")
            return {'CANCELLED'}

        # 打印合法名称
        names = []
        for child in tree_root.children:
            self.list_all_paths(child, "", names)
        # self.report({'INFO'}, f"{names}")

        # 设置全局单位
        bpy.context.scene.unit_settings.length_unit = 'METERS'
        bpy.context.scene.unit_settings.scale_length = 0.5

        # 遍历导出物体
        for obj in selected_objects:
            obj_name = obj.name

            # 是否合法
            this_name = obj_name.split('.')[0]
            if (this_name not in names) or (len(obj_name) == 0):
                self.report({'ERROR'}, f"物体名称非法: {this_name}")
                continue

            prefix = FbxOutput.export_dirpath + "Assets\Art\MapSources\Architecture\XSJArtEditorTools\胡家豪\\"
            export_filepath = prefix + create_path_from_name(obj_name, "Fbx")
            if not os.path.exists(export_filepath):
                os.makedirs(export_filepath)

            base_name = re.split(r'\.\d{3}', obj_name)[0]
            export_filepath = os.path.join(export_filepath, f"{base_name}.fbx")

            # 创建副本导出
            obj_copy = obj.copy()
            obj_copy.data = obj.data.copy()
            context.collection.objects.link(obj_copy)

            bpy.ops.object.select_all(action='DESELECT')
            obj_copy.select_set(True)
            context.view_layer.objects.active = obj_copy

            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

            bpy.ops.export_scene.fbx(
                filepath=export_filepath,
                use_selection=True,
                apply_unit_scale=True,
                use_space_transform=True,
                bake_space_transform=True,
                global_scale=1
            )

            # 删除副本
            bpy.data.objects.remove(obj_copy, do_unlink=True)

        self.report({'INFO'}, f"物体成功导出到: {FbxOutput.export_dirpath}")
        return {'FINISHED'}

    def list_all_paths(self, node, nowname, names):
        if node is None or node.value == "Bound":
            return None

        # 过滤中文和下划线
        pattern = re.compile(r'[^\u4e00-\u9fff_]+')
        matches = pattern.findall(node.value)
        result = ''.join(matches)

        for child in node.children:
            content = nowname
            if len(content) != 0:
                content += '_'
            content += result
            self.list_all_paths(child, content, names)

        if len(node.children) == 0 and result != "":
            names.append(nowname + "_" + result)

    def invoke(self, context, event):
        if FbxOutput.export_dirpath:
            return self.execute(context)

        self.filepath = ""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


# 导出 Json
class JsonCreator(bpy.types.Operator):
    bl_label = "选择 Unity 项目文件夹"
    bl_idname = "object.output_json"

    filepath: bpy.props.StringProperty(subtype="DIR_PATH")
    export_dirpath = None

    def execute(self, context):
        # 错误检查
        if not self.filepath and not JsonCreator.export_dirpath:
            self.report({'ERROR'}, "No directory selected.")
            return {'CANCELLED'}

        # 存储路径
        if self.filepath:
            JsonCreator.export_dirpath = self.filepath

        # 根据集合名设置路径
        nowcollection = bpy.context.collection
        prefix = JsonCreator.export_dirpath + "Assets\Art\MapSources\Architecture\XSJArtEditorTools\胡家豪\\"
        export_filepath = prefix + nowcollection.name + "\Json"
        if not os.path.exists(export_filepath):
            os.makedirs(export_filepath)

        # 根据
        main_objects = []
        other_objects = []
        for obj in nowcollection.objects:
            if 'Kit' in obj.name or "Adorn" in obj.name:
                other_objects.append(obj)
            else:
                main_objects.append(obj)

        # 合并并导出主体物体
        bpy.ops.object.select_all(action='DESELECT')
        object_copies = []

        for obj in main_objects:
            obj_copy = obj.copy()
            obj_copy.data = obj_copy.data.copy()
            bpy.context.collection.objects.link(obj_copy)
            object_copies.append(obj_copy)

        for obj_copy in object_copies:
            obj_copy.select_set(True)

        bpy.context.view_layer.objects.active = object_copies[-1]

        bpy.ops.object.join()
        merged_object = bpy.context.view_layer.objects.active

        base_export_filepath = os.path.join(export_filepath, f"{nowcollection.name}.fbx")

        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

        bpy.ops.export_scene.fbx(
            filepath=base_export_filepath,
            use_selection=True,
            apply_unit_scale=True,
            use_space_transform=True,
            bake_space_transform=True,
            global_scale=1
        )

        main_location = merged_object.location
        bpy.data.objects.remove(merged_object, do_unlink=True)

        # 生成集合内部物体的基础 Json 信息
        base_export_filepath = os.path.join(export_filepath, f"{nowcollection.name}.json")
        my_scale = bpy.context.scene.unit_settings.scale_length
        base_structures = {"items": []}
        for obj in other_objects:
            structure = {"name": f"{obj.name}", "data": []}
            structure["data"].append({"location": f"{(obj.location - main_location) * my_scale}"})
            structure["data"].append({"euler": f"{obj.rotation_euler}"})
            structure["data"].append({"scale": f"{obj.scale}"})
            base_structures["items"].append(structure)

        with open(base_export_filepath, 'w', encoding='utf-8') as json_file:
            json.dump(base_structures, json_file, ensure_ascii=False, indent=2)

        # 生成所有物体的大小 Json 信息
        size_export_filepath = os.path.join(prefix, "my_size_json.json")
        size_structures = {"items": []}
        for key, value in my_size_dict.items():
            structure = {"name": f"{key}", "size": value}
            size_structures["items"].append(structure)

        with open(size_export_filepath, 'w', encoding='utf-8') as json_file:
            json.dump(size_structures, json_file, ensure_ascii=False, indent=2)

        self.report({'INFO'}, f"物体成功导出到: {JsonCreator.export_dirpath}")
        return {'FINISHED'}

    def invoke(self, context, event):
        if JsonCreator.export_dirpath:
            return self.execute(context)

        self.filepath = ""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


# ======================================================================================================================
# 根据解析的 JSON 数据命名
class PanelName(bpy.types.Panel):
    bl_label = "物体命名"
    bl_idname = "OBJECT_PT_set_name"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MyTool'

    def draw(self, context):
        global now_name

        # 初始化
        tool = context.scene.my_tool
        layout = self.layout
        box = layout.box()

        # 导入 JSON 文件
        row = box.row()
        row.operator("object.load_json", text="导入 JSON 文件")

        # 同步功能 0
        row = box.row()
        row.prop(tool, "func0", text="同步所有同名物体")

        # 动态 UI 界面
        for i in range(6):
            prop = f"prefix_{i}"
            value = getattr(tool, prop, "")
            if value != "":
                row = box.row()
                row.prop(tool, prop, text=f"前缀-{i}")

        # 当前命名
        row = box.row()
        row.label(text="当前命名: " + now_name)

        # 设置命名
        row = box.row()
        row.operator("object.set_name", text="命名")

        # 创建集合
        row = box.row()
        row.operator("object.create_collection", text="创建集合")

        # 分隔线
        layout.separator()


# 设置选中物体的中心点
class PanelCenter(bpy.types.Panel):
    bl_label = "中心设置"
    bl_idname = "OBJECT_PT_set_center"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MyTool'

    def draw(self, context):
        global now_name

        # 初始化
        tool = context.scene.my_tool
        layout = self.layout
        box = layout.box()

        # 插值
        row = box.row()
        row.prop(tool, "interp_x", slider=True)
        row = box.row()
        row.prop(tool, "interp_y", slider=True)
        row = box.row()
        row.prop(tool, "interp_z", slider=True)

        # 同步功能 1
        row = box.row()
        row.prop(tool, "func1", text="同步所有同名物体")

        # 设置中心
        row = box.row()
        row.operator("object.set_center", text="设置中心")

        # 分隔线
        layout.separator()


# 设置导出
class PanelOutput(bpy.types.Panel):
    bl_label = "导出设置"
    bl_idname = "OBJECT_PT_output"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MyTool'

    def draw(self, context):
        # 初始化
        layout = self.layout
        box = layout.box()

        # 导出 JSON
        row = box.row()
        row.operator("object.output_json", text="创建 JSON")

        # 导出物体
        row = box.row()
        row.operator("object.output_fbx", text="导出为 FBX")


# ======================================================================================================================
def register():
    bpy.utils.register_class(MyProperties)
    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=MyProperties)

    # =======================================
    bpy.utils.register_class(PanelName)
    bpy.utils.register_class(PanelCenter)
    bpy.utils.register_class(PanelOutput)

    # =======================================
    bpy.utils.register_class(JsonLoader)
    bpy.utils.register_class(NameSetter)
    bpy.utils.register_class(CollectionCreator)

    bpy.utils.register_class(CenterSetter)

    bpy.utils.register_class(JsonCreator)
    bpy.utils.register_class(FbxOutput)


def unregister():
    bpy.utils.unregister_class(MyProperties)
    del bpy.types.Scene.my_tool

    # =======================================
    bpy.utils.unregister_class(PanelName)
    bpy.utils.unregister_class(PanelCenter)
    bpy.utils.unregister_class(PanelOutput)

    # =======================================
    bpy.utils.unregister_class(JsonLoader)
    bpy.utils.unregister_class(NameSetter)
    bpy.utils.unregister_class(CollectionCreator)

    bpy.utils.unregister_class(CenterSetter)

    bpy.utils.unregister_class(JsonCreator)
    bpy.utils.unregister_class(FbxOutput)


if __name__ == "__main__":
    register()
