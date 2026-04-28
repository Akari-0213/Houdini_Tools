import pathlib

# This code is called when instances of this SOP cook.
node = hou.pwd()
geo = node.geometry()


pictures_folder_path = pathlib.Path(node.parm('pictures_folder').eval())
create_num = node.parm('create_num').eval()

def get_image_paths(folder_path: pathlib.Path) -> list[pathlib.Path]:
    image_paths = [path for path in folder_path.iterdir() if path.name.startswith('hou_pictures') and path.suffix in ['.png', '.jpeg', '.jpg']]
    return image_paths


def get_picture_aspect(image_paths: list[pathlib.Path]) -> list[tuple[int, int]]:
    picture_aspects = []
    for image_path in image_paths:
        image_name = image_path.stem
        name_parts = image_name.split('_')
        width, height = (int(name_parts[-2]), int(name_parts[-1]))
        picture_aspects.append((width, height))
    return picture_aspects


def set_aspect(picture_aspects: list[tuple[int, int]]):
    for ptnum in range(0, create_num):
        point = geo.points()[ptnum]
        idx = ptnum % len(picture_aspects)
        width, height = picture_aspects[idx]
        point.setAttribValue("aspect", hou.Vector3(width, height, 0))


def set_filename(image_paths: list[pathlib.Path]):
    for ptnum in range (0, create_num):
        point = geo.points()[ptnum]
        idx = ptnum % len(image_paths)
        image_path = image_paths[idx]
        point.setAttribValue("filename", str(image_path))

if(pictures_folder_path.is_dir()):
    #filename設定
    image_paths = get_image_paths(pictures_folder_path)
    set_filename(image_paths)

    #aspect設定
    picture_aspects = get_picture_aspect(image_paths)
    set_aspect(picture_aspects)

    
else:
    print("フォルダを選択してください")

