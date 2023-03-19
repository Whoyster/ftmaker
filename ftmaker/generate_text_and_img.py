import openai
import requests
from requests.structures import CaseInsensitiveDict
import json
import os
from tqdm import tqdm

def download_image(image_url, file_name):
    response = requests.get(image_url)
    if response.status_code == 200:
        with open(file_name, 'wb') as f:
            f.write(response.content)
    else:
        print(f"Error: {response.status_code}")

def generate_img(prompt, api_key, image_api_version):
    url = 'https://api.openai.com/v1/images/generations'
    headers = CaseInsensitiveDict()
    headers['Content-Type'] = 'application/json'
    headers['Authorization'] = f'Bearer {api_key}'

    data = {
        'model': image_api_version,
        'prompt': prompt,
        'num_images': 1,
        'size': '256x256',
        'response_format': 'url'
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_data = json.loads(response.text)
        image_url = response_data['data'][0]['url']
        return image_url
    else:
        print(prompt)
        print("Error: No response from generate_img")
        print(f"Error: {response.status_code}")
        print(response.text)
        return None
    
def generate_and_download_img(api_key, image_api_version, image_system_prompt, book_json):
    book_id = book_json['id']
    book_title = book_json['title']
    book_path = os.path.join('results', f"{book_id}_{book_title}", "images")

    if not os.path.exists(book_path):
        os.makedirs(book_path)    

    for idx, page in tqdm(enumerate(book_json["pages"])):
        img_prompt = image_system_prompt + page['img']
        image_url = generate_img(img_prompt, api_key, image_api_version)
        image_file_name = f"{book_id}_{idx}.jpg"
        image_path = os.path.join(book_path, image_file_name)
        download_image(image_url, os.path.join(book_path, image_file_name))
        page["img_path"] = image_path
        book_json["pages"][idx] = page
    
    return book_json


def generate_text(prompt, api_key, text_api_version):
    url = 'https://api.openai.com/v1/chat/completions'
    headers = CaseInsensitiveDict()
    headers['Content-Type'] = 'application/json'
    headers['Authorization'] = f'Bearer {api_key}'

    data = {
        "model": text_api_version,
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_data = json.loads(response.text)
        image_url = response_data['choices'][0]['message']['content']
        return image_url
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def generate_book_json(book_id, prompt, api_key, 
             text_api_version="text-davinci-002", 
             img_api_version="image-alpha-001"):
    
    prompt = prompt
    api_key = api_key
    text_api_version = text_api_version
    img_api_version = img_api_version

    raw_text = generate_text(prompt, api_key, text_api_version)

    if isinstance(raw_text, str) :
        if raw_text[0] != '{':
            print("Error: raw_text is not json format")
            return None

    book_json = json.loads(raw_text)
    book_json['id'] = book_id
    book_json = generate_and_download_img(api_key, img_api_version, book_json)
    
    return book_json