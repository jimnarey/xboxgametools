import json
import re
import os

def get_prefs(json_path):
    with open(json_path, 'r') as json_file:
        return json.load(json_file)


# class RomFile:

#     def __init__(path, basename):
#         self.path = path
#         self.basename = basename

# class RootDir:

#     def __init__(dir_path):
#         self.dir_path = dir_path
#         self.files = []

#     def get_files(dir_path):
#         for root, dirs, files in os.walk(self.dir_path):
#                 for file in files:
#                     self.file_paths.append(RomFile(root, basename))

def get_files(dir_path):
    file_paths = []
    for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_paths.append(os.path.join(root, file))
    return file_paths


def truncate_disk_num(file_name):
    redata = re.compile(re.escape('disk'), re.IGNORECASE)
    return redata.sub('D', file_name)


def remove_the(file_name):
    if ', The' in file_name:
        return file_name.replace(', The', '')
    return file_name


def remove_illegal_chars(file_name):
    new_name = file_name
    for char in [',', ':', '+', '?', '=', '|']:
        new_name = new_name.replace(char, '')
    return new_name


def get_illegal_names(file_paths):
    new_file_paths = []
    for file_path in file_paths:
        if len(os.path.basename(file_path)) > 42:
            print(os.path.basename)



# prefs = get_prefs('./json/nameforexfat_template.json')
file_paths = get_files('./fixtures')