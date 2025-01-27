import json
import os
import uuid

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
        "topicListUploads": [],  # We'll store file paths here
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


def create_event(meet_id, event_name):
    """
    Creates a new event within the specified meet using the given event_name.
    Returns the newly generated event's ID, or None if meet not found.
    """
    data = load_data()
    for meet in data["meets"]:
        if meet["id"] == meet_id:
            new_event_id = str(uuid.uuid4())
            new_event = {
                "id": new_event_id,
                "eventName": event_name,
                "examTopics": [],
                "participants": [],
                "examImagePaths": [],  # store exam file paths
                "scoreImagePaths": []  # store score sheet file paths
            }
            meet["events"].append(new_event)
            save_data(data)
            return new_event_id
    return None


def get_event(meet_id, event_id):
    """
    Returns the event object from the specified meet, or None if not found.
    """
    data = load_data()
    for meet in data["meets"]:
        if meet["id"] == meet_id:
            for event in meet["events"]:
                if event["id"] == event_id:
                    return event
    return None


# NEW FUNCTIONS FOR STORING FILE PATHS:

def add_topic_list_files(meet_id, file_paths):
    """
    Appends the given file paths to the 'topicListUploads' field in the specified meet.
    """
    data = load_data()
    for meet in data["meets"]:
        if meet["id"] == meet_id:
            if "topicListUploads" not in meet:
                meet["topicListUploads"] = []
            meet["topicListUploads"].extend(file_paths)
            save_data(data)
            return
    # If meet not found, do nothing (or raise an error if desired)


def add_exam_files(meet_id, event_id, file_paths):
    """
    Appends the given file paths to the 'examImagePaths' for the specified event.
    """
    data = load_data()
    for meet in data["meets"]:
        if meet["id"] == meet_id:
            for event in meet["events"]:
                if event["id"] == event_id:
                    if "examImagePaths" not in event:
                        event["examImagePaths"] = []
                    event["examImagePaths"].extend(file_paths)
                    save_data(data)
                    return
    # If not found, do nothing (or handle error)


def add_score_files(meet_id, event_id, file_paths):
    """
    Appends the given file paths to the 'scoreImagePaths' for the specified event.
    """
    data = load_data()
    for meet in data["meets"]:
        if meet["id"] == meet_id:
            for event in meet["events"]:
                if event["id"] == event_id:
                    if "scoreImagePaths" not in event:
                        event["scoreImagePaths"] = []
                    event["scoreImagePaths"].extend(file_paths)
                    save_data(data)
                    return
    # If not found, do nothing (or handle error)
