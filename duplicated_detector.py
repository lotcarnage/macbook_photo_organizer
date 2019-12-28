import glob
import hashlib
import itertools
import filecmp
from tqdm import tqdm
import multiprocessing
import argparse
import os

def __calc_hash(file_path):
    with open(file_path, "rb") as file_data:
        md5_value = hashlib.md5(file_data.read(1024*1024*8))
    return file_path, md5_value.hexdigest()

def __detect_duplicated_groups(path_list):
    process_pool = multiprocessing.Pool(multiprocessing.cpu_count())
    result = process_pool.map(__calc_hash, tqdm(path_list), 10)
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

def __compare_file(file_pair):
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

