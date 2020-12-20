import json
import re
import os
from optparse import OptionParser


class FileName:

    def __init__(self, file_path, max_length):
        self.full_path = file_path
        self.max_length = max_length
        self.dir_path, self.base_name = os.path.split(file_path)
        self.new_base_name = self.base_name

    def replace_sub_string(self, sub_string, replacement, case_sensitive=True):
        if case_sensitive:
            self.new_base_name = self.new_base_name.replace(
                sub_string, replacement)  # No if check for substring
        else:
            redata = re.compile(re.escape(sub_string), re.IGNORECASE)
            self.new_base_name = redata.sub(replacement, self.new_base_name)

    def replace_many(self, sub_strings, replacement, case_sensitive):
        for sub_string in sub_strings:
            self.replace_sub_string(
                sub_string, replacement, case_sensitive=case_sensitive)

    def cut_multi_whitespace(self):
        self.new_base_name = ' '.join(self.new_base_name.split())

    def apply_shorten_replacements(self, replace_specs):
        for replace_spec in replace_specs:
            if self.current_length() > self.max_length:
                self.replace_sub_string(
                    replace_spec['pattern'],
                    replace_spec['replacement'],
                    replace_spec['caseSensitive'])
            else:
                break

    def compress_subtitle(self, compress_spec):
        if compress_spec['subtitleMark'] in self.new_base_name:
            name_stem, name_ext = os.path.splitext(self.new_base_name)
            # Find the last occurance of text meeting the specified regex (e.g. '_Dxx')
            preserve_text_occurances = re.findall(compress_spec['preserveSuffix'], name_stem)
            preserve_text = ''
            if preserve_text_occurances:
                preserve_text = preserve_text_occurances[-1]
                # Remove last occurance of found substring from name stem
                name_stem = ''.join(name_stem.rsplit(preserve_text, 1))
            subtitle = name_stem.split(compress_spec['subtitleMark'])[-1]
            name_stem = ''.join(name_stem.rsplit(subtitle, 1))
            # Replace full subtitle with abbreviation
            subtitle = ''.join(char[0] for char in subtitle.split())
            self.new_base_name = '{0}{1}{2}{3}'.format(name_stem, subtitle, preserve_text, name_ext)

    def ordered_shorten(self, replace_specs, compress_spec):
        self.apply_shorten_replacements(replace_specs)
        if self.current_length() > self.max_length:
            self.compress_subtitle(compress_spec)

    def orig_length(self):
        return len(self.base_name)

    def current_length(self):
        return len(self.new_base_name)

    def new_file_path(self):
        return os.path.join(self.dir_path, self.new_base_name)


class RootDir:

    def __init__(self, dir_path, file_max_length):
        self.dir_path = dir_path
        self.file_max_length = file_max_length
        self.files = []
        self.get_files(dir_path)
        self.name_length_summary = []

    def get_files(self, dir_path):
        for root, dirs, files in os.walk(self.dir_path):
            for file in files:
                self.files.append(FileName(os.path.join(
                    root, file), self.file_max_length))

    def gen_name_length_summary(self, max_length):
        too_long = 0
        too_long_files = []
        for file in self.files:
            if file.current_length() > max_length:
                too_long += 1
                too_long_files.append('{0}\n'.format(file.new_base_name))
        summary = ['{0} files are longer than {1} characters:\n'.format(
            too_long, max_length)] + too_long_files + ['\n\n****************\n\n']
        self.name_length_summary += summary

    def remove_illegal_strings(self, illegal_strings):
        for file in self.files:
            file.replace_many(illegal_strings, '', True)

    def replace_in_file(self, file, replace_spec):
        file.replace_sub_string(
            replace_spec['pattern'],
            replace_spec['replacement'],
            replace_spec['caseSensitive'])

    def make_replacements(self, replace_specs):
        for file in self.files:
            for replace_spec in replace_specs:
                self.replace_in_file(file, replace_spec)
                # file.cut_multi_whitespace()

    def shorten_long_names(self, replace_specs, compress_spec):
        for file in self.files:
            file.ordered_shorten(replace_specs, compress_spec)

    def cut_multi_whitespace(self):
        for file in self.files:
            file.cut_multi_whitespace()


def get_prefs(json_path):
    with open(json_path, 'r') as json_file:
        return json.load(json_file)


def write_summary(summary_file_path, summary_lines):
    with open(summary_file_path, 'w') as summary_file:
        summary_file.writelines(summary_lines)


parser = OptionParser()
parser.add_option('-j', '--json', dest='json_prefs',
                  help='Specify input json file')
(options, args) = parser.parse_args()
if options.json_prefs is None:
    print(parser.usage)
    exit(0)

prefs = get_prefs(options.json_prefs)

root = RootDir(prefs['rootDir'], prefs['maxFileNameLength'])
root.gen_name_length_summary(prefs['maxFileNameLength'])
root.remove_illegal_strings(prefs['illegalStrings'])
root.gen_name_length_summary(prefs['maxFileNameLength'])
root.make_replacements(prefs['replaceInAll'])
root.cut_multi_whitespace()
root.gen_name_length_summary(prefs['maxFileNameLength'])
root.shorten_long_names(prefs['replaceToShorten'], prefs['subtitleCompress'])
root.gen_name_length_summary(prefs['maxFileNameLength'])
write_summary(prefs['summaryFilePath'], root.name_length_summary)
