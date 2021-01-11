import os
from optparse import OptionParser
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from lhafile import LhaFile

test_source = '/media/jimnarey/HDD_Data_B/Emulation - Working/Romsets - Temp/roms/WHDLoadZip/0/1943_v1.2.zip'
test_root = '/media/jimnarey/HDD_Data_B/Emulation - Working/Romsets - Temp/roms/test'
test_lha_source_dir = '/media/jimnarey/HDD_Data_B/Emulation - Working/Romsets - Temp/roms/test/1943_v1.2'
test_target = '/media/jimnarey/HDD_Data_B/Emulation - Working/Romsets - Temp/roms/test_lha.lha'

def get_stem(file_path):
    stem, ext =  os.path.splitext(os.path.basename(file_path))
    return stem

def make_temp_dir_name(target_root, source_file_path):
    return os.path.join(target_root, get_stem(source_file_path))
    

def unzip(source_file_path, target_root):
    try:
        with ZipFile(source_file_path, 'r') as zf:
            zf.extractall(path=make_temp_dir_name(target_root, source_file_path))
    except BadZipFile:
        print('{0}{1}'.format('Bad Zip: ', source_file_path))


# def make_lha(source_dir, target_file_path):
#     lf = LhaFile(target_file_path, 'w')
#     for root, dirs, files in os.walk(root_dir):
#         for file in files:
#             lf.write(os.path.join(root, file))
#             lf.filelist 



def change_arc(root_dir):
    file_paths = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            file_paths.append(os.path.join(root, file))
    return file_paths


# parser = OptionParser()
# parser.add_option('-d', '--dir', dest='root_dir', help='Specify root dir')
# (options, args) = parser.parse_args()
# if options.root_dir is None:
#     print(parser.usage)
#     exit(0)


