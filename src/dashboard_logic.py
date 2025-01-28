# src/dashboard_logic.py

import os
import json
from src.data_manager import load_data

TEAM_EVENTS = {
    "Frosh-Soph 2-Person",
    "Jr-Sr 2-Person",
    "Frosh-Soph 8-person",
    "Jr-Sr 8-person",
    "Calculator Team"
}

def get_topic_accuracy_across_meets(skip_team_events=False):
    """
    If skip_team_events=True, we ignore any meets' events that are in TEAM_EVENTS.
    We accumulate question-level stats: topic_stats[topic] = {"correct": X, "attempted": Y, "accuracy": float}
    Return a dict of topics to stats.
    """
    data = load_data()
    topic_stats = {}

    for meet in data["meets"]:
        for event in meet["events"]:
            event_name = event.get("eventName", "")
            # skip if user requests skipping team events
            if skip_team_events and event_name in TEAM_EVENTS:
                continue

            exam_topics = event.get("examTopics", [])
            question_to_topics = {}
            for q in exam_topics:
                q_num = q["questionNumber"]
                question_to_topics[q_num] = q["topics"]

            for participant in event.get("participants", []):
                correct_qs = participant.get("correctQuestions", [])
                incorrect_qs = participant.get("incorrectQuestions", [])
                for q_num in correct_qs:
                    if q_num in question_to_topics:
                        for topic in question_to_topics[q_num]:
                            topic_stats.setdefault(topic, {"correct": 0, "attempted": 0})
                            topic_stats[topic]["correct"] += 1
                            topic_stats[topic]["attempted"] += 1
                for q_num in incorrect_qs:
                    if q_num in question_to_topics:
                        for topic in question_to_topics[q_num]:
                            topic_stats.setdefault(topic, {"correct": 0, "attempted": 0})
                            topic_stats[topic]["attempted"] += 1

    # finalize accuracy
    for topic, stats in topic_stats.items():
        c = stats["correct"]
        a = stats["attempted"]
        stats["accuracy"] = float(c) / a if a > 0 else 0.0

    return topic_stats


def get_event_scores_summary():
    """
    Return a list of:
    {
      "meetTitle": ...,
      "eventName": ...,
      "totalQuestions": ...,
      "totalCorrect": ...,
      "totalParticipants": ...
    }
    We'll handle sorting in app.py.
    """
    data = load_data()
    summaries = []

    for meet in data["meets"]:
        meet_title = meet["title"]
        for event in meet["events"]:
            event_name = event.get("eventName", "Unnamed Event")
            exam_topics = event.get("examTopics", [])
            total_questions = len(exam_topics)

            total_correct = 0
            participants_list = event.get("participants", [])
            for participant in participants_list:
                total_correct += len(participant.get("correctQuestions", []))

            summaries.append({
                "meetTitle": meet_title,
                "eventName": event_name,
                "totalQuestions": total_questions,
                "totalCorrect": total_correct,
                "totalParticipants": len(participants_list)
            })

    return summaries


def get_individual_breakdowns(skip_team_events=False):
    """
    Return a list of participants across all meets/events with overall stats, skipping team events if desired.
    e.g. [
      {
        "studentName": "...",
        "gradeLevel": "...",
        "meetsEventsParticipated": X,
        "totalCorrect": Y,
        "totalQuestionsAttempted": Z
      },
      ...
    ]
    """
    data = load_data()
    participants_map = {}

    for meet in data["meets"]:
        for event in meet["events"]:
            event_name = event.get("eventName", "")
            if skip_team_events and event_name in TEAM_EVENTS:
                continue

            exam_topics = event.get("examTopics", [])
            for participant in event.get("participants", []):
                key = (participant["studentName"], participant["gradeLevel"])
                if key not in participants_map:
                    participants_map[key] = {
                        "studentName": participant["studentName"],
                        "gradeLevel": participant["gradeLevel"],
                        "meetsEventsParticipated": 0,
                        "totalCorrect": 0,
                        "totalQuestionsAttempted": 0
                    }

                p_data = participants_map[key]
                p_data["meetsEventsParticipated"] += 1

                correct_qs = participant.get("correctQuestions", [])
                incorrect_qs = participant.get("incorrectQuestions", [])
                p_data["totalCorrect"] += len(correct_qs)
                p_data["totalQuestionsAttempted"] += (len(correct_qs) + len(incorrect_qs))

    return list(participants_map.values())
