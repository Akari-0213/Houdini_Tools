import subprocess
import pathlib
import re



Blender_PATH = pathlib.Path(r'c:\Program Files\Blender Foundation\Blender 4.3\blender.exe')
blender_import_usd_path = pathlib.Path(r'C:\Houdini\houdini_scripts\blender_export\blender_import_usd.py')


def main() -> None:


    usd_file = hou.parm('/stage/usd_rop1/lopoutput').eval()
    usd_file_path = pathlib.Path(usd_file)
    new_file_suffix = re.split(':', usd_file_path.suffix)[0]

    new_usd_file_path = usd_file_path.parent/f"{usd_file_path.stem}{new_file_suffix}"


    try:
        hou.parm('/stage/usd_rop1/execute').pressButton()
        if not new_usd_file_path.is_file():
            raise FileNotFoundError(f"usdファイルが生成されませんでした。:{usd_file}")
    except hou.OperationFailed:
        print("usdファイルの保存に失敗しました。")


    cmd = [Blender_PATH, "--python", blender_import_usd_path, "--", str(new_usd_file_path)]
    subprocess.Popen(cmd)


if __name__ == '__main__':
    main()
