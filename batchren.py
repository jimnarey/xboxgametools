import json
import re
import os


def get_prefs(json_path):
    with open(json_path, 'r') as json_file:
        return json.load(json_file)


class RomFile:

    def __init__(self, file_path):
        self.full_path = file_path
        self.dir_path, self.base_name = os.path.split(file_path)
        self.new_base_name = self.base_name

    def replace_sub_string(self, sub_string, replacement, case_sensitive=True):
        if case_sensitive:
            self.new_base_name = self.new_base_name.replace(sub_string, replacement)  # No if check for substring
        else:
            redata = re.compile(re.escape(sub_string), re.IGNORECASE)
            self.new_base_name = redata.sub('replacement', self.new_base_name)

    # def replace_case_insensitive(self, sub_string, replacement):
    #     redata = re.compile(re.escape(sub_string), re.IGNORECASE)
    #     self.new_base_name = redata.sub('replacement', self.new_base_name)

    # def replace_case_sensitive(self, sub_string, replacement):
    #     if sub_string in self.new_base_name:
    #         self.new_base_name = self.new_base_name.replace(sub_string, replacement)

    def replace_many(self, sub_strings, replacement, case_sensitive):
        for sub_string in sub_strings:
            self.replace_sub_string(sub_string, replacement, case_sensitive)

    def orig_length(self):
        return len(self.base_name)

    def current_length(self):
        return len(self.new_base_name)

    def new_file_path(self):
        return os.path.join(self.dir_path, self.new_base_name)


class RootDir:

    def __init__(self, dir_path):
        self.dir_path = dir_path
        self.files = []

    def get_files(self, dir_path):
        for root, dirs, files in os.walk(self.dir_path):
            for file in files:
                self.file_paths.append(RomFile(os.path.join(root, file)))


prefs = get_prefs('./my_json/amiga_rename_vm.json')


def process(prefs):
    root = RootDir(prefs['rootDir'])
    for file in root.files:
        if prefs['illegalChars']:
            file.replace_sub_strings(prefs['illegalChars'], '')
