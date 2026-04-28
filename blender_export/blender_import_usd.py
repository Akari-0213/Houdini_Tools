import sys


import bpy


def get_args():
    try:
        idx = sys.argv.index("--")
        return sys.argv[idx + 1:]
    except ValueError:
        return[]


def main() -> None:
    args = get_args()

    if not args:
        print("引数が設定されていません")
        return
    usd_file = args[0]

    all_objects = bpy.ops.object.select_all(action="SELECT")
    for object in all_objects:
        bpy.ops.object.delete()

    
    bpy.ops.wm.usd_import(filepath=usd_file)


if __name__ == '__main__':
    main()

