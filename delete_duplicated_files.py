import os
from datetime import datetime
from tqdm import tqdm
import PIL.Image
import PIL.ExifTags
import argparse

def __is_jpeg(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    return ext in [".jpg", ".jpeg"]

def __is_mov(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    return ext in [".mov"]

def __datetime_to_date_string(date):
    v = str(date).split()
    yyyymmdd = ":".join(v[0].split("-"))
    return " ".join([yyyymmdd, v[1]])

def __get_creation_date(file_path):
    if os.name == "posix":
        stat = os.stat(file_path)
        date = datetime.fromtimestamp(stat.st_birthtime)
    else:
        date = datetime.fromtimestamp(os.path.getctime(file_path))
    return __datetime_to_date_string(date)

def __extract_jpg_original_date(file_path):
    with PIL.Image.open(file_path) as jpeg_file:
        exif = jpeg_file._getexif()
    return exif[36867]

def __extract_mov_original_date(file_path):
    from datetime import datetime as DateTime
    import struct

    ATOM_HEADER_SIZE = 8
    # difference between Unix epoch and QuickTime epoch, in seconds
    EPOCH_ADJUSTER = 2082844800

    original_date  = None
    # search for moov item
    with open(file_path, "rb") as mov_file:
        while True:
            atom_header = mov_file.read(ATOM_HEADER_SIZE)
            #~ print('atom header:', atom_header)  # debug purposes
            if atom_header[4:8] == b'moov':
                break  # found
            else:
                atom_size = struct.unpack('>I', atom_header[0:4])[0]
                mov_file.seek(atom_size - 8, 1)

        # found 'moov', look for 'mvhd' and timestamps
        atom_header = mov_file.read(ATOM_HEADER_SIZE)
        if atom_header[4:8] == b'cmov':
            raise RuntimeError('moov atom is compressed')
        elif atom_header[4:8] != b'mvhd':
            raise RuntimeError('expected to find "mvhd" header.')
        else:
            mov_file.seek(4, 1)
            original_date = struct.unpack('>I', mov_file.read(4))[0] - EPOCH_ADJUSTER
            original_date = DateTime.fromtimestamp(original_date)
            if original_date.year < 1990:  # invalid or censored data
                original_date = None
    if original_date is not None:
        original_date = __datetime_to_date_string(original_date)
    return original_date

def __get_jpeg_creation_date(file_path):
    try:
        date = __extract_jpg_original_date(file_path)
    except:
        date = __get_creation_date(file_path)
    return date

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--delete_list_file_path", type=str, required=True)
    args = parser.parse_args()

    with open(args.delete_list_file_path, "rt") as list_file:
        lines = [line.strip().split(" // ") for line in list_file.readlines()]
    for line in tqdm(lines):
        if os.path.isfile(line[0]) and os.path.isfile(line[1]):
            date_lhv = __get_jpeg_creation_date(line[0])
            date_rhv = __get_jpeg_creation_date(line[1])
            if date_lhv is None:
                print(line[0])
            if date_rhv is None:
                print(line[1])
            delete_target = line[1] if date_lhv <= date_rhv else line[0]
            if os.path.isfile(delete_target):
                os.remove(delete_target)
    exit(0)
