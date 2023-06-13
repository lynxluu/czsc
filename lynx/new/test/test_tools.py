import os

# Set the directory path where your files are located


def change_name():
    dir = r"D:\usr\git\czsc\lynx\new\data\\"
    for filename in os.listdir(dir):
        if filename.startswith("data_"):
            newname = filename.replace("data_", "")
            print(f"修改文件名称{filename}-->{newname}")
            os.rename(dir + filename, dir + newname)

change_name()