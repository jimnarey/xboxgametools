import os
import re
import py7zr
# import pprint
from py7zr import Bad7zFile


class ArchiveEntry:

    def __init__(self, entry_name):
        self.entry_name = entry_name
        self.region_other_codes = []
        self.dump_codes = []
        self._populate_codes()

    def _populate_codes(self):
        self.region_other_codes = re.findall("\((.*?)\)", self.entry_name)
        self.dump_codes = re.findall("\[(.*?)\]", self.entry_name)


class ArchiveFile:

    def __init__(self, file_path):
        self.file_path = file_path
        self.all_entries = []
        self.sorted_entries = []
        self.ok_dumps = []

    def populate_entries(self):
        try:
            with py7zr.SevenZipFile(self.file_path, mode='r') as arch:
                self.all_entries = [ArchiveEntry(entry)
                                    for entry in arch.getnames()]
        except (OSError, Bad7zFile):
            return False
        return True

    def cut_by_ro_codes(self, bad_codes):
        for entry in self.sorted_entries:
            for code in bad_codes:
                if code in entry.region_other_codes:
                    self.sorted_entries.remove(entry)

    def get_ok_dumps(self, ok_dump_regexes):
        for entry in self.all_entries:
            for code in entry.dump_codes:
                if any(re.match(regex, code) for regex in ok_dump_regexes):
                    self.ok_dumps.append(entry)
                    print(entry.entry_name)
            if not entry.dump_codes:
                self.ok_dumps.append(entry)


class RomRootFolder:

    # def __init__(self, dir_path, log_path):
    def __init__(self, dir_path):
        self.dir_path = dir_path
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

    def all_dump_codes(self):
        dump_codes = []
        for archive in self.valid_archives:
            for entry in archive.all_entries:
                for code in entry.dump_codes:
                    if code not in dump_codes:
                        dump_codes.append(code)
        return dump_codes

    def all_ro_codes(self):
        ro_codes = []
        for archive in self.valid_archives:
            for entry in archive.all_entries:
                for code in entry.region_other_codes:
                    if code not in ro_codes:
                        ro_codes.append(code)
        return ro_codes


start_path_linux = '/media/jimnarey/HDD_Data_B/Romsets/Genesis Full Set/'

start_path_linux_vm = '/media/sf_G_DRIVE/Romsets/Genesis Full Set'
log_path_linux_vm = '/media/sf_G_DRIVE/Romsets/genesis_log.txt'

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

root = RomRootFolder(start_path_linux_vm)

for arch in root.valid_archives:
    arch.get_ok_dumps(ok_dump_regexes)
