import os
from synopsis_zip import SynopsisZip
from file_renamer import FileRenamer

synopsis_dir = './synopsis'

class SynopsisFinder:

    def __init__(self, system):
        self.system = system
        try:
            self.synopsis_zip = SynopsisZip(os.path.join(synopsis_dir, '{0}{1}'.format(system, '.zip')))
        except OSError:
            print('Specified synopsis file not found')
            exit(0)

    
    