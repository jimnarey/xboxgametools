import os
import re
import json
from pathlib import Path
# import pprint
from optparse import OptionParser
import py7zr
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
            entry for entry in self.ok_ro if entry in self.ok_dumps]

    def get_matches(self, ok_dump_regexes, ok_ro_list):
        self._get_ok_dumps(ok_dump_regexes)
        self._get_ok_ro(ok_ro_list)
        self._cross_ref_matches()

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

    def extract_entry(self, target_path, entry_name):
        with py7zr.SevenZipFile(self.file_path, 'r') as arch:
            arch.extract(path=target_path, targets=[entry_name])

    def extract_best_match(self, target_path):
        print('Extracting: {0}'.format(self.matches[0].entry_name))
        self.extract_entry(target_path, self.matches[0].entry_name)


class RomRootFolder:

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

    def generate_summary(self):
        has_matches = 0
        no_matches = 0
        has_matches_lines = []
        no_matches_lines = []
        for arch in self.valid_archives:
            if arch.num_matches():
                has_matches += 1
                has_matches_lines.append(arch.summary())
                # print(arch.file_path)
                has_matches_lines.append(arch.matches[0].entry_name)
                has_matches_lines.append('\n\n')
            else:
                no_matches += 1
                no_matches_lines.append(arch.summary())
                for entry in arch.all_entries:
                    no_matches_lines.append(
                        '{entry}\n'.format(entry=entry.entry_name))
                no_matches_lines.append('\n')
        headlines = ['Total archives: {0}\n'.format(len(self.valid_archives)), 'With matches: {0}\n'.format(has_matches), 'No matches: {0}\n'.format(no_matches), '\n']
        return headlines + has_matches_lines + no_matches_lines

    def write_summary(self, summary_file_path):
        with open(summary_file_path, 'w') as summary_file:
            summary_file.writelines(self.generate_summary())

    def extract_matches(self, target_path):
        for arch in self.valid_archives:
            if arch.matches:
                arch.extract_best_match(target_path)


def get_prefs(json_path):
    with open(json_path, 'r') as json_file:
        return json.load(json_file)


def get_dump_code_regexes(ok_dump_codes):
    regexes = []
    for code in ok_dump_codes:
        regexes.append(re.compile("^[%s][0-9]{0,2}" % code))
    return regexes


def process(prefs):
    root = RomRootFolder(prefs['rootDir'])
    ok_dump_regexes = get_dump_code_regexes(prefs['okDumpCodes'])
    root.sort(ok_dump_regexes, prefs['okRoCodes'])
    if prefs['writeSummary'] is True:
        root.write_summary(prefs['summaryFilePath'])
    if prefs['writeFiles'] is True:
        if not os.path.isdir(prefs['targetDir']):
            target_path = Path(prefs['targetDir'])
            target_path.mkdir(parents=True, exist_ok=True)
        root.extract_matches(prefs['targetDir'])


parser = OptionParser()
parser.add_option('-j', '--json', dest='json_prefs', help='Specify input json file')
(options, args) = parser.parse_args()
if options.json_prefs is None:
    print(parser.usage)
    exit(0)

prefs = get_prefs(options.json_prefs)
process(prefs)
