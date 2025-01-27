# data_manager.py

import json
import os
import uuid

# Adjust this path if your store.json is located elsewhere
STORE_FILE_PATH = os.path.join("data", "store.json")


def load_data():
    """
    Reads JSON from data/store.json into a Python dictionary and returns it.
    If the file does not exist or is invalid, returns a default structure.
    """
    if not os.path.exists(STORE_FILE_PATH):
        return {"meets": []}

    with open(STORE_FILE_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {"meets": []}
    # Ensure the top-level structure is what we expect
    if "meets" not in data:
        data["meets"] = []
    return data


def save_data(data):
    """
    Writes the Python dictionary back to data/store.json in JSON format.
    """
    with open(STORE_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def create_meet(title):
    """
    Creates a new meet with a unique ID and the given title.
    Initializes empty fields for topicList and events.
    Returns the newly generated meet ID.
    """
    data = load_data()

    new_meet_id = str(uuid.uuid4())
    new_meet = {
        "id": new_meet_id,
        "title": title,
        "topicList": {},  # We'll store parsed topics here eventually
        "events": []
    }

    data["meets"].append(new_meet)
    save_data(data)
    return new_meet_id


def get_meet(meet_id):
    """
    Returns the meet object with the given meet_id, or None if not found.
    """
    data = load_data()
    for meet in data["meets"]:
        if meet["id"] == meet_id:
            return meet
    return None
