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
    Returns a dict: { topic: {"correct": X, "attempted": Y, "accuracy": float, "lost_points": float} }
    across all meets. If skip_team_events=True, team events are ignored.
    """
    data = load_data()
    topic_stats = {}

    for meet in data["meets"]:
        for event in meet["events"]:
            event_name = event.get("eventName", "")
            if skip_team_events and event_name in TEAM_EVENTS:
                continue

            exam_topics = event.get("examTopics", [])
            q2topics = {}
            for item in exam_topics:
                q_num = item["questionNumber"]
                q2topics[q_num] = item["topics"]

            if event_name in TEAM_EVENTS:
                team_correct = event.get("teamCorrectQuestions", [])
                team_incorrect = event.get("teamIncorrectQuestions", [])
                for cq in team_correct:
                    if cq in q2topics:
                        for t in q2topics[cq]:
                            topic_stats.setdefault(t, {"correct": 0, "attempted": 0})
                            topic_stats[t]["correct"] += 1
                            topic_stats[t]["attempted"] += 1
                for iq in team_incorrect:
                    if iq in q2topics:
                        for t in q2topics[iq]:
                            topic_stats.setdefault(t, {"correct": 0, "attempted": 0})
                            topic_stats[t]["attempted"] += 1
            else:
                for participant in event.get("participants", []):
                    correct_qs = participant.get("correctQuestions", [])
                    incorrect_qs = participant.get("incorrectQuestions", [])
                    for cq in correct_qs:
                        if cq in q2topics:
                            for t in q2topics[cq]:
                                topic_stats.setdefault(t, {"correct": 0, "attempted": 0})
                                topic_stats[t]["correct"] += 1
                                topic_stats[t]["attempted"] += 1
                    for iq in incorrect_qs:
                        if iq in q2topics:
                            for t in q2topics[iq]:
                                topic_stats.setdefault(t, {"correct": 0, "attempted": 0})
                                topic_stats[t]["attempted"] += 1

    # Finalize the accuracy and lost_points for each topic.
    for topic, stats in topic_stats.items():
        c = stats["correct"]
        a = stats["attempted"]
        stats["accuracy"] = float(c) / a if a > 0 else 0.0
        # Compute importance as (1 - accuracy**2) * attempted.
        stats["importance"] = (1 - stats["accuracy"]**3)*10*(1-(1/(2*(a+1))))

    return topic_stats


def get_event_scores_summary():
    """
    Returns a list of event summaries (for the entire dashboard):
    [
      {
        "meetTitle": ...,
        "eventName": ...,
        "totalQuestions": ...,
        "totalCorrect": ...,
        "totalParticipants": ...
      },
      ...
    ]
    This now counts correct answers from teamCorrectQuestions for team events,
    and from participants' correctQuestions for individual events.
    """
    data = load_data()
    summaries = []

    for meet in data["meets"]:
        meet_title = meet["title"]
        for event in meet["events"]:
            event_name = event.get("eventName", "Unnamed Event")

            # If you stored examTopics, numQuestions, etc.:
            exam_topics = event.get("examTopics", [])
            # For display, let's define totalQuestions:
            # prefer event["numQuestions"] if present, else fall back to len(exam_topics)
            total_questions = event.get("numQuestions") or len(exam_topics)

            # Distinguish team vs. individual
            if event_name in TEAM_EVENTS:
                # team event => totalCorrect is from event["teamCorrectQuestions"]
                team_correct = event.get("teamCorrectQuestions", [])
                total_correct = len(team_correct)
                total_participants = len(event.get("participants", []))  # Just the # people on the team
            else:
                # individual event => sum participant correct
                total_correct = 0
                participants_list = event.get("participants", [])
                for participant in participants_list:
                    total_correct += len(participant.get("correctQuestions", []))
                total_participants = len(participants_list)

            summaries.append({
                "meetTitle": meet_title,
                "eventName": event_name,
                "totalQuestions": total_questions,
                "totalCorrect": total_correct,
                "totalParticipants": total_participants
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

def get_event_topic_accuracy(meet_id, event_id):
    """
    Returns a dict: topic -> {correct: X, attempted: Y, accuracy: float}
    for a single event (question-level data).
    Ignores teamCorrectQuestions, because that doesn't map to topics easily.
    """
    data = load_data()
    topic_stats = {}
    the_event = None

    for meet in data["meets"]:
        if meet["id"] == meet_id:
            for evt in meet["events"]:
                if evt["id"] == event_id:
                    the_event = evt
                    break
    if not the_event:
        return {}

    exam_topics = the_event.get("examTopics", [])
    # map question->topics
    q2topics = {}
    for item in exam_topics:
        q2topics[item["questionNumber"]] = item["topics"]

    # for each participant (individual event), accumulate correctness
    # if it's a team event and you want to skip participant-level data, do so
    # but let's just do what we do for normal question-level participants.
    for p in the_event.get("participants", []):
        correct_qs = p.get("correctQuestions", [])
        incorrect_qs = p.get("incorrectQuestions", [])
        for cq in correct_qs:
            if cq in q2topics:
                for t in q2topics[cq]:
                    topic_stats.setdefault(t, {"correct": 0, "attempted": 0})
                    topic_stats[t]["correct"] += 1
                    topic_stats[t]["attempted"] += 1
        for iq in incorrect_qs:
            if iq in q2topics:
                for t in q2topics[iq]:
                    topic_stats.setdefault(t, {"correct": 0, "attempted": 0})
                    topic_stats[t]["attempted"] += 1

    # finalize accuracy
    for t, stats in topic_stats.items():
        c = stats["correct"]
        a = stats["attempted"]
        stats["accuracy"] = c / a if a > 0 else 0.0

    return topic_stats
