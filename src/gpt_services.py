# src/gpt_services.py
import os
import base64
import json
from openai import OpenAI
from pydantic import BaseModel

from dotenv import load_dotenv
load_dotenv()


class StudentScores(BaseModel):
    correctQuestions: list[int]
    incorrectQuestions: list[int]


# Initialize the client with your API key (loaded from .env or environment variables).
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# We define a helper to find which courses an event covers
def get_event_courses(event_name):
    """
    Return a list of courses for the given event name.
    For example:
      "Individual Algebra" -> ["Algebra"]
      "Frosh-Soph 2-Person" -> ["Algebra", "Geometry"]
      ...
    """
    # You can expand or rename these as you like
    if "Algebra" in event_name and "II" not in event_name:
        return ["Algebra"]
    if "Geometry" in event_name:
        return ["Geometry"]
    if "Algebra II" in event_name:
        return ["Algebra II"]
    if "Precalculus" in event_name:
        return ["Precalculus"]
    if "Frosh-Soph" in event_name:
        return ["Algebra", "Geometry"]
    if "Jr-Sr" in event_name:
        return ["Algebra II", "Precalculus"]
    if "Calculator" in event_name:
        return ["Algebra", "Geometry", "Algebra II", "Precalculus"]
    # fallback
    return []

def parse_topic_list_images(file_paths):
    """
    Sends the uploaded topic list images to GPT-4o-mini, asking for a JSON structure:
    {
      "Algebra": [...],
      "Geometry": [...],
      "Algebra II": [...],
      "Precalculus": [...]
    }
    """

    # 1. Build the "content" array with text + images as data URLs
    content_list = [
        {
            "type": "text",
            "text": (
                "Please parse these images into a JSON with the following format:\n"
                "{\n"
                "  \"Algebra\": [],\n"
                "  \"Geometry\": [],\n"
                "  \"Algebra II\": [],\n"
                "  \"Precalculus\": []\n"
                "}\n\n"
                "Return valid JSON only. No extra commentary."
            ),
        }
    ]

    for path in file_paths:
        # Convert to absolute path under 'uploads/'
        full_path = os.path.join("uploads", path)
        # Read & base64-encode
        with open(full_path, "rb") as f:
            b64_str = base64.b64encode(f.read()).decode("utf-8")
        # Append as an image_url content
        content_list.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{b64_str}"
                }
            }
        )

    # 2. Make the call
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": content_list
                }
            ],
            #max_tokens=700  # Adjust if needed
        )
        # 3. GPT response
        assistant_reply = response.choices[0].message.content
        print("GPT Response:", assistant_reply)


        # Strip any markdown code block formatting
        clean_response = assistant_reply.strip()
        if clean_response.startswith('```'):
            # Remove opening ```json or ``` and closing ```
            clean_response = clean_response.split('\n', 1)[1] if '\n' in clean_response else clean_response[3:]
            clean_response = clean_response.rsplit('\n', 1)[0] if '\n' in clean_response else clean_response[:-3]
            clean_response = clean_response.strip()
            print(f"Cleaned response: {clean_response[:200]}...")  # Print first 200 chars
        assistant_reply = clean_response

        # 4. Parse as JSON
        parsed_data = json.loads(assistant_reply)
        return parsed_data
    except Exception as e:
        print("Error calling GPT for parse_topic_list_images:", e)
        return {
            "Algebra": [],
            "Geometry": [],
            "Algebra II": [],
            "Precalculus": []
        }



def parse_exam_images(file_paths, known_topic_list, event_name=""):
    """
    We adapt the prompt to say:
    'This exam is on the <courses> topics.'
    Then we require 2-4 topics per question.
    """
    # Determine courses from event name
    courses = get_event_courses(event_name)
    courses_str = ", ".join(courses) if courses else "various"

    images_b64 = []
    for path in file_paths:
        full_path = os.path.join("uploads", path)
        with open(full_path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("utf-8")
            images_b64.append({"filename": path, "content_b64": b64_data})

    system_prompt = (
        "You are an AI that reads exam images (base64), "
        "identifies each question number, and tags them with 2-4 relevant math topics.\n"
        "Return valid JSON only.\n"
    )

    # We embed the event's courses in the user message
    user_text = (
        f"This exam is on the {courses_str} topics. We also have a known topic list to guide labeling.\n"
        "Please identify each question (questionNumber) and list 2-4 relevant topics, returning valid JSON only.\n"
        "Example:\n"
        "[\n  {\"questionNumber\": 1, \"topics\": [\"Algebra - Factoring\", \"Geometry - angle measure\"]},\n  ...\n]\n\n"
        f"Known topic list for reference: {json.dumps(known_topic_list)}"
    )

    content_list = [
        {"type": "text", "text": user_text},
    ]

    for path in file_paths:
        full_path = os.path.join("uploads", path)
        with open(full_path, "rb") as f:
            b64_str = base64.b64encode(f.read()).decode("utf-8")
        content_list.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{b64_str}"
                }
            }
        )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": content_list
                }
            ],
            temperature = .2
            #max_tokens=700
        )
        assistant_reply = response.choices[0].message.content
        print("GPT Response:", assistant_reply)

        # Strip any markdown code block formatting
        clean_response = assistant_reply.strip()
        if clean_response.startswith('```'):
            # Remove opening ```json or ``` and closing ```
            clean_response = clean_response.split('\n', 1)[1] if '\n' in clean_response else clean_response[3:]
            clean_response = clean_response.rsplit('\n', 1)[0] if '\n' in clean_response else clean_response[:-3]
            clean_response = clean_response.strip()
            print(f"Cleaned response: {clean_response[:200]}...")  # Print first 200 chars
        assistant_reply = clean_response

        parsed_data = json.loads(assistant_reply)
        return parsed_data
    except Exception as e:
        print("Error calling GPT for parse_exam_images:", e)
        return []


def parse_single_student_exam_image(file_path, known_exam_data):
    """
    Given ONE student's single exam answer sheet image and the event's known exam data
    (which question corresponds to which topics),
    ask GPT which questions were correct/incorrect/unattempted.

    Return a JSON structure, for example:
    {
      "correctQuestions": [1, 2, 5],
      "incorrectQuestions": [3],
    }
    """

    # Convert file path to base64
    full_path = os.path.join("uploads", file_path)
    with open(full_path, "rb") as f:
        b64_str = base64.b64encode(f.read()).decode("utf-8")

    # Build the content array (text + image)
    content_list = [
        {
            "type": "text",
            "text": ("Here is a graded student answer sheet. The question is correct if there is a check and/or a c next to it. If there is an x, it is incorrect. The number of questions correct should match the number correct listed at the top right. Respond with a json."
            )
        },
        # {
        #     "type": "text",
        #     "text": f"known_exam_data:\n{json.dumps(known_exam_data)}"
        # },
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{b64_str}"
            }
        }
    ]

    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": content_list
                }
            ],
            response_format = StudentScores,
            temperature = 0
        )
        assistant_reply = response.choices[0].message.content
        print("GPT Response:", assistant_reply)

        # Strip any markdown formatting
        clean_response = assistant_reply.strip()
        if clean_response.startswith("```"):
            # Remove opening ```... and trailing ```
            parts = clean_response.split("\n", 1)
            if len(parts) > 1:
                clean_response = parts[1]
            # Remove the last block if it ends with ```
            if "```" in clean_response:
                clean_response = clean_response.split("```", 1)[0]
            clean_response = clean_response.strip()

        parsed_data = json.loads(clean_response)
        return parsed_data
    except Exception as e:
        print("Error calling GPT for parse_single_student_exam_image:", e)
        # Return a default if GPT fails
        return {
            "correctQuestions": [],
            "incorrectQuestions": [],
        }