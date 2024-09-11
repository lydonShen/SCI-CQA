import os 
import json
import csv


def load_json_file(json_path):
    with open(json_path, encoding='utf-8') as json_file:
        json_strs = json.load(json_file)
    return json_strs


def extract_from_json_result(json_result):
    question_type = json_result['type']
    image_path = json_result['image_path']
    conversations = json_result['conversations']

    return question_type, image_path, conversations


def write_json(dict, output_files):
    with open(output_files, 'w', encoding='utf-8') as file:
        json_str = json.dumps(dict, indent=4)
        file.write(json_str)
    print(f'File {output_files} is wrote done.')


def clean_json_filepath(json_path,cleaned_json_path):
    json_dict = []
    results = load_json_file(json_path)
    total = 0
    for result in results:
        image_path = os.path.join('/data/datasets/chart/chartdata/chartimg', result['image_path'])
        if not os.path.exists(image_path):
            json_dict.append(result)
            total += 1
    print(total)
    write_json(json_dict, cleaned_json_path)


def num_of_right_answer(json_of_gpt4o, json_file_other):
    right_dict = []
    wrong_dict = []
    total_right = 0
    basename = os.path.basename(json_file_other)
    gpt_results = load_json_file(json_of_gpt4o)
    other_results = load_json_file(json_file_other)
    for gpt_result, other_result in zip(gpt_results, other_results): 
        question_type, image_path, conversetion_gpt = extract_from_json_result(gpt_result)
        _, _, conversetion_other = extract_from_json_result(other_result)
        gpt_answer = conversetion_gpt[1]['value']
        other_answer = conversetion_other[1]['value']
        if other_answer in gpt_answer:
            right_dict.append({
                "type": question_type,
                "image_path": image_path,
                "conversations": [
                    {
                        "form": "human",
                        "value": conversetion_gpt[0]['value']
                    },
                    {
                        "form": "gpt4",
                        "value": conversetion_other[1]['value']
                    }
                ],
            })
            total_right += 1
        else:
            wrong_dict.append({
                "type": question_type,
                "image_path": image_path,
                "conversations": [
                    {
                        "form": "human",
                        "value": conversetion_gpt[0]['value']
                    },
                    {
                        "form": "gpt4o",
                        "value": conversetion_gpt[1]['value'],
                    },
                    {
                        "form": basename,
                        "value": conversetion_other[1]['value'],
                    }
                ],
            })
    correct_rate = total_right/len(gpt_results)
    wrong_rate = 1 - correct_rate
    write_json(right_dict, f'/home/data_sld/chart/result_of_experiments/correct_{basename}_rate_{correct_rate*100:.2f}%.json')
    write_json(wrong_dict, f'/home/data_sld/chart/result_of_experiments/wrong_{basename}_rate_{wrong_rate*100:.2f}%.json')
    print(f'The number of the toatal question is {len(gpt_results)}')
    print(f"The number of the toatal rigth is {total_right}, the percentage of correctness is {correct_rate*100:.2f}%.")
    
def check_images(json_path):
    num_exist = 0
    num_loss = 0
    results = load_json_file(json_path)
    loss_file_name = []
    loss_image_file = 'loss_image_file.csv'
    for result in results:
        image_path = os.path.join('/data/datasets/chart/chartdata/chartimg', result['image_path'])
        if not os.path.exists(image_path):
            image_path = os.path.join('/home/data_sld/flowchart_V1_human_check/', result['image_path'])
            if os.path.exists:
                loss_file_name.append(result['image_path'])
                num_exist += 1
            else:
                num_loss += 1
    with open(loss_image_file, 'w', encoding='utf-8') as file:
        w = csv.writer(file)
        for f_n in loss_file_name:
            w.writerow([f_n])
    print(f'Loss {num_loss}. Exist {num_exist}')
# "/home/data_sld/chart/result_of_experiments/true_or_false_by_chartllama.json"

row_multi_choice_json_path = '/home/data_sld/chart/multi-choice.json'
row_true_or_false_json_path = "/home/data_sld/chart/true_or_false.json"
row_openend_json_path = "/home/data_sld/chart/open_end.json"

result_of_experiments_folder = '/home/data_sld/chart/result_of_experiments'
name_of_json_file = 'true_or_false_by_llava_v1.6-13B.json'

target_json = os.path.join(result_of_experiments_folder, name_of_json_file)

num_of_right_answer(row_true_or_false_json_path, target_json)

# check_images(json_path)
# a = clean_json_filepath(json_path, output_json)
# num_of_right_answer('cleaned_multi-choice.json', 'multi_choice_by_internvl2-8b.json')





