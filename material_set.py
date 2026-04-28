from PySide6 import QtWidgets, QtCore
import pathlib
import re
import voptoolutils


def clicked_create_mtbuilder_button(mt_library: str, mt_name: str, texture_paths: dict) -> None:
    print("create_mtbuilderが押されました")
    material_library_path = mt_library

    if not material_library_path:
        print("Material Library のパスを入力してください")
        return
    if not mt_name:
        print("Material Nameを記入してださい")
        return
    
    mt_lib_node = hou.node(material_library_path)
    if mt_lib_node is None:
        print(f"ノードが見つかりません。{material_library_path}")
        return

    try:
        mask = voptoolutils.KARMAMTLX_TAB_MASK
        mtl_builder = voptoolutils._setupMtlXBuilderSubnet(
            destination_node = mt_lib_node,
            name = mt_name,
            mask = mask,
            folder_label="Karma Material Builder"
        )
    except Exception as e:
        print(f"ノードの作成に失敗しました: {e}")
    
    mapping = {
        "base_color": texture_paths.get("basecolor"),
        "diffuse_roughness": texture_paths.get("roughness"),
        "normal": texture_paths.get("normal")
        }
    material_path = f"{material_library_path}/{mt_name}"
    material_node = hou.node(material_path)

    for input_name, new_path in mapping.items():
        if not new_path:
            continue
        image_node = create_image_node(material_node, input_name)
        if image_node:
            image_node.parm('file').set(new_path)
            print(f"{input_name}テクスチャを追加しました:{new_path}")
        else:
            print(f"{input_name}テクスチャを追加されませんでした")

    # マテリアルライブラリにパス追加
    set_materiallibrary_path(mt_lib_node, mt_name)


def clicked_change_texture_button(mt_library: str, mt_name: str, texture_paths: dict) -> None:
    print("change_textureが押されました")
    material_library_path = mt_library
    if not material_library_path:
        print("Material Library のパスを入力してください")
        return
    if not mt_name:
        print("Material Nameを記入してださい")
        return

    material_path = f"{material_library_path}/{mt_name}"
    material_node = hou.node(material_path)
    if material_node is None:
        print(f"ノードが見つかりません。{material_library_path}")
        return
    print("ありました")

    mapping = {
        "base_color": texture_paths.get("basecolor"),
        "diffuse_roughness": texture_paths.get("roughness"),
        "normal": texture_paths.get("normal")
    }
    for input_name, new_path in mapping.items():
        if not new_path:
            continue
        image_node = get_image_node(material_node, input_name)
        if image_node:
            image_node.parm('file').set(new_path)
            print(f"{input_name}テクスチャを変更しました:{new_path}")
        else:
            print(f"{input_name}接続先が見つかりませんでした。")


def get_image_node(material_node: any, input_name: str) -> any:
    surface_shader = None
    for child in material_node.children():
        if child.type().name() == "mtlxstandard_surface":
            surface_shader = child
            break
    if not surface_shader:
        print("mtlxstandard_surface shaderが見つかりませんでした")
        return

    input_index = surface_shader.inputIndex(input_name)
    if input_index < 0:
        return None
    
    connected_node = surface_shader.input(input_index)
    if not connected_node:
        return None

    if connected_node.type().name() == "mtlximage":
        return connected_node


def create_image_node(material_node: any, input_name: str) -> any:
    surface_shader = None
    for child in material_node.children():
        if child.type().name() == "mtlxstandard_surface":
            surface_shader = child
            break
    if not surface_shader:
        print("mtlxstandard_surface shaderが見つかりませんでした")
        return None
    
    image_node = material_node.createNode("mtlximage", f"image_{input_name}")
    input_index = surface_shader.inputIndex(input_name)

    if input_index < 0:
        print(f"{input_name}の入力インデックスが見つかりませんでした。")
        return None
    
    surface_shader.setInput(input_index, image_node, 0)
    image_node.moveToGoodPosition()

    return image_node


def set_materiallibrary_path(mt_lib_node: any, mt_name: str) -> None:
    num_material_parm = mt_lib_node.parm("materials")
    current_count = num_material_parm.eval()
    new_count = current_count + 1
    num_material_parm.set(new_count)
    mt_lib_node.parm(f"matnode{new_count}").set(mt_name)
    mt_lib_node.parm(f"matpath{new_count}").set(mt_name)


class map_select(QtWidgets.QHBoxLayout):
    def __init__(self, map_name: str) -> None:
        super().__init__()
        self.map_name = map_name
        label = QtWidgets.QLabel(f"{self.map_name}")
        self.map_line = QtWidgets.QLineEdit()
        file_select_button = QtWidgets.QPushButton("ファイル選択")
        file_select_button.clicked.connect(self.clicked_file_select)
        self.addWidget(label)
        self.addWidget(self.map_line)
        self.addWidget(file_select_button)
        
    def clicked_file_select(self) -> None:
        print("file select button clicked")
    
    def get_texture_path(self) -> any:
        map_path = self.map_line.text()
        if map_path.startswith("file:///"):
            new_map_path = re.split('file:///', map_path)[1]
            map_path = new_map_path
        return map_path


def settings_spinbox() -> any:
    doublespinbox = QtWidgets.QDoubleSpinBox()
    doublespinbox.setMinimum(0.0)
    doublespinbox.setMaximum(1.0)
    doublespinbox.setDecimals(2)
    return doublespinbox 

# ダイアログの作成
dialog = QtWidgets.QWidget()
dialog.setGeometry(150, 150, 500, 300)

# 作ったダイアログとHoudiniウィンドウの間に親子関係をつくる。
dialog.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)
layout = QtWidgets.QVBoxLayout()

mt_library_layout = QtWidgets.QHBoxLayout()
library_label = QtWidgets.QLabel("MaterialLibrary Node Path")
mt_library_path_line = QtWidgets.QLineEdit()
mt_library_layout.addWidget(library_label)
mt_library_layout.addWidget(mt_library_path_line)

material_name_layout = QtWidgets.QHBoxLayout()
material_label = QtWidgets.QLabel("Material Name")
material_name_line = QtWidgets.QLineEdit()
material_name_layout.addWidget(material_label)
material_name_layout.addWidget(material_name_line)

basecolor_layout = map_select("Basecolor:")
normal_layout = map_select("Normal:")
roughness_layout = map_select("Roughness:")
texure_settings_group = QtWidgets.QGroupBox("テクスチャ設定")
texture_layout = QtWidgets.QVBoxLayout()
texture_layout.addLayout(basecolor_layout)
texture_layout.addLayout(normal_layout)
texture_layout.addLayout(roughness_layout)
texure_settings_group.setLayout(texture_layout)

pbr_setting_group = QtWidgets.QGroupBox("その他設定")
param_layout = QtWidgets.QGridLayout()
param_layout.addWidget(QtWidgets.QLabel("Specular:"), 0, 0)
specular_doublespinbox = settings_spinbox()
param_layout.addWidget(specular_doublespinbox, 0, 1)
param_layout.addWidget(QtWidgets.QLabel("Metalness:"), 1, 0)
metal_doublespinbox = settings_spinbox()
param_layout.addWidget(metal_doublespinbox, 1, 1)
pbr_setting_group.setLayout(param_layout)

button_layout = QtWidgets.QHBoxLayout()
create_mt_button = QtWidgets.QPushButton("Create New Material")
create_mt_button.clicked.connect(lambda: clicked_create_mtbuilder_button(
    mt_library_path_line.text(),
    material_name_line.text(),
    {
        "basecolor": basecolor_layout.get_texture_path(),
        "normal": normal_layout.get_texture_path(),
        "roughness": roughness_layout.get_texture_path()
    }
    ))
change_texture_button = QtWidgets.QPushButton("Change Material Texture")
change_texture_button.clicked.connect(lambda: clicked_change_texture_button(
    mt_library_path_line.text(), 
    material_name_line.text(),
    {
        "basecolor": basecolor_layout.get_texture_path(),
        "normal": normal_layout.get_texture_path(),
        "roughness": roughness_layout.get_texture_path()
    }
    ))
button_layout.addWidget(create_mt_button)
button_layout.addWidget(change_texture_button)

layout.addLayout(mt_library_layout)
layout.addLayout(material_name_layout)
layout.addWidget(texure_settings_group)
layout.addWidget(pbr_setting_group)
layout.addLayout(button_layout)



dialog.setLayout(layout)
# ダイアログの表示
dialog.show()
