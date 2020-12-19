import os
import re
import py7zr
# import pprint
from py7zr import Bad7zFile


english_language_codes = [
                            'JUE',
                            'UE',
                            'JE',
                            'JU',
                            'E',
                            'U',
                            'UK',
                            'A',
                            '4',
                            'W'
                        ]

ok_dump_regexes = [
    re.compile("!"),
    re.compile("^[a,o,f][0-9]{1}")
]


class ArchiveEntry:

    def __init__(self, entry_name):
        self.entry_name = entry_name
        self.ro_codes = []
        self.dump_codes = []
        self._populate_codes()

    def _populate_codes(self):
        self.ro_codes = re.findall("\((.*?)\)", self.entry_name)
        self.dump_codes = re.findall("\[(.*?)\]", self.entry_name)

    def all_codes(self, code_type):
        if code_type == 'dump':
            return self.dump_codes
        elif code_type == 'ro':
            return self.ro_codes
        return None


class ArchiveFile:

    def __init__(self, file_path):
        self.file_path = file_path
        self.all_entries = []
        self.ok_dumps = []
        self.ok_ro = []
        self.matches = []

    def populate_entries(self):
        try:
            with py7zr.SevenZipFile(self.file_path, mode='r') as arch:
                self.all_entries = [ArchiveEntry(entry)
                                    for entry in arch.getnames()]
        except (OSError, Bad7zFile):
            return False
        return True

    def _get_ok_dumps(self, ok_dump_regexes):
        for entry in self.all_entries:
            for code in entry.dump_codes:
                if any(re.match(regex, code) for regex in ok_dump_regexes):
                    self.ok_dumps.append(entry)
            if not entry.dump_codes:
                self.ok_dumps.append(entry)

    def _get_ok_ro(self, ok_ro_list):
        for entry in self.all_entries:
            for code in ok_ro_list:
                if code in entry.ro_codes:
                    self.ok_ro.append(entry)

    def _cross_ref_matches(self):
        if self.ok_dumps and self.ok_ro:
            self.matches = [entry for entry in self.ok_dumps if entry in self.ok_ro]

    def get_matches(self, ok_dump_regexes, ok_ro_list):
        self._get_ok_dumps(ok_dump_regexes)
        self._get_ok_ro(ok_ro_list)
        self._cross_ref_matches

    def get_num_matches(self):
        return len(self.matches)

    # Use set
    def all_codes(self, code_type):
        codes = []
        for entry in self.all_entries:
            for code in entry.all_codes(code_type):
                if code not in codes:
                    codes.append(code)
        return codes


class RomRootFolder:

    def __init__(self, dir_path, log_path):
        self.dir_path = dir_path
        self.log_path = log_path
        self.file_paths = []
        self.valid_archives = []
        self.invalid_file_paths = []
        self._get_file_paths()
        self._get_archives()

    def _get_file_paths(self):
        for root, dirs, files in os.walk(self.dir_path):
            for file in files:
                self.file_paths.append(os.path.join(root, file))

    def _get_archives(self):
        for file_path in self.file_paths:
            current_file = ArchiveFile(file_path)
            if current_file.populate_entries() is True:
                self.valid_archives.append(current_file)
            else:
                self.invalid_file_paths.append(file_path)

    def all_codes(self, code_type):
        codes = []
        for arch in self.valid_archives:
            for code in arch.all_codes(code_type):
                if code not in codes:
                    codes.append(code)
        return codes

    # def all_dump_codes(self):
    #     dump_codes = []
    #     for archive in self.valid_archives:
    #         for entry in archive.all_entries:
    #             for code in entry.dump_codes:
    #                 if code not in dump_codes:
    #                     dump_codes.append(code)
    #     return dump_codes

    # def all_ro_codes(self):
    #     ro_codes = []
    #     for archive in self.valid_archives:
    #         for entry in archive.all_entries:
    #             for code in entry.ro_codes:
    #                 if code not in ro_codes:
    #                     ro_codes.append(code)
    #     return ro_codes

    def sort(self, ok_dump_regexes, ok_ro_codes):
        for arch in self.valid_archives:
            arch.get_matches(ok_dump_regexes, ok_dump_regexes)

    def write_log(self):
        output = []
        for arch in self.valid_archives:
            output.append("{file} : {matches}\n".format(file=arch.file_path, matches=str(arch.get_num_matches())))
        with open(self.log_path, 'w') as log_file:
            log_file.writelines(output)


start_path_linux = '/media/jimnarey/HDD_Data_B/Romsets/Genesis Full Set/'

start_path_linux_vm = '/media/sf_G_DRIVE/Romsets/Genesis Full Set'
log_path_linux_vm = '/media/sf_G_DRIVE/Romsets/genesis_log.txt'

root = RomRootFolder(start_path_linux_vm, log_path_linux_vm)
# root.sort()
root.write_log()

# for arch in root.valid_archives:
#     arch.get_ok_dumps(ok_dump_regexes)