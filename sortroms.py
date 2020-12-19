import os
import re
import json
import py7zr
import pprint
from py7zr import Bad7zFile


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
        self.best_match = None

    def name(self):
        return os.path.basename(self.file_path)

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
        self.matches = [
            entry for entry in self.ok_dumps if entry in self.ok_ro]

    def get_matches(self, ok_dump_regexes, ok_ro_list):
        self._get_ok_dumps(ok_dump_regexes)
        self._get_ok_ro(ok_ro_list)
        self._cross_ref_matches()

    def _sort_matches_by_dump(self, ok_dump_regexes):
        if self.matches:
            dump_sorted = []
            for regex in ok_dump_regexes:
                    for index, entry in enumerate(self.matches):
                        if any(re.match(regex, ro_code) for dump_code in entry.dump_codes):
                            dump_sorted.append(self.matches.pop(index))
            self.matches = dump_sorted.extend(self.matches)

    def _sort_matches_by_ro(self, ok_ro_codes):
        ro_sorted = []
        for code in ok_ro_codes:
            for index, entry in enumerate(self.matches):
                if code in entry.ro_codes:
                    ro_sorted.append(self.matches.pop(index))
        self.matches = ro_sorted.extend(self.matches)

    def sort_matches(self, ok_dump_regexes, ok_ro_codes):
        self._sort_matches_by_ro(ok_ro_codes)
        self._sort_matches_by_dump(ok_dump_regexes)

    def num_matches(self):
        return len(self.matches) if self.matches else 0

    # Use set
    def all_codes(self, code_type):
        codes = []
        for entry in self.all_entries:
            for code in entry.all_codes(code_type):
                if code not in codes:
                    codes.append(code)
        return codes

    def summary(self):
        return '{archive} - DM: {num_dm} - ROM: {num_rom} - BOTH: {num_both}\n'.format(
            archive=self.name(),
            num_dm=len(self.ok_dumps),
            num_rom=len(self.ok_ro),
            num_both=self.num_matches())


class RomRootFolder:

    def __init__(self, dir_path, summary_file_path):
        self.dir_path = dir_path
        self.summary_file_path = summary_file_path
        self.file_paths = []
        self.valid_archives = []
        self.invalid_file_paths = []
        self.has_matches = []
        self.no_matches = []
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

    def sort(self, ok_dump_regexes, ok_ro_codes):
        for arch in self.valid_archives:
            arch.get_matches(ok_dump_regexes, ok_ro_codes)
            # arch.sort_matches(ok_dump_regexes, ok_ro_codes)

    def sort_by_has_matches(self):
        self.has_matches = []
        self.no_matches = []
        for arch in self.valid_archives:
            if arch.num_matches():
                self.has_matches.append(arch)
            else:
                self.no_matches.append(arch)

    def generate_summary(self):
        self.sort_by_has_matches()
        summary_lines = ['\n', '\n']
        for arch in self.has_matches:
            summary_lines.append(arch.summary())
            summary_lines.append(arch.matches[0].entry_name)
            summary_lines.append('\n')
        summary_lines.extend(['\n', '\n'])
        for arch in self.no_matches:
            summary_lines.append(arch.summary())
            for entry in arch.all_entries:
                summary_lines.append(
                    '{entry}\n'.format(entry=entry.entry_name))
            summary_lines.append('\n')
        return summary_lines

    def write_summary(self):
        with open(self.summary_file_path, 'w') as summary_file:
            summary_file.writelines(self.generate_summary())


def get_prefs(json_path):
    with open(json_path, 'r') as json_file:
        return json.load(json_file)


# def get_dump_code_regexes(simple_dump_codes, numeral_dump_codes):
#     simple_dc_insert = ','.join(simple_dump_codes)
#     numeral_dc_insert = ','.join(numeral_dump_codes)
#     # Use old-style string formatting for clarity since regex uses {}
#     return [
#         re.compile("^[%s][0-9]{1}" % numeral_dc_insert),
#         re.compile("[%s]" % simple_dc_insert)
#     ]

def get_dump_code_regexes(ok_dump_codes):
    regexes = []
    for code in ok_dump_codes:
        regexes.append(re.compile("^[%s][0-9]{0,2}" % code))
    return regexes

prefs = get_prefs('./my_json/genesis_vm.json')

root = RomRootFolder(prefs['rootDir'], prefs['summaryFilePath'])

ok_dump_regexes = get_dump_code_regexes(
    prefs['okDumpCodes'])

root.sort(ok_dump_regexes, prefs['okRoCodes'])

root.write_summary()
