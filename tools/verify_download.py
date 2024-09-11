'''
Author: Qigqi
FilePath: /tools/verify_download.py
Copyright (c) 2024 by Qigqi, All Rights Reserved. 
'''
import os
import tarfile
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

    
def verify_tar_gz_file(file_path):
    try:
        with tarfile.open(file_path, 'r:gz') as tar:
            tar.getnames()
        # print(f"Tar.gz file {file_path} verification successful.")
        return True
    except Exception as e:
        # print(f"Tar.gz file {file_path} verification failed: {e}")
        return False
    

for i in range(1):
    TOTAL_FAILED_NUMBER = 0
    TOTAL_SUCCESS_NUMBER = 0
    dir_path = f'tex_source/test_latex'
    filenames = os.listdir(dir_path)

        # with ThreadPoolExecutor(max_workers=100) as executor:
        #     results = list(executor.map(verify_tar_gz_file, [os.path.join(dir_path, filename) for filename in filenames]))
    for filename in tqdm(filenames):
        try:
            if verify_tar_gz_file(os.path.join(dir_path, filename)):
                TOTAL_SUCCESS_NUMBER += 1
            else:
                TOTAL_FAILED_NUMBER +=1
        except Exception as e:
            print(f"{filename} happened {e}")
    print(f'The number of files successfully downloaded is {TOTAL_SUCCESS_NUMBER}')
    print(f'The number of files that failed to download is {TOTAL_FAILED_NUMBER}')
    print(f'The success rate is {(TOTAL_SUCCESS_NUMBER/(TOTAL_SUCCESS_NUMBER+TOTAL_FAILED_NUMBER)*100)}')
