import os
import oss2
from openai import OpenAI
import uuid
import re
import json
from http import HTTPStatus
from dashscope import Application
import dashscope
import cv2
import numpy as np
from paddleocr import PaddleOCR

# Set DashScope base URL
dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'

# OSS credentials
access_key_id = "LTAI5tEJDP5DZBKML4Y8svJH"
access_key_secret = "duccPZm9rOqrhibOnl9YV1zfkZ0pt1"
endpoint = "oss-ap-southeast-1.aliyuncs.com"
bucket_name = "essay-sight-bucket"

auth = oss2.Auth(access_key_id, access_key_secret)
bucket = oss2.Bucket(auth, endpoint, bucket_name)

def upload_to_oss(local_file_path):
    filename = f"uploads/{uuid.uuid4().hex}_{os.path.basename(local_file_path)}"
    bucket.put_object_from_file(filename, local_file_path)
    return f"https://{bucket_name}.{endpoint}/{filename}"

def extract_text(image_path):
    image_url = upload_to_oss(image_path)
    system_prompt = """You are a visual OCR engine for grading the image. Your task is to transcribe handwritten text from images. 
        You must extract the text *exactly* as it appears - including misspellings, casing, punctuation, and spacing. 
        Do NOT correct spelling or grammar. Do NOT interpret what the user intended. 
        Important: Use '\n' (a newline character) after each handwritten line in the image.Use another '\n\n' after each paragraph
        Simply copy the handwritten letters exactly, even if they are misspelled or grammatically incorrect."""

    client = OpenAI(
        api_key="sk-cbcfd01d86a74ec2a93e1dd9ac5261b2",
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    )

    messages = [
        {
            "role": "system",
            "content": [{"type": "text", "text": system_prompt}]
        },
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": image_url},
                {"type": "text", "text": "Please extract all handwritten text from this essay image and return it as plain English text with Question: question and Answer: answer format.This is a mechanical transcription task. If the handwriting is incomplete, do not try to guess or complete it. For example, if the handwriting says 'notise', you must return 'notise' - not 'notice'.Spelling in the image must be preserved exactly.Add a '\n' at the end of each line as it appears in the image."}
            ]
        }
    ]

    completion = client.chat.completions.create(
        model="qwen-vl-max",
        messages=messages,
        temperature=0
    )

    return completion.choices[0].message.content

def sent_to_agent(prompt_input):
    response = Application.call(
        api_key="sk-6ea3d073fea942d395cbb6b5e708f1ea",
        app_id='0e3b9ac5ce0640b2943314c5855c8e41',
        prompt=prompt_input)

    if response.status_code != HTTPStatus.OK:
        print(f'request_id={response.request_id}')
        print(f'code={response.status_code}')
        print(f'message={response.message}')
        print(f'Refer to: https://www.alibabacloud.com/help/en/model-studio/developer-reference/error-code')
    return response.output.text
def extract_non_json_text(output):
    """
    Extracts all text from the output string except the JSON block.
    """
    match = re.search(r"```json(.*?)```", output, re.DOTALL)
    if match:
        json_block = match.group(0)
        non_json_text = output.replace(json_block, "").strip()
        return non_json_text
    else:
        return output.strip()
def change_to_json(output):
    match = re.search(r"```json(.*?)```", output, re.DOTALL)
    if match:
        json_text = match.group(1).strip()
        try:
            data = json.loads(json_text)
            return data
        except json.JSONDecodeError as e:
            print("? Failed to decode JSON:", e)
    return None

ocr = PaddleOCR(det_db_box_thresh=0.1, det_db_unclip_ratio=1.5, use_angle_cls=True, lang='en')

def interpolate_word_boxes(line_box, line_text, spacing_char=' '):
    words = line_text.strip().split(spacing_char)
    total_chars = sum(len(w) for w in words) + (len(words) - 1)
    if total_chars == 0:
        return []

    box = np.array(line_box)
    top_line = np.linspace(box[0], box[1], num=total_chars + 1)
    bottom_line = np.linspace(box[3], box[2], num=total_chars + 1)

    word_boxes = []
    char_idx = 0
    for word in words:
        chars_in_word = len(word)
        start = char_idx
        end = char_idx + chars_in_word

        word_box = [
            top_line[start],
            top_line[end],
            bottom_line[end],
            bottom_line[start],
        ]
        word_boxes.append({"word": word, "box": word_box})
        char_idx = end + 1

    return word_boxes

def annotate_essay_image(image_path: str, result_1: dict, output_path="annotated.jpg") -> str:
    image = cv2.imread(image_path)
    result = ocr.ocr(image_path, cls=True)

    raw_text = result_1["flattened"]
    output_mark = result_1["full_text"]

    good_part = output_mark['strong_content'] + output_mark['good_vocab_usage']
    bad_part = (
        output_mark['grammar_mistakes'] +
        output_mark['awkward_phrasing'] +
        output_mark['punctuation_mistakes'] +
        output_mark['spelling_mistake']
    )

    para = raw_text.encode('utf-8').decode('unicode_escape').strip().split('\n')

    for line, text in zip(result[0], para):
        box = line[0]
        pts = np.array(box).astype(int)

        matched_label = None
        matched_color = None

        for part in bad_part:
            if part.strip() in text:
                matched_label = "Needs Improvement"
                matched_color = (0, 0, 255)
                break

        for part in good_part:
            if part.strip() in text:
                matched_label = "Good Content"
                matched_color = (0, 255, 0)
                break

        if matched_label:
            bottom_left = tuple(pts[3])
            bottom_right = tuple(pts[2])
            cv2.line(image, bottom_left, bottom_right, matched_color, thickness=2)
            label_pos = (pts[0][0], max(pts[0][1] - 10, 10))
            cv2.putText(image, matched_label, label_pos, cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, matched_color, 1, cv2.LINE_AA)

    h, w, _ = image.shape
    font_scale = 0.4
    line_height = 15
    x_pos = 10
    y_pos = h - 300

    feedback_texts = [
        ("Strong Content:", output_mark['strong_content'], (0, 255, 0)),
        ("Good Vocabulary:", output_mark['good_vocab_usage'], (0, 255, 0)),
        ("Grammar Mistakes:", output_mark['grammar_mistakes'], (0, 0, 255)),
        ("Awkward Phrasing:", output_mark['awkward_phrasing'], (0, 0, 255)),
        ("Punctuation Mistakes:", output_mark['punctuation_mistakes'], (0, 0, 255)),
        ("Spelling Mistakes:", output_mark['spelling_mistake'], (0, 0, 255)),
    ]

    for title, items, color in feedback_texts:
        cv2.putText(image, title, (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 1, cv2.LINE_AA)
        y_pos += line_height
        for item in items:
            text_line = f"- {item[:40]}..." if len(item) > 40 else f"- {item}"
            cv2.putText(image, text_line, (x_pos + 10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 1, cv2.LINE_AA)
            y_pos += line_height

    cv2.imwrite(output_path, image)
    print(f"? Annotated image saved to: {output_path}")

    # Upload to OSS and return the public URL
    annotated_url = upload_to_oss(output_path)
    return annotated_url
