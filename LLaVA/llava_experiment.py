##############################
# task:Multi-Choice Question
# author:sld
# time:2024.06.20
##############################
import argparse
import torch
import os
import json
from tqdm import tqdm
import shortuuid
import time

from llava.constants import IMAGE_TOKEN_INDEX, DEFAULT_IMAGE_TOKEN, DEFAULT_IM_START_TOKEN, DEFAULT_IM_END_TOKEN
from llava.conversation import conv_templates, SeparatorStyle
from llava.model.builder import load_pretrained_model
from llava.utils import disable_torch_init
from llava.mm_utils import tokenizer_image_token, get_model_name_from_path, KeywordsStoppingCriteria

from PIL import Image
import math
# from ChatTranslate import translate

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

def eval_model(args):
    # Model
    cuda_ids = "0, 1, 2, 3"
    os.environ['CUDA_VISIBLE_DEVICES'] = cuda_ids
    data_type = input("Pleace input datatype!<<<<<<<<< flow or datachart>>>>>>>>>>>>")
    json_files_folder = '/home/data_sld/chart/evl_questions'
    answer_files_folder = f'/home/data_sld/chart/result_of_humancheck_evl'
    question_prompt_json = load_json_file(args.question_prompt)
    model_name = args.model_path.split('/')[-1]

    if data_type == "datachart":
        image_folder = "/home/data_sld/datachart_v2_human_check"
    elif data_type =="flow":
        image_folder = "/home/data_sld/flowchart_V1_human_check"
    else:
        print("Input right datatype!")
        return
    
    if args.experiment_name == 'multi_choice':
        question_file = os.path.join(json_files_folder, f'{data_type}_choice_evl_humancheck.json')
        answers_file = os.path.join(answer_files_folder, f'{data_type}_choice_evl_humancheck_by_{model_name}.json')
        question_prompt = question_prompt_json[0]['multi_choice_question_prompt']
    elif args.experiment_name == 'true_false':
        question_file = os.path.join(json_files_folder, f'{data_type}_tof_evl_humancheck.json')
        answers_file = os.path.join(answer_files_folder, f'{data_type}_tof_evl_humancheck_by_{model_name}.json')
        question_prompt = question_prompt_json[1]['true_false_question_prompt']
    elif args.experiment_name == 'open_end':
        question_file = os.path.join(json_files_folder, f'{data_type}_oe_evl_humancheck.json')
        answers_file = os.path.join(answer_files_folder, f'{data_type}_oe_evl_humancheck_by_{model_name}.json')
        question_prompt = question_prompt_json[2]['open_end_question_prompt']
    else:
        print("No such experiment!")
        return
    
    os.makedirs(answer_files_folder, exist_ok=True)
    print(f"Loading file {question_file}.............")
    print(f"Running {args.experiment_name} experiment by {model_name}.........")
    print(f'Saving file {answers_file}..........')

    disable_torch_init()
    model_path =(args.model_path)
    model_name = get_model_name_from_path(model_path)
    tokenizer, model, image_processor, context_len = load_pretrained_model(model_path, args.model_base, model_name)
    json_path = question_file
    json_results = load_json_file(json_path)
    
    # question = "Please classify this input chart, which is extracted from research papers,by choosing one of the following categories and output the corresponding option:\
    # 1.Bar chart, 2.Line chart, 3.Scatter plot, 4.Pie chart, 5.Histogram, 6.Box plot, 7.Model structure diagram, 8.Experimental Result chart, 9.Other types.\
    # Do not output irrelevant content, just output the chosen option.The answer is limited to 10 words or less."
    
    question = question_prompt
    mc_qa_dict = []
    for result in tqdm(json_results):
        question_type, image_filename, conversations = extract_from_json_result(result)
        json_question = conversations[0]['value']
        json_answer = conversations[1]['value']
        qs = question
        if question_type == 'Multiple-Choice Questions':
            qs = qs +("Question and options:" + json_question)
        else:
            qs = qs +("Question:" + json_question)
        # print(qs)
        cur_prompt = qs
        image_file = os.path.join(image_folder, image_filename)
        if model.config.mm_use_im_start_end:
            qs = DEFAULT_IM_START_TOKEN + DEFAULT_IMAGE_TOKEN + DEFAULT_IM_END_TOKEN + '\n' + qs
        else:
            qs = DEFAULT_IMAGE_TOKEN + '\n' + qs

        conv = conv_templates[args.conv_mode].copy()
        conv.append_message(conv.roles[0], qs)
        conv.append_message(conv.roles[1], None)
        prompt = conv.get_prompt()

        input_ids = tokenizer_image_token(prompt, tokenizer, IMAGE_TOKEN_INDEX, return_tensors='pt').unsqueeze(0).cuda()
        # image = Image.open(os.path.join(args.image_folder, image_file))
        try:
            #image = Image.open(os.path.join('/bpfs/v2_mnt/HCG/open_source_data/database/hcg_health_skin/', image_file))
            image = Image.open(image_file)
            
        except:
            print('No such image: ', os.path.join(image_folder, image_file))
            continue
        try:
            # YOUR IMAGE LOADING CODE HERE
            image_tensor = image_processor.preprocess(image, return_tensors='pt')['pixel_values'][0]
        except OSError as e:
            print(f"Error loading image: {e}")
            # 继续处理下一个图像
            continue

        stop_str = conv.sep if conv.sep_style != SeparatorStyle.TWO else conv.sep2
        keywords = [stop_str]
        stopping_criteria = KeywordsStoppingCriteria(keywords, tokenizer, input_ids)

        n = 0
        while True:
            with torch.inference_mode():
                output_ids = model.generate(
                    input_ids,
                    images=image_tensor.unsqueeze(0).half().cuda(),
                    do_sample=True if args.temperature > 0 else False,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    num_beams=args.num_beams,
                    # no_repeat_ngram_size=3,
                    max_new_tokens=1024,
                    use_cache=True)

            outputs = tokenizer.batch_decode(output_ids[:, :], skip_special_tokens=True)[0]
            outputs = outputs.strip()
            if outputs.endswith(stop_str):
                outputs = outputs[:-len(stop_str)]
            outputs = outputs.strip()
            n += 1
            if 'itchy' not in outputs:
                break
            if n > 20:
                break

        print(outputs)
        mc_qa_dict.append({
                "type": question_type,
                "image_path": image_filename,
                "conversations": [
                    {
                        "form": "human",
                        "value": json_question.replace('*','').replace('$','')
                    },
                    {
                        "form": "gpt",
                        "value": json_answer.replace('*','').replace('$','')
                    },
                    {
                        "form": model_name,
                        "value": outputs
                    }
                    
                ],
            })
    write_json(mc_qa_dict, answers_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=str, default="/home/data_sld/llava_v1.6-13B")
    parser.add_argument("--model-base", type=str, default=None)
    parser.add_argument("--image_folder", type=str, default="/data/datasets/chart/chartdata/chartimg")
    parser.add_argument("--ori-file", type=str, default="None")
    parser.add_argument("--conv-mode", type=str, default="llava_v1")
    parser.add_argument("--question_prompt", type=str, default="/home/data_sld/chart/chart_classification_caption_jsons/questions_prompt.json")
    parser.add_argument("--json_path",type=str, default="/home/data_sld/chart/open_end.json")
    parser.add_argument("--experiment_name", type=str, default="open_end")
    parser.add_argument("--output_json_path",type=str, default="/home/data_sld/chart/result_of_experiments/open_end_by_llava_v1.6-13B.json")
    parser.add_argument("--num-chunks", type=int, default=1)
    parser.add_argument("--chunk-idx", type=int, default=0)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top_p", type=float, default=1)
    parser.add_argument("--num_beams", type=int, default=1)
    parser.add_argument("--save_json", type=bool, help="save json", default=True)
    args = parser.parse_args()
    eval_model(args)
