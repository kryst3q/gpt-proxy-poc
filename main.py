import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
import weaviate
import openai
import logging
from transformers import AutoTokenizer
import math
import re

from weaviate import ConsistencyLevel

load_dotenv()

OPEN_AI_KEY = os.getenv('OPEN_AI_KEY')
WEAVIATE_URL = os.getenv('WEAVIATE_URL')

app = FastAPI()
client = weaviate.Client(
    url=WEAVIATE_URL,
    additional_headers={
        "X-OpenAI-Api-Key": OPEN_AI_KEY
    }
)
openai.api_key = OPEN_AI_KEY
tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")


@app.post("/summary")
async def answer(request: Request):
    data = await request.json()
    countries = data['countries']
    response = []
    for country in countries:
        results = client.query.get("FeedItem", ["summary", "link"]).with_ask(
            {"question": "Provide me information about economic situation of " + country}).with_limit(3).do()

        messages = [
            {"role": "system",
             "content": "Your task is to prepare a summary of informations about given country from economic perspective. Omit informations about culture and history of the given country. The summary is intended to be purely informative. Do not use suggestions, commands or prohibitions. The summary must fit within 260 characters."}
        ]
        content = ""
        links = []

        for result in results["data"]["Get"]["FeedItem"]:
            content += result["summary"]
            if "link" in result:
                links.append(result["link"])

        content_tokens = len(tokenizer.encode(content))
        max_tokens = 3097
        instruction = "Provide me a summary of the following text: "

        if content_tokens > max_tokens:
            parts_number = math.ceil(content_tokens / max_tokens)
            messages.append({"role": "user", "content": instruction + split_into_parts(content, parts_number)[0]})
        else:
            messages.append({"role": "user", "content": instruction + content})

        chat_response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        summary = chat_response['choices'][0]['message']['content']
        dangerous_level = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[
            {"role": "system",
             "content": "Based on provided text evaluate the level of making business in given country. Evaluation must be an integer between 1 and 10, where 1 is most secure and 10 is most dangerous. Return only integer evaluation in response and no other text! Don't use any words in response."},
            {"role": "user", "content": summary}
        ])
        response.append({
            "country": country,
            "summary": summary,
            "links": links,
            "dangerous_level": dangerous_level['choices'][0]['message']['content']
        })

    return response


@app.get("/articles")
async def articles():
    results = client.query.get("FeedItem", ["title", "content", "summary"]).with_additional(['id']).do()
    response = []

    print("test", results)

    for result in results["data"]["Get"]["FeedItem"]:
        response.append({
            "id": result["_additional"]["id"],
            "title": result["title"],
            "content": result["content"],
            "summary": result["summary"]
        })

    return response


@app.post("/articles")
async def add_article(request: Request):
    data = await request.json()

    properties = {
        'title': data["title"],
        'content': data["content"],
        'summary': summarize(data["content"])
    }

    print(properties)

    try:
        data_uuid = client.data_object.create(
            properties,
            "FeedItem"
        )

    except Exception as e:
        return {"status": "error", "message": str(e)}

    return {"status": "ok", "id": data_uuid}


@app.put("/articles/{id}")
async def update_article(id: str, request: Request):
    data = await request.json()

    properties = {
        'title': data["title"],
        'content': data["content"],
        'summary': summarize(data["content"])
    }

    try:
        client.data_object.update(
            properties,
            class_name="FeedItem",
            uuid=id,
            consistency_level=ConsistencyLevel.ALL
        )

    except Exception as e:
        return {"status": "error", "message": str(e)}

    return {"status": "ok"}


@app.delete("/articles/{id}")
async def delete_article(id: str):
    try:
        client.data_object.delete(
            id,
            class_name="FeedItem",
            consistency_level=ConsistencyLevel.ALL
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}

    return {"status": "ok"}


def split_into_parts(text, num_parts):
    # Split the text into sentences using regular expressions
    sentences = re.split(r'(?<=\w\.)\s+', text)

    # Calculate the number of sentences per part
    sentences_per_part = len(sentences) // num_parts

    # Initialize a list to store the parts
    parts = []

    # Loop through each part
    for i in range(num_parts):
        # Calculate the start and end indices for the current part
        start = i * sentences_per_part
        end = (i + 1) * sentences_per_part

        # Ensure that the end index falls at the end of a sentence
        while end < len(sentences) and not sentences[end].endswith('.'):
            end += 1

        # Add the sentences for the current part to the parts list
        part = ' '.join(sentences[start:end])
        parts.append(part)

    return parts


def summarize(text):
    content_tokens = len(tokenizer.encode(text))
    max_tokens = 3097

    if content_tokens > max_tokens:
        parts_number = math.ceil(content_tokens / max_tokens)
        text = split_into_parts(text, parts_number)[0]

    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[
        {"role": "system",
         "content": "Your task is to prepare a summary of a text provided by user. The summary is intended to be purely informative. Do not use suggestions, commands or prohibitions. The summary must fit within 280 characters."},
        {"role": "user",
         "content": "Provide me a summary of the following text: " + text}
    ])

    return response['choices'][0]['message']['content']
