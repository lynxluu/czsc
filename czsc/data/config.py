
import json
import yaml

def json_config():
    with open(r'E:\usr\git\czsc\czsc\data\config.json') as f:
        data = json.load(f)

    return data

def yaml_config():
    with open(r'E:\usr\git\czsc\czsc\data\config.yaml', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    return data

# para1 = json_config()
# para2 = yaml_config()
#
# print(para1["dev"]["data_path"])
# print(para1["dev"]["sdt"])
# print(para1["dev"]["edt"])
#
# print(para2["dev"]["data_path"])
# print(para2["dev"]["sdt"])
# print(para2["dev"]["edt"])