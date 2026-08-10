from PySide6 import QtWidgets, QtCore
import re
import pathlib
import json

SETTINGS_PATH= pathlib.Path(r"C:\\Houdini\\houdini_scripts\\fbx_importer\\fbximporter_settings.json")


def delete_item(fbx_list :any) -> None:
    selected_node = hou.selectedNodes()[0].path()
    if not selected_node:
        print("shelf_dopノードが選択されていません")
        return

    current_item = fbx_list.currentItem()
    if not current_item:
        print("削除するアイテムが選択されていません")
        return
    full_path = current_item.data(QtCore.Qt.UserRole)
    
    file_name = current_item.text()
    target_node_path = f"{selected_node}/{file_name}"
    target_node = hou.node(target_node_path)
    if target_node:
        target_node.destroy()
        print(f"ノードを削除しました: {target_node_path}")
    else:
        print(f"削除対象のノードが見つかりませんでした: {target_node_path}")
        return
    
    settings = load_setting()
    if full_path in settings:
        del settings[full_path]
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as file:
                json.dump(settings, file, indent=4, ensure_ascii=False)
            print(f"jsonから削除しました: {full_path}")
        except Exception as e:
            print(f"設定ファイルの更新に失敗しました: {e}")
    
    row = fbx_list.row(current_item)
    fbx_list.takeItem(row)

    assign_id_wrangle_node = hou.node(f"{selected_node}/attribwrangle_assign_id")
    if assign_id_wrangle_node:
        all_weights = create_weight_str()
        set_weight_to_wrangle(assign_id_wrangle_node, all_weights)


def update_node(file_path: str, scale_param: float, rotation: tuple[float, float, float], maxstack_num: int, weight: int) -> None:
    selected_node = hou.selectedNodes()[0].path()
    if not selected_node:
        print("shelf_dopノードが選択されていません")
        return
    file_name: str = pathlib.Path(file_path).name
    settings = load_setting()
    if file_path not in settings:
        print(f"{file_path}は追加されていません")
        return
    save_json(file_path, scale_param, rotation, maxstack_num, weight)
    all_weights = create_weight_str()
    file_node = hou.node(f"{selected_node}/{file_name}/file1")
    trans_node = hou.node(f"{selected_node}/{file_name}/transform1")
    wrangle_node = hou.node(f"{selected_node}/{file_name}/attribwrangle1")
    assign_id_wrangle_node = hou.node(f"{selected_node}/attribwrangle_assign_id")
    
    if file_path.startswith("file:///"):
        new_file_path = re.split("file:///", file_path)[1]
        file_path = new_file_path
        
    file_node.parm("file").set(file_path)
    trans_node.parm("scale").set(scale_param)
    
    rx, ry, rz = rotation
    trans_node.parm("rx").set(rx)
    trans_node.parm("ry").set(ry)
    trans_node.parm("rz").set(rz)
    
    wrangle_node.parm("snippet").set(
        f"""
        i@stack_num = {maxstack_num};
        """)
    
    set_weight_to_wrangle(assign_id_wrangle_node, all_weights)


def create_file_node(fbx_list: any, file_path: str, scale_param: float, rotation: tuple[float, float, float], maxstack_num: int, weight: int) -> None:
    shelf_geometry_node = hou.selectedNodes()[0]
    if not shelf_geometry_node:
        print("shelf_dopノードが選択されていません")
        return

    file_name: str = pathlib.Path(file_path).name
    settings = load_setting()
    if file_path in settings:
        print(f"すでに{file_path}は存在しています")
        return
    
    save_json(file_path, scale_param, rotation, maxstack_num, weight)
    all_weights = create_weight_str()
    set_list(fbx_list, file_name, file_path)

    subnet_node = shelf_geometry_node.createNode("subnet", f"{file_name}")
    new_file_node = subnet_node.createNode("file")
    trans_node = subnet_node.createNode("xform")
    matchsize_node = subnet_node.createNode("matchsize")
    pack_node = subnet_node.createNode("pack")
    wrangle_node = subnet_node.createNode("attribwrangle")
    output_node = subnet_node.createNode("output")
    assign_id_wrangle_node = hou.node(f"{shelf_geometry_node.path()}/attribwrangle_assign_id")

    trans_node.setInput(0, new_file_node)
    matchsize_node.setInput(0, trans_node)
    pack_node.setInput(0, matchsize_node)
    wrangle_node.setInput(0, pack_node)
    output_node.setInput(0, wrangle_node)

    if file_path.startswith("file:///"):
        new_file_path = re.split("file:///", file_path)[1]
        file_path = new_file_path
        
    new_file_node.parm("file").set(file_path)
    trans_node.parm("scale").set(scale_param)
    
    rx, ry, rz = rotation
    trans_node.parm("rx").set(rx)
    trans_node.parm("ry").set(ry)
    trans_node.parm("rz").set(rz)
    
    matchsize_node.parm("justify_y").set("min")
    wrangle_node.parm("class").set(1)
    wrangle_node.parm("snippet").set(
        f"""
        i@stack_num = {maxstack_num};
        """)
        
    set_weight_to_wrangle(assign_id_wrangle_node, all_weights)
    
    print(f"ファイルが追加されました{file_name}")
    merge_node = hou.node(f"{shelf_geometry_node.path()}/merge_fbx")
    new_file_node_inputtednum = len(merge_node.inputs())
    merge_node.setInput(new_file_node_inputtednum, subnet_node)


def set_weight_to_wrangle(assign_id_wrangle_node: any, all_weights: str):
    assign_id_wrangle_node.parm("snippet").set(
        f"""
float weights[] = {{{all_weights}
}}; 
float total_w = 0;
foreach(float w; weights){{
    total_w += w;
}}


//重み間での自動生成
float r = rand(@ptnum + chi("seed")) * total_w;
float num = 0;
i@fbx_id = 0;
// 累積判定のループ
for(int i = 0; i < len(weights); i++){{
    num += weights[i];
    if(r < num){{
        i@fbx_id = i;
        break;
    }}
}}
""")


def save_json(file_path: pathlib.Path, scale_param: float, rotation: tuple[float, float, float], maxstack_num: int, weight: int) -> None:
    settings = load_setting()
    if file_path not in settings:
        settings[file_path] = {}
        
    rx, ry, rz = rotation
    settings[file_path]["scale"] = scale_param
    settings[file_path]["rx"] = rx
    settings[file_path]["ry"] = ry
    settings[file_path]["rz"] = rz
    settings[file_path]["maxstack_num"] = maxstack_num
    settings[file_path]["weight"] = weight
    
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as file:
            json.dump(settings, file, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"設定ファイルの保存に失敗しました: {e}")


def load_setting() -> dict[str, dict[str, any]]:
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as file:
                file_data: dict[str, dict[str, any]] = json.load(file)
                return file_data
        except Exception as e:
            print("設定ファイル読み込みエラー:", e)
    return {}

def create_weight_str() -> str:
    settings = load_setting()
    weights = [str(data.get("weight")) for data in settings.values()]
    return ", ".join(weights)

    
def settings_spinbox(init_num: float, maximun: float, decimals: int, step_num: any) -> QtWidgets.QDoubleSpinBox:
    double_spinbox =  QtWidgets.QDoubleSpinBox()
    double_spinbox.setValue(init_num)
    double_spinbox.setMinimum(0.0)
    double_spinbox.setMaximum(maximun)
    double_spinbox.setDecimals(decimals)
    double_spinbox.setSingleStep(step_num)
    return double_spinbox


def set_list(fbx_list: any, file_name: str, file_path: str) -> None:
    new_item = QtWidgets.QListWidgetItem(f"{file_name}")
    new_item.setData(QtCore.Qt.UserRole, file_path)
    fbx_list.insertItem(0, new_item)
    fbx_list.setCurrentItem(new_item)


def on_selected_Item(fbx_list: QtWidgets.QListWidget, path_line: QtWidgets.QLineEdit, 
                     scale_spinbox: QtWidgets.QDoubleSpinBox, 
                     rotate_x_spinbox: QtWidgets.QDoubleSpinBox, 
                     rotate_y_spinbox: QtWidgets.QDoubleSpinBox, 
                     rotate_z_spinbox: QtWidgets.QDoubleSpinBox, 
                     stacknum_spinbox: QtWidgets.QDoubleSpinBox,
                     weight_spinbox: QtWidgets.QDoubleSpinBox):
    settings = load_setting()
    current_item = fbx_list.currentItem()
    if current_item is None:
        return
    
    full_path = current_item.data(QtCore.Qt.UserRole)
    path_line.setText(full_path)
    current_item_setting: dict[str, any] = settings.get(full_path, {})
    print(f"アイテムが選択されました。{current_item_setting}")
    
    item_scale = current_item_setting.get('scale', 1.0)
    item_rx = current_item_setting.get('rx', 0.0)
    item_ry = current_item_setting.get('ry', 0.0)
    item_rz = current_item_setting.get('rz', 0.0)
    item_stacknum = current_item_setting.get('maxstack_num', 1)
    item_weight = current_item_setting.get('weight', 1)
    
    scale_spinbox.setValue(item_scale)
    rotate_x_spinbox.setValue(item_rx)
    rotate_y_spinbox.setValue(item_ry)
    rotate_z_spinbox.setValue(item_rz)
    stacknum_spinbox.setValue(item_stacknum)
    weight_spinbox.setValue(item_weight)

class mainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.fbx_path_line = QtWidgets.QLineEdit()
        self.scale_spinbox = settings_spinbox(0.0, 5.0, 3, 0.01)
        self.rotate_x_spinbox = settings_spinbox(0.0, 360, 1, 1.0)
        x_css = '''
        border: 2px solid hsv(0, 90, 100);
        '''
        self.rotate_x_spinbox.setStyleSheet(x_css)
        self.rotate_y_spinbox = settings_spinbox(0.0, 360, 1, 1.0)
        y_css = '''
        border: 2px solid hsv(120, 90, 80);
        '''
        self.rotate_y_spinbox.setStyleSheet(y_css)
        self.rotate_z_spinbox = settings_spinbox(0.0, 360, 1, 1.0)
        z_css = '''
        border: 2px solid hsv(220, 90, 100);
        '''
        self.rotate_z_spinbox.setStyleSheet(z_css)
        self.stacknum_spinbox = settings_spinbox(1.0, 10, 0, 1)
        self.weight_spinbox = settings_spinbox(1.0, 100, 0, 1)
        self.fbx_list = QtWidgets.QListWidget()

        import_layout = self.set_import_layout()
        list_layout = self.set_list_layout()

        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(import_layout, 3)
        layout.addLayout(list_layout, 1)
        self.setLayout(layout)
    
    def get_rotation(self) -> tuple[float, float, float]:
        return (
            self.rotate_x_spinbox.value(),
            self.rotate_y_spinbox.value(),
            self.rotate_z_spinbox.value()
        )
    
    def set_import_layout(self) -> QtWidgets.QVBoxLayout:
        import_layout = QtWidgets.QVBoxLayout()
        fbx_layout = QtWidgets.QHBoxLayout()
        fbx_label = QtWidgets.QLabel("fbx_filepath")
        file_clear_button = QtWidgets.QPushButton("クリア")
        select_file_button = QtWidgets.QPushButton("ファイル選択")
        file_clear_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        select_file_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        file_clear_button.clicked.connect(self.clicked_clear)
        select_file_button.clicked.connect(self.select_file)
        fbx_layout.addWidget(fbx_label)
        fbx_layout.addWidget(self.fbx_path_line)
        fbx_layout.addWidget(file_clear_button)
        fbx_layout.addWidget(select_file_button)
        import_layout.addLayout(fbx_layout)

        settings_group = QtWidgets.QGroupBox("設定")
        param_layout = QtWidgets.QGridLayout()
        param_layout.addWidget(QtWidgets.QLabel("Scale"), 0, 0)
        param_layout.addWidget(self.scale_spinbox, 0, 1)
        
        param_layout.addWidget(QtWidgets.QLabel("Rotate"), 1, 0)
        param_layout.addWidget(self.rotate_x_spinbox, 1, 1)
        param_layout.addWidget(self.rotate_y_spinbox, 1, 2)
        param_layout.addWidget(self.rotate_z_spinbox, 1, 3)
        
        param_layout.addWidget(QtWidgets.QLabel("MaxStackNum"), 2, 0)
        param_layout.addWidget(self.stacknum_spinbox, 2, 1)
        
        param_layout.addWidget(QtWidgets.QLabel("Appearance_Weight"), 4, 0)
        param_layout.addWidget(self.weight_spinbox, 4, 1)
        
        settings_group.setLayout(param_layout)
        import_layout.addWidget(settings_group)
        button_layout = self.set_button_layout() 
        import_layout.addLayout(button_layout)
        return import_layout

    def set_list_layout(self) -> QtWidgets.QVBoxLayout:
        list_layout = QtWidgets.QVBoxLayout()
        list_label = QtWidgets.QLabel("FBX List")
        list_layout.addWidget(list_label)
        
        settings = load_setting()
        for full_path in reversed(list(settings.keys())):
            file_name = pathlib.Path(full_path).name
            item = QtWidgets.QListWidgetItem(file_name)
            item.setData(QtCore.Qt.UserRole, full_path) # フルパスを裏データとして保存
            self.fbx_list.addItem(item)
            
        self.fbx_list.itemClicked.connect(lambda: on_selected_Item(
            self.fbx_list, self.fbx_path_line, 
            self.scale_spinbox, 
            self.rotate_x_spinbox, self.rotate_y_spinbox, self.rotate_z_spinbox,
            self.stacknum_spinbox, self.weight_spinbox))
            
        list_layout.addWidget(self.fbx_list)
        delete_button = QtWidgets.QPushButton("アイテム削除")
        delete_button.clicked.connect(lambda: delete_item(self.fbx_list))
        list_layout.addWidget(delete_button)
        return list_layout
    
    def set_button_layout(self) -> QtWidgets.QHBoxLayout:
        button_layout = QtWidgets.QHBoxLayout()
        add_button = QtWidgets.QPushButton("FBX追加")
        add_button.clicked.connect(lambda: create_file_node(
            self.fbx_list, self.fbx_path_line.text(), 
            self.scale_spinbox.value(),
            self.get_rotation(), 
            int(self.stacknum_spinbox.value()),
            int(self.weight_spinbox.value())))
        button_layout.addWidget(add_button)
        
        update_button = QtWidgets.QPushButton("パラメータ更新")
        update_button.clicked.connect(lambda: update_node(
            self.fbx_path_line.text(), 
            self.scale_spinbox.value(), 
            self.get_rotation(),
            int(self.stacknum_spinbox.value()), 
            int(self.weight_spinbox.value())))
        button_layout.addWidget(update_button)
        return button_layout

    def clicked_clear(self):
        self.fbx_path_line.clear()

    def select_file(self):
        selected_file, _ = QtWidgets.QFileDialog.getOpenFileName(self, "ファイルを選択してください。")
        if selected_file:
            self.fbx_path_line.setText(selected_file)

dialog = mainWindow()
dialog.setGeometry(150, 150, 500, 300)
dialog.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)
dialog.show()
