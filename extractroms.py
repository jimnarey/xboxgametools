import os
import re
import py7zr
import pprint
from py7zr import Bad7zFile

start_path = '/media/jimnarey/HDD_Data_B/Romsets/Genesis Full Set/'

english_language_codes = ['JUE', 'UE', 'JE', 'JU', 'E', 'U', 'UK', 'A', '4', 'W']

ok_dumps = ['!', 'a', 'o', 'h', 't', 'f']

class ArchiveEntry:

    def __init__(self, entry_name):
        self.entry_name = entry_name
        self.region_other_codes = []
        self.dump_codes = []
        self._populate_codes()

    def _populate_codes(self):
        self.region_other_codes = re.findall("\((.*?)\)", self.entry_name)
        self.dump_codes = re.findall("\[(.*?)\]", self.entry_name)

    # def num_dump_codes(self):
    #     return len(self.dump_codes)

    # def num_region_codes(self):
    #     return len(self.region_codes)


class ArchiveFile:

    def __init__(self, file_path):
        self.file_path = file_path
        self.entries = []
        self.good_dumps = []
        self.best_version = None

    def populate_entries(self):
        try:
            with py7zr.SevenZipFile(self.file_path, mode='r') as arch:
                self.entries = [ArchiveEntry(entry) for entry in arch.getnames()]
        except (OSError, Bad7zFile):
            return False
        return True

    def get_good_dumps(self):
        for entry in self.entries:
            if '!' in entry.dump_codes:
                self.good_dumps.append(entry)
            if not entry.dump_codes:
                self.good_dumps.append(entry)

    def get_best_version(self):
        for ro_code in english_language_codes:
            for entry in self.entries:
                if ro_code in entry.region_other_codes:
                    for dump_code in ok_dumps:
                        if dump_code in entry.dump_codes:
                            self.best_version = entry
                            return
        
    
class RomRootFolder:

    def __init__(self, dir_path):
        self.dir_path = dir_path
        self.file_paths = []
        self.valid_archives = []
        self.sorted_archives = []
        self.invalid_file_paths = []
        self.with_best_version = []
        self.no_best_version = []
        self._get_file_paths()
        self._get_archives()
        self._find_best_versions()

    def _get_file_paths(self):
        for root, dirs, files in os.walk(self.dir_path):
            for file in files:
                self.file_paths.append(os.path.join(root, file))

    def _get_archives(self):
        for file_path in self.file_paths:
            current_file = ArchiveFile(file_path)
            if current_file.populate_entries() == True:
                self.valid_archives.append(current_file)
            else:
                self.invalid_file_paths.append(file_path)

    def _prune_archives(self):


    def _find_best_versions(self):
        for arch in self.sorted_archives:
            arch.get_best_version()
            if arch.best_version:
                self.with_best_version.append(arch)
            else:
                self.no_best_version.append(arch)

root = RomRootFolder(start_path)
for arch in root.no_best_version:
    for entry in arch.entries:
        pprint.pprint(entry.entry_name)

