import io
from zipfile import ZipFile

class SynopsisZip:

    def __init__(self, synopsis_path):
        self.synopsis_path = synopsis_path
        self.contents = {}
        self._open()

    def _open(self):
        with ZipFile(self.synopsis_path, 'r') as synopsis_zip:
            for name in synopsis_zip.namelist():
                synopsis_text_file = synopsis_zip.open(name, 'r')
                synopsis_io = io.TextIOWrapper(io.BytesIO(synopsis_text_file.read()))
                self.contents[name] = synopsis_io.read()

# sms_s = SynopsisZip('./synopsis/mastersystem.zip')