import glob
import hashlib
import itertools
import filecmp
from tqdm import tqdm
import multiprocessing
import argparse
import os
import PIL.Image

def __is_jpeg(file_path):
    return os.path.splitext(file_path)[1].lower() in [".jpg", ".jpeg"]

def __calc_hash(file_path):
    if __is_jpeg(file_path):
        with PIL.Image.open(file_path) as jpeg_file:
            data = jpeg_file.tobytes()
    else:
        with open(file_path, "rb") as file_data:
            data = file_data.read(1024*1024*8)
    return file_path, hashlib.md5(data).hexdigest()

def __detect_duplicated_groups(path_list):
    process_pool = multiprocessing.Pool(multiprocessing.cpu_count())
    result = process_pool.map(__calc_hash, tqdm(path_list), 100)
    group_map = {}
    for file_path, hash_string in result:
        if hash_string not in group_map:
            group_map[hash_string] = []
        group_map[hash_string].append(file_path)

    duplicated_groups = [
        (hash_string, path_group)
        for hash_string, path_group in group_map.items()
        if 2 <= len(path_group)
    ]
    return duplicated_groups

def __read_picture(picture_file_path):
    with PIL.Image.open(picture_file_path) as pic:
        pic_bytes =  pic.tobytes()
    return pic_bytes

def __compare_bytes(lhbytes, rhbytes):
    if len(lhbytes) != len(rhbytes):
        return False
    for lhv, rhv in zip(lhbytes, rhbytes):
        if lhv - rhv != 0:
            return False
    return True

def __compare_file(file_pair):
    if __is_jpeg(file_pair[0]):
        lhv = __read_picture(file_pair[0])
        rhv = __read_picture(file_pair[1])
        return __compare_bytes(lhv, rhv)
    return filecmp.cmp(file_pair[0], file_pair[1], False)

def __deep_compare_file_pairs(file_pairs):
    process_pool = multiprocessing.Pool(multiprocessing.cpu_count())
    compare_result_list = process_pool.map(__compare_file, tqdm(file_pairs), 1)
    duplicated_pairs = [
        file_pair
        for is_duplicated, file_pair in zip(compare_result_list, file_pairs)
        if is_duplicated
    ]
    return duplicated_pairs

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--directory", type=str, required=True)
    args = parser.parse_args()

    search_query = os.path.join(os.path.abspath(args.directory), "**/*.*")
    files = glob.glob(search_query, recursive=True)
    duplicated_groups = __detect_duplicated_groups(files)

    file_pairs = []
    for key, duplicated_file_path_list in tqdm(duplicated_groups):
        file_pairs.extend(itertools.combinations(duplicated_file_path_list, 2))
    duplicated_pairs = __deep_compare_file_pairs(file_pairs)

    for path_a, path_b in duplicated_pairs:
        print(f"{path_a} // {path_b}")
    exit(0)

