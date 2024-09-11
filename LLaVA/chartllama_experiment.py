##############################
# task:chartllama Reasoning
# author:qgq
# time:2024.07.25
##############################
import argparse
import torch
import os
import json
from tqdm import tqdm
import shortuuid
import warnings
import shutil
import time
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig, BitsAndBytesConfig
from llava.constants import IMAGE_TOKEN_INDEX, DEFAULT_IMAGE_TOKEN, DEFAULT_IM_START_TOKEN, DEFAULT_IM_END_TOKEN, DEFAULT_IMAGE_PATCH_TOKEN
from llava.conversation import conv_templates, SeparatorStyle
# from llava.model.builder import load_pretrained_model
from llava.model import *
from llava.utils import disable_torch_init
from llava.mm_utils import tokenizer_image_token, process_images, get_model_name_from_path
from torch.utils.data import Dataset, DataLoader

from PIL import Image
import math

def load_json_file(json_path):
    """
    读取json文件
    """
    with open(json_path, encoding='utf-8') as json_file:
        json_strs = json.load(json_file)
    return json_strs

def write_json(dict, output_files):
    with open(output_files, 'w', encoding='utf-8') as file:
        json_str = json.dumps(dict, indent=4)
        file.write(json_str)
    print(f'File {output_files} is wrote done.')

def load_pretrained_model(model_path, model_base, model_name, load_8bit=False, load_4bit=False, device_map="auto", device="cuda"):
    kwargs = {"device_map": device_map}

    if load_8bit:
        kwargs['load_in_8bit'] = True
    elif load_4bit:
        kwargs['load_in_4bit'] = True
        kwargs['quantization_config'] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type='nf4'
        )
    else:
        kwargs['torch_dtype'] = torch.float16
    # ("--model-path", type=str, default='/home/data_sld/chartllama_lora')
    # ("--model-base", type=str, default='/home/data_sld/llava_v1.5-13B')
    # Load LLaVA model
    if model_base is None:
        raise ValueError('There is `lora` in model name but no `model_base` is provided. If you are loading a LoRA model, please provide the `model_base` argument. Detailed instruction: https://github.com/haotian-liu/LLaVA#launch-a-model-worker-lora-weights-unmerged.')
    if model_base is not None:
        lora_cfg_pretrained = AutoConfig.from_pretrained(model_path)
        tokenizer = AutoTokenizer.from_pretrained(model_base, use_fast=False)
        print('Loading LLaVA from base model...')
        
        model = LlavaLlamaForCausalLM.from_pretrained(model_base, low_cpu_mem_usage=True, config=lora_cfg_pretrained, **kwargs)
        token_num, tokem_dim = model.lm_head.out_features, model.lm_head.in_features
        if model.lm_head.weight.shape[0] != token_num:
            model.lm_head.weight = torch.nn.Parameter(torch.empty(token_num, tokem_dim, device=model.device, dtype=model.dtype))
            model.model.embed_tokens.weight = torch.nn.Parameter(torch.empty(token_num, tokem_dim, device=model.device, dtype=model.dtype))

        print('Loading additional LLaVA weights...')
        if os.path.exists(os.path.join(model_path, 'non_lora_trainables.bin')):
            non_lora_trainables = torch.load(os.path.join(model_path, 'non_lora_trainables.bin'), map_location='cpu')
        else:
            # this is probably from HF Hub
            from huggingface_hub import hf_hub_download
            def load_from_hf(repo_id, filename, subfolder=None):
                cache_file = hf_hub_download(
                    repo_id=repo_id,
                    filename=filename,
                    subfolder=subfolder)
                return torch.load(cache_file, map_location='cpu')
            non_lora_trainables = load_from_hf(model_path, 'non_lora_trainables.bin')
        non_lora_trainables = {(k[11:] if k.startswith('base_model.') else k): v for k, v in non_lora_trainables.items()}
        if any(k.startswith('model.model.') for k in non_lora_trainables):
            non_lora_trainables = {(k[6:] if k.startswith('model.') else k): v for k, v in non_lora_trainables.items()}
        model.load_state_dict(non_lora_trainables, strict=False)

        from peft import PeftModel
        print('Loading LoRA weights...')
        model = PeftModel.from_pretrained(model, model_path)
        print('Merging LoRA weights...')
        model = model.merge_and_unload()
        print('Model is loaded...')

    image_processor = None

    mm_use_im_start_end = getattr(model.config, "mm_use_im_start_end", False)
    mm_use_im_patch_token = getattr(model.config, "mm_use_im_patch_token", True)
    if mm_use_im_patch_token:
        tokenizer.add_tokens([DEFAULT_IMAGE_PATCH_TOKEN], special_tokens=True)
    if mm_use_im_start_end:
        tokenizer.add_tokens([DEFAULT_IM_START_TOKEN, DEFAULT_IM_END_TOKEN], special_tokens=True)
    model.resize_token_embeddings(len(tokenizer))

    vision_tower = model.get_vision_tower()
    if not vision_tower.is_loaded:
        vision_tower.load_model()
    vision_tower.to(device=device, dtype=torch.float16)
    image_processor = vision_tower.image_processor

    if hasattr(model.config, "max_sequence_length"):
        context_len = model.config.max_sequence_length
    else:
        context_len = 2048

    return tokenizer, model, image_processor, context_len

def split_list(lst, n):
    """Split a list into n (roughly) equal-sized chunks"""
    chunk_size = math.ceil(len(lst) / n)  # integer division
    return [lst[i:i+chunk_size] for i in range(0, len(lst), chunk_size)]


def get_chunk(lst, n, k):
    chunks = split_list(lst, n)
    return chunks[k]


# Custom dataset class
class CustomDataset(Dataset):
    def __init__(self, questions, image_folder, tokenizer, image_processor, model_config, question_prompt):
        self.questions = questions
        self.image_folder = image_folder
        self.tokenizer = tokenizer
        self.image_processor = image_processor
        self.model_config = model_config
        self.question_prompt = question_prompt

    def __getitem__(self, index):
    #     question = """
    #     You will receive a multiple-choice question related to a chart presented in the input image. The question will have four options, only one of which is correct. It's a closed question, please output only the correct option without providing any additional explanation or information.
    #     For example: 	
    #     Question: According to the chart, which category has the highest percentage?
    #     A. Category A 	
    #     B. Category B 
    #     C. Category C 	
    #     D. Category D  
    #     You should output: B
    #     Please process the following question: 
    #     [ Insert the question and options here along with the image of the chart ]
    # """
        question = self.question_prompt
        line = self.questions[index]
        image_file = line["image_path"]
        question_type = line["type"]

        qs = line["conversations"][0]['value'].replace(DEFAULT_IMAGE_TOKEN, '').strip()
        # if question_type == "Multiple-Choice Questions":
        #     qs = question + ("Question and options:" + qs) #选择题时使用这个
        # else:
        #     qs = question + ("Question:" + qs)
        qs = question + qs
        # print(qs)
        if self.model_config.mm_use_im_start_end:
            qs = DEFAULT_IM_START_TOKEN + DEFAULT_IMAGE_TOKEN + DEFAULT_IM_END_TOKEN + '\n' + qs
        else:
            qs = DEFAULT_IMAGE_TOKEN + '\n' + qs
        # print(qs)
        conv = conv_templates[args.conv_mode].copy()
        conv.append_message(conv.roles[0], qs)
        conv.append_message(conv.roles[1], None)
        prompt = conv.get_prompt()
        # print(prompt)
        image_path = os.path.join(self.image_folder, image_file)
        if os.path.exists(image_path):
            image = Image.open(image_path).convert('RGB')
        else:
            image = Image.new('RGB', (448, 448), (0, 0, 0))
            print(f'File {image_path} not exist.')
        image_tensor = process_images([image], self.image_processor, self.model_config)[0]
        input_ids = tokenizer_image_token(prompt, self.tokenizer, IMAGE_TOKEN_INDEX, return_tensors='pt')
        return input_ids, image_tensor

    def __len__(self):
        return len(self.questions)


# DataLoader
def create_data_loader(questions, image_folder, tokenizer, image_processor, model_config, question_prompt, batch_size=1, num_workers=4):
    assert batch_size == 1, "batch_size must be 1"
    dataset = CustomDataset(questions, image_folder, tokenizer, image_processor, model_config, question_prompt)
    data_loader = DataLoader(dataset, batch_size=batch_size, num_workers=num_workers, shuffle=False)
    return data_loader


def eval_model(args):
    cuda_ids = "0, 1, 2, 3"
    os.environ['CUDA_VISIBLE_DEVICES'] = cuda_ids
    # Model
    disable_torch_init()
    # data_type = args.data_type
    data_type = input("Pleace input datatype!<<<<<<<<< flow or datachart or datachart_flow>>>>>>>>>>>>")
    
    answer_files_folder = f'/home/data_sld/chart/result_of_test'
    question_prompt_json = load_json_file(args.question_prompt)
    model_name = args.model_path.split('/')[-1]
    os.makedirs(answer_files_folder, exist_ok=True)
    if data_type == "datachart":
        image_folder = "/home/data_sld/chart/test/d_test_images"
        json_files_folder = "/home/data_sld/chart/test/d_test"
    elif data_type =="flow":
        image_folder = "/home/data_sld/chart/test/f_test_images"
        json_files_folder = "/home/data_sld/chart/test/f_test"
    elif data_type =="datachart_flow":
        image_folder = "/home/data_sld/chart/test/df_test_images"
        json_files_folder = "/home/data_sld/chart/test/df_test"
    else:
        return
    
    if args.experiment_name == 'multi_choice':
        question_file = os.path.join(json_files_folder, f'choice_{data_type}.json')
        answers_file = os.path.join(answer_files_folder, f'choice_{data_type}_by_{model_name}.json')
        question_prompt = question_prompt_json[0]['multi_choice_question_prompt']
    elif args.experiment_name == 'true_false':
        question_file = os.path.join(json_files_folder, f'tof_{data_type}.json')
        answers_file = os.path.join(answer_files_folder, f'tof_{data_type}_by_{model_name}.json')
        question_prompt = question_prompt_json[1]['true_false_question_prompt']
    elif args.experiment_name == 'open_end':
        question_file = os.path.join(json_files_folder, f'oe_{data_type}.json')
        answers_file = os.path.join(answer_files_folder, f'oe_{data_type}_by_{model_name}.json')
        question_prompt = question_prompt_json[2]['open_end_question_prompt']
    else:
        print("No such experiment!")
        return
    
    os.makedirs(answer_files_folder, exist_ok=True)
    print(f"Loading file {question_file}.............")
    print(f"Running {args.experiment_name} experiment by {model_name}.........")
    print(f'Saving file {answers_file}..........')
    model_path = os.path.expanduser(args.model_path)
    # model_name = get_model_name_from_path(model_path)
    tokenizer, model, image_processor, context_len = load_pretrained_model(model_path, args.model_base, model_name)

    # questions = [json.loads(q) for q in open(os.path.expanduser(args.question_file), "r")]
    questions = json.load(open(os.path.expanduser(question_file), 'r'))
    questions = get_chunk(questions, args.num_chunks, args.chunk_idx)

    answer_dict = []
    if 'plain' in model_name and 'finetune' not in model_name.lower() and 'mmtag' not in args.conv_mode:
        args.conv_mode = args.conv_mode + '_mmtag'
        print(f'It seems that this is a plain model, but it is not using a mmtag prompt, auto switching to {args.conv_mode}.')
    # question_prompt = load_json_file(args.question_prompt)[2]['open_end_question_prompt']
    data_loader = create_data_loader(questions, image_folder, tokenizer, image_processor, model.config, question_prompt)
    start_time = time.time()
    for (input_ids, image_tensor), line in tqdm(zip(data_loader, questions), total=len(questions)):
        try:
            cur_prompt = line["conversations"][0]['value'].replace(DEFAULT_IMAGE_TOKEN, '').strip()
            q_type = line['type']
            image_file = line['image_path']
            json_question = line['conversations'][0]['value']
            json_response = line['conversations'][1]['value']
            stop_str = conv_templates[args.conv_mode].sep if conv_templates[args.conv_mode].sep_style != SeparatorStyle.TWO else conv_templates[args.conv_mode].sep2
            input_ids = input_ids.to(device='cuda', non_blocking=True)

            with torch.inference_mode():
                output_ids = model.generate(
                    input_ids,
                    images=image_tensor.to(dtype=torch.float16, device='cuda', non_blocking=True),
                    do_sample=True if args.temperature > 0 else False,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    num_beams=args.num_beams,
                    max_new_tokens=1636,
                    use_cache=True)

            input_token_len = input_ids.shape[1]
            outputs = tokenizer.batch_decode(output_ids[:, :], skip_special_tokens=True)[0]
            outputs = outputs.strip()
            if outputs.endswith(stop_str):
                outputs = outputs[:-len(stop_str)]
            outputs = outputs.strip()
            print(outputs)
            answer_dict.append({
                    "type": q_type,
                    "image_path": image_file,
                    "conversations": [
                        {
                            "form": "human",
                            "value": json_question.replace('*','').replace('$','')
                        },
                        {
                            "form": "gpt",
                            "value": json_response.replace('*','').replace('$','')
                        },
                        {
                            "from":model_name,
                            "value":outputs
                        }
                    ],
                })
        except Exception as e:
            print(e)
            continue
    end_time = time.time()
    total_time = end_time - start_time
    averga_time = total_time/len(data_loader)
    # write_json(answer_dict, answers_file)
    print(f'Total time spent:{total_time:.2f}, average time:{averga_time:.2f}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=str, default='/home/data_sld/chartllama_lora')
    parser.add_argument("--model-base", type=str, default='/home/data_sld/llava_v1.5-13B')
    parser.add_argument("--experiment_name", type=str, default="open_end")
    parser.add_argument("--question_prompt", type=str, default="/home/data_sld/chart/chart_classification_caption_jsons/questions_prompt.json")
    parser.add_argument("--conv-mode", type=str, default="v1")
    parser.add_argument("--num-chunks", type=int, default=1)
    parser.add_argument("--chunk-idx", type=int, default=0)
    parser.add_argument("--temperature", type=float, default=0)
    parser.add_argument("--top_p", type=float, default=None)
    parser.add_argument("--num_beams", type=int, default=1)
    args = parser.parse_args()

    eval_model(args)

# CUDA_VISIBLE_DEVICES=1 python -m llava.eval.model_vqa_lora --model-path /home/data_sld/chartllama_lora \
#     --question-file /home/data_sld/chart/multi-choice.json \
#     --image-folder /data/datasets/chart/chartdata/chartimg \
#     --answers-file answer.jsonl \
#     --num-chunks $CHUNKS \
#     --chunk-idx $IDX \
#     --temperature 0 \
#     --conv-mode vicuna_v1 &