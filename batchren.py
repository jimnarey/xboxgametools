import json
import re
import os
from optparse import OptionParser


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
            self.new_base_name = redata.sub(replacement, self.new_base_name)

    def replace_many(self, sub_strings, replacement, case_sensitive):
        for sub_string in sub_strings:
            self.replace_sub_string(sub_string, replacement, case_sensitive=case_sensitive)

    def cut_multi_whitespace(self):
        self.new_base_name = ' '.join(self.new_base_name.split())

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
        self.get_files(dir_path)
        self.name_length_summary = []

    def get_files(self, dir_path):
        for root, dirs, files in os.walk(self.dir_path):
            for file in files:
                self.files.append(RomFile(os.path.join(root, file)))

    def gen_name_length_summary(self, max_length):
        too_long = 0
        too_long_files = []
        for file in self.files:
            if file.current_length() > max_length:
                too_long += 1
                too_long_files.append('{0}\n'.format(file.new_base_name))
        summary = ['{0} files are longer than {1} characters:\n'.format(too_long, max_length)] + too_long_files + ['\n\n****************\n\n']
        self.name_length_summary += summary

    def remove_illegal_strings(self, illegal_strings):
        for file in self.files:
            file.replace_many(illegal_strings, '', True)

    def replace_in_file(self, file, replace_spec):
        file.replace_sub_string(
            replace_spec['pattern'],
            replace_spec['replacement'],
            replace_spec['caseSensitive'])

    def make_replacements(self, replace_specs, max_length):
        for file in self.files:
            for replace_spec in replace_specs:
                if replace_spec['longOnly'] is False or file.current_length() > max_length:
                    self.replace_in_file(file, replace_spec)
                    file.cut_multi_whitespace()


def get_prefs(json_path):
    with open(json_path, 'r') as json_file:
        return json.load(json_file)


def write_summary(summary_file_path, summary_lines):
    with open(summary_file_path, 'w') as summary_file:
        summary_file.writelines(summary_lines)


parser = OptionParser()
parser.add_option('-j', '--json', dest='json_prefs', help='Specify input json file')
(options, args) = parser.parse_args()
if options.json_prefs is None:
    print(parser.usage)
    exit(0)

prefs = get_prefs(options.json_prefs)

root = RootDir(prefs['rootDir'])
root.gen_name_length_summary(prefs['maxFileNameLength'])
root.remove_illegal_strings(prefs['illegalStrings'])
root.gen_name_length_summary(prefs['maxFileNameLength'])
root.make_replacements(prefs['replace'], prefs['maxFileNameLength'])
root.gen_name_length_summary(prefs['maxFileNameLength'])
write_summary(prefs['summaryFilePath'], root.name_length_summary)
