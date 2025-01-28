import json
import os
import uuid

STORE_FILE_PATH = os.path.join("data", "store.json")


def load_data():
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
    with open(STORE_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def create_meet(title):
    data = load_data()
    new_meet_id = str(uuid.uuid4())
    new_meet = {
        "id": new_meet_id,
        "title": title,
        "topicList": {},
        "topicListUploads": [],
        "events": []
    }
    data["meets"].append(new_meet)
    save_data(data)
    return new_meet_id


def get_meet(meet_id):
    data = load_data()
    for meet in data["meets"]:
        if meet["id"] == meet_id:
            return meet
    return None


def create_event(meet_id, event_name):
    data = load_data()
    for meet in data["meets"]:
        if meet["id"] == meet_id:
            new_event_id = str(uuid.uuid4())
            new_event = {
                "id": new_event_id,
                "eventName": event_name,
                "examTopics": [],
                "participants": [],
                "examImagePaths": [],
                "scoreImagePaths": []
            }
            meet["events"].append(new_event)
            save_data(data)
            return new_event_id
    return None


def get_event(meet_id, event_id):
    data = load_data()
    for meet in data["meets"]:
        if meet["id"] == meet_id:
            for event in meet["events"]:
                if event["id"] == event_id:
                    return event
    return None


def add_topic_list_files(meet_id, file_paths):
    data = load_data()
    for meet in data["meets"]:
        if meet["id"] == meet_id:
            if "topicListUploads" not in meet:
                meet["topicListUploads"] = []
            meet["topicListUploads"].extend(file_paths)
            save_data(data)
            return


def add_exam_files(meet_id, event_id, file_paths):
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


def add_score_files(meet_id, event_id, file_paths):
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


def update_meet_topic_list(meet_id, parsed_topics):
    data = load_data()
    for meet in data["meets"]:
        if meet["id"] == meet_id:
            meet["topicList"] = parsed_topics
            save_data(data)
            return


def update_event_exam_topics(meet_id, event_id, exam_topics):
    data = load_data()
    for meet in data["meets"]:
        if meet["id"] == meet_id:
            for event in meet["events"]:
                if event["id"] == event_id:
                    event["examTopics"] = exam_topics
                    save_data(data)
                    return


def add_participant_scores(meet_id, event_id, participant_scores):
    data = load_data()
    for meet in data["meets"]:
        if meet["id"] == meet_id:
            for event in meet["events"]:
                if event["id"] == event_id:
                    event["participants"].extend(participant_scores)
                    save_data(data)
                    return
                
def update_team_scores(meet_id, event_id, correct_qs, incorrect_qs):
    data = load_data()
    for meet in data["meets"]:
        if meet["id"] == meet_id:
            for event in meet["events"]:
                if event["id"] == event_id:
                    event["teamCorrectQuestions"] = correct_qs
                    event["teamIncorrectQuestions"] = incorrect_qs
                    save_data(data)
                    return


# -------------- OPTIONAL DELETE FUNCTIONS ---------------

def delete_event(meet_id, event_id):
    """
    Removes the event from the specified meet.
    Returns True if found & deleted, False otherwise.
    """
    data = load_data()
    for meet in data["meets"]:
        if meet["id"] == meet_id:
            for i, event in enumerate(meet["events"]):
                if event["id"] == event_id:
                    meet["events"].pop(i)
                    save_data(data)
                    return True
    return False


def delete_participant(meet_id, event_id, student_name, grade_level):
    """
    Removes a participant from the event's participants array,
    matching both studentName and gradeLevel.
    Returns True if found & removed, False otherwise.
    """
    data = load_data()
    for meet in data["meets"]:
        if meet["id"] == meet_id:
            for event in meet["events"]:
                if event["id"] == event_id:
                    participants = event.get("participants", [])
                    for i, p in enumerate(participants):
                        if (p.get("studentName") == student_name and
                            p.get("gradeLevel") == grade_level):
                            participants.pop(i)
                            save_data(data)
                            return True
    return False


# data_manager.py

def update_event_num_questions(meet_id, event_id, num_questions):
    """
    Store num_questions in the event so participants can skip re-entering it for manual scoring.
    """
    data = load_data()
    for meet in data["meets"]:
        if meet["id"] == meet_id:
            for event in meet["events"]:
                if event["id"] == event_id:
                    event["numQuestions"] = num_questions
                    save_data(data)
                    return

