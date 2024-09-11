'''
Author: Qigqi
LastEditors: lydonShen lyden_shen@sina.com
FilePath: /tools/verify_images.py
Copyright (c) 2024 by Qigqi, All Rights Reserved. 
'''
import json
import os

def load_json_file(json_path):
    with open(json_path, encoding='utf-8') as json_file:
        json_strs = json.load(json_file)
    return json_strs

version = 2

image_folder = f"/data/datasets/chart/chartdata_v2/chartimg"
json_file = f'/home/data_sld/chart/datachart_question/multi_choice_datachart.json'
# image_folder = f'chartdata_v{version}/chartimg'
for version in range(2,5):
    # json_file = f'chart_caption_raw_v{version}.json'
    total_not_exist_num = 0
    json_results = load_json_file(json_file)
    for result in json_results:
        image_path = os.path.join(image_folder, result['image_path'])
        if not os.path.exists(image_path):
            total_not_exist_num += 1
            print(result['image_path'])
    print(f'Total number of image {len(json_results)}, the number of the not exist images {total_not_exist_num}.')