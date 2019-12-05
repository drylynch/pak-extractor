from pathlib import Path

MAGIC_NUMBER = b'\x50\x41\x43\x4B'
OFFSET_MAGIC_NUMBER = 0
OFFSET_TOC = 4
OFFSET_MYSTERY_ID = 8
OFFSET_DATA_START = 12


def is_valid_magic_number(magic):
    return magic == MAGIC_NUMBER


def read_bytes_from_file(f, offset, length):
    """ return length bytes from file at offset """
    f.seek(offset)
    return f.read(length)


def read_magic_from_pak(f):
    """ return bytestring magic number found in .pak """
    return read_bytes_from_file(f, OFFSET_MAGIC_NUMBER, 4)


def read_toc_offset_from_pak(f):
    """ return int toc offset found in .pak """
    return int.from_bytes(read_bytes_from_file(f, OFFSET_TOC, 4), 'little')


def read_mystery_id_from_pak(f):
    """ return int mystery id found in .pak. still no idea what this does. """
    return int.from_bytes(read_bytes_from_file(f, OFFSET_MYSTERY_ID, 4), 'little')


def read_toc_from_pak(f):
    """ return table of contents from .pak """
    f.seek(read_toc_offset_from_pak(f))
    toc = []
    while True:
        line = f.read(64)  # index items are 64 bytes long
        if not line:
            break
        toc.append(PakFile(line))
    return toc


def validate_magic_number(f):
    """ raises ValueError if magic number in file isn't right """
    if not is_valid_magic_number(read_magic_from_pak(f)):
        raise ValueError("ERROR: invalid pak file! (magic number mismatch)")


class Pak:
    def __init__(self):
        """ describes a full .pak file """
        self.toc_offset = None  # table of contents offset
        self.mystery_id = None  # no idea what this is for, taken from original .pak, seems to have no effect on game
        self.table_of_contents = []  # list of PakFiles contained in this .pak

    def __str__(self):
        outstr = "Pak(toc_offset: {0}, mystery_id: {1})".format(self.toc_offset, self.mystery_id)


    def compile_to(self, output_path):
        """ compile and write .pak file to path """
        if not self.is_everything_ready_to_compile():
            raise ValueError("ERROR: pak or pakfiles are missing data, cannot compile!")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(MAGIC_NUMBER
                    + self.toc_offset.to_bytes(4, 'little')
                    + self.mystery_id.to_bytes(4, 'little'))
            for p in self.table_of_contents:
                f.write(p.data)
                f.write(b'\x00' * p.data_padding_length)
            f.write(self.get_full_table_of_contents())

    def get_full_table_of_contents(self):
        """ return table of contents as would be found in a .pak """
        output = b''
        for p in self.table_of_contents:
            output += p.output_line()
        return output

    def is_everything_ready_to_compile(self):
        """ return true if everything needed is ready and the pak can be compiled (no variables are None) """
        pak_ready = (self.toc_offset is not None
                     and self.mystery_id is not None)
        pakfiles_ready = True
        for t in self.table_of_contents:
            if not (t.path is not None
                    and t.data is not None
                    and t.data_offset is not None
                    and t.data_length is not None
                    and t.data_padding_length is not None):
                pakfiles_ready = False
                break
        return pak_ready and pakfiles_ready


class PakFile:
    def __init__(self, tocline=None):
        """ describes a file packed in a .pak file, ie a table entry in the table of contents """
        self.path = None  # file path, pathlib Path
        self.data = None  # file data, bytes
        self.data_offset = None  # int offset of file data in .pak
        self.data_length = None  # int length of file data
        self.data_padding_length = None  # int length of padding after file data
        if tocline is not None:
            self.parse_line(tocline)

    def __str__(self):
        return "PakFile(path: {0}, offset: {1}, data_length: {2}, data set: {3})".format(self.path, self.data_offset, self.data_length, self.data is not None)

    def parse_line(self, tocline):
        """ split table of contents line into its parts """
        self.path = Path(
            tocline[0:52].decode('utf-8').strip('\x00'))  # first 52 bytes is left justified path, padded with \x00
        self.data_offset = int.from_bytes(tocline[52:56], 'little')
        self.data_length = int.from_bytes(tocline[56:60], 'little')  # bytes [56:60] are the same as [60:64], both length. not sure why.

    def set_data(self, data):
        """ set file data, and compute related bits """
        self.data = data
        self.data_length = len(data)
        self.calculate_padding()

    def calculate_padding(self):
        """ calculate length of null padding between data to align on 8-byte blocks. requires data! """
        if self.data is None:
            raise ValueError("ERROR: data must be set with set_data() to calculate padding")
        else:
            self.data_padding_length = 8 + (8 - ((self.data_offset + self.data_length) % 8))  # 8 < padding <= 16, to align data on 8-byte blocks with an 8-byte null delimiter

    def output_line(self):
        """ return this file's info as a table of contents entry (64 length bytestring) """
        path = str(self.path).replace('\\', '/').encode().ljust(52, b'\x00')  # convert windows backslashes to unix forward slashes, encode to bytes, left justified
        offset = self.data_offset.to_bytes(4, 'little')
        length = self.data_length.to_bytes(4, 'little')
        return path + offset + length + length
