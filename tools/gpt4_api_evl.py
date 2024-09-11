import os
import sys
import time
import requests
import base64
import json
from typing import List, Dict

# Define API keys and model names
GPT4_API_KEYs = ["Your KEY"]
CHAT_MODELS = ["Model name"]

class GPT4API:
    _instance = None  

    def __new__(cls, *args, **kwargs):
        """
        Creates an instance of GPT4API class and initializes endpoint and API key.

        Args:
            cls (type): Class object.

        Returns:
            GPT4API: Singleton instance of the GPT4API class.
        """
        if not cls._instance:
            cls.endpoint = "your endpoint"
            cls.api_key = GPT4_API_KEYs[0]
            cls.api_key_id = 0
            cls._instance = super(GPT4API, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __call__(
        self,
        model: str = "gpt-4",
        query: str = "",
        b64enc_image: str = "",
        messages: List[Dict] = [],
        temperature: float = 0.2,
        top_p: float = 0.8,
        automatic_retry: int = 0
    ) -> str:
        """
        Sends a request to the GPT-4 model and retrieves the response, supporting image transmission via Base64 encoding.

        Args:
            model (str, optional): Model used, defaults to "gpt-4".
            query (str, optional): User input text, defaults to an empty string.
            b64enc_image (str, optional): Base64 encoded image, defaults to an empty string.
            messages (List[Dict], optional): List of context messages containing role and content, defaults to an empty list.
            temperature (float, optional): Parameter controlling the randomness of generated text, defaults to 0.2.
            top_p (float, optional): Parameter controlling text diversity, defaults to 0.8.
            automatic_retry (int, optional): Number of automatic retries, defaults to 0.

        Returns:
            str: Text result returned by the GPT-4 model.
        """
        if not messages:
            if not b64enc_image:
                messages = [{"role": "user", "content": query}]
            else:
                messages = [{
                    "role": "user",
                    "content": [
                        {'type': "text", "text": query},
                        {'type': "image_url", "image_url": {"url": f"data:image/png;base64,{b64enc_image}"}}
                    ]
                }]

        retry_times = 0
        while retry_times < automatic_retry + 1:
            retry_times += 1
            try:
                response = requests.post(
                    url=self.endpoint,
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "top_p": top_p,
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
            except KeyboardInterrupt:
                sys.exit(0)
            except Exception as e:
                print(f"Error: {e}")
                continue

            print(f"Response Status Code: {response.status_code}")
            print(response.text)

            if response.status_code == 200:
                choices = response.json().get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
                return "Error"
            else:
                sys.exit(0)
                
        return "Error."


def update_json_file(results, json_path):
    
    """
    Updates the specified JSON file with new results.
    """
    
    with open(json_path, 'w') as json_file:
        json.dump(results, json_file, indent=4)


if __name__ == "__main__":
    API_IN = GPT4API()
    index = 0
    results = []
    question_json_path = './data/evl_questions/datachart_choice_evl.json'
    results_json_file = "./data/result_of_evl/datachart_choice_evl_by_gpt—4o.json"
    
    with open(question_json_path, 'r') as json_file:
            data = json.load(json_file)
            
    for item in data:
        question = """ Prompt """
        
        # question =question = """ 
        #     You are a professional scientific literature analyst specializing in evaluating open-ended answers based on scientific charts, model diagrams, and flowcharts. Your task is to score the answers provided by a vision language model based on the content of the charts or diagrams and the standard answer. Additionally, evaluate how closely the model's output matches the standard answer provided. The scoring scale ranges from 0 to 5 points. Please follow the scoring criteria below.
        #     Open-Ended Answer Scoring Criteria (0-5 points)
        #     5 Points: Comprehensive and Accurate Answer
        #     - Matches the standard answer closely in terms of detail and correctness
        #     - Answer covers all key points and details from the chart or model
        #     - The response includes clear logic and explanations
        #     - Completely aligns with the content of the image and considers all aspects of the image
        #     4 Points: Accurate but Slightly Incomplete Answer
        #     - Matches the standard answer well but with minor omissions or differences
        #     - Answer covers most of the key points and details but may miss some minor information
        #     - The response is logically clear, but explanations might be less detailed
        #     - Mostly aligns with the image content, covering most important information
        #     3 Points: Partially Accurate Answer
        #     - Partially matches the standard answer, with significant deviations in detail or correctness
        #     - Answer covers some key points but has noticeable omissions
        #     - The response is logically adequate but somewhat simplistic or unclear
        #     - Partially aligns with the image content, covering some information but missing many details
        #     2 Points: Answer with Some Errors
        #     - Shows substantial deviation from the standard answer, with major differences in correctness or detail
        #     - Answer covers a few key points but misses many important details
        #     - The response lacks clarity and is somewhat confused
        #     - Somewhat aligns with the image content but contains clear misunderstandings or omissions
        #     1 Point: Mostly Incorrect Answer
        #     - Matches the standard answer poorly, with many inaccuracies or irrelevant information
        #     - Answer fails to cover key points
        #     - The response lacks logical coherence and proper explanation
        #     - Mostly does not align with the image content, with substantial misunderstandings
        #     0 Points: Completely Incorrect or Irrelevant Answer
        #     - Does not match the standard answer at all, with completely incorrect or irrelevant information
        #     - Answer is irrelevant or entirely incorrect regarding the chart or model
        #     - No logical structure, with explanations unrelated to the question
        #     - Completely does not align with the image content
        #     Please score the following:
        #     """
        
        question += " Question: " + str(item["conversations"][0]["value"])
        image_path = "./charts/charts/" + item["image_path"].split("/")[-1]
        image_b64 = str(base64.b64encode(open(image_path, "rb").read()), 'utf-8')
        
        resp = API_IN(
            model="gpt-4o",
            query=question,
            b64enc_image=image_b64
        )

        item["conversations"][2]["value"] = resp
        print(resp)
        
        results.append({
            'type': item["type"],
            "image_path": item["image_path"],
            "conversations": item['conversations'],
        })

        index += 1
        update_json_file(results, results_json_file)
        print(f"Updated JSON with processing results.")
        print(f"Processed items: {index}")
