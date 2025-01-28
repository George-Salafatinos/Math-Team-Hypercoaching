# dashboard_logic.py

from src.data_manager import load_data

def get_topic_accuracy_across_meets():
    """
    Returns a dict of:
    {
      "Algebra": {"correct": X, "attempted": Y, "accuracy": 0.??},
      "Geometry": {"correct": ..., "attempted": ..., "accuracy": ...},
      ...
    }
    
    We consider a question 'attempted' if it appears in participant["correctQuestions"] or participant["incorrectQuestions"].
    If a question is never listed, you can treat it as unattempted (some teams do that as incorrect, depends on your logic).
    """
    data = load_data()

    # We'll accumulate stats like: topic_stats[topic] = {"correct": 0, "attempted": 0}
    topic_stats = {}

    for meet in data["meets"]:
        for event in meet["events"]:
            exam_topics = event.get("examTopics", [])
            # Build a quick map: questionNumber -> list_of_topics
            question_to_topics = {}
            for q in exam_topics:
                q_num = q["questionNumber"]
                question_to_topics[q_num] = q["topics"]  # e.g. ["Algebra - Factoring", ...]

            # For each participant, see which questions they got correct, incorrect
            for participant in event.get("participants", []):
                correct_qs = participant.get("correctQuestions", [])
                incorrect_qs = participant.get("incorrectQuestions", [])
                # If you consider unattempted as incorrect, they won't appear in either list, so no "attempted".
                # Or if you consider unattempted as "incorrect," you'd combine them. (But let's keep your logic: only correct or incorrect.)
                
                # For each correct question:
                for q_num in correct_qs:
                    # Add +1 to "correct" AND +1 to "attempted" for all topics of that question
                    if q_num in question_to_topics:
                        these_topics = question_to_topics[q_num]
                        for topic in these_topics:
                            if topic not in topic_stats:
                                topic_stats[topic] = {"correct": 0, "attempted": 0}
                            topic_stats[topic]["correct"] += 1
                            topic_stats[topic]["attempted"] += 1

                # For each incorrect question:
                for q_num in incorrect_qs:
                    if q_num in question_to_topics:
                        these_topics = question_to_topics[q_num]
                        for topic in these_topics:
                            if topic not in topic_stats:
                                topic_stats[topic] = {"correct": 0, "attempted": 0}
                            # incorrect means +0 correct, but +1 attempted
                            topic_stats[topic]["attempted"] += 1

    # Finally, compute accuracy = correct/attempted for each topic
    for topic, stats in topic_stats.items():
        c = stats["correct"]
        a = stats["attempted"]
        accuracy = float(c) / a if a > 0 else 0.0
        stats["accuracy"] = accuracy

    return topic_stats


def get_event_scores_summary():
    """
    Returns a list of event summaries. For each event:
    {
      "meetTitle": "...",
      "eventName": "...",
      "totalQuestions": N,
      "totalCorrect": M,
      "totalParticipants": P
    }
    
    So you can show "Event: Individual Algebra, total Q=10, total correct=24, participants=5, etc."
    """
    data = load_data()
    summaries = []

    for meet in data["meets"]:
        meet_title = meet["title"]
        for event in meet["events"]:
            event_name = event.get("eventName", "Unnamed Event")
            exam_topics = event.get("examTopics", [])
            # Figure out how many distinct questions in examTopics
            all_q_nums = [q["questionNumber"] for q in exam_topics]
            total_questions = len(all_q_nums)

            # Sum total correct
            total_correct = 0
            participants_list = event.get("participants", [])
            for participant in participants_list:
                # correctQuestions might overlap or might be out-of-range, but typically not
                total_correct += len(participant.get("correctQuestions", []))

            summary_item = {
                "meetTitle": meet_title,
                "eventName": event_name,
                "totalQuestions": total_questions,
                "totalCorrect": total_correct,
                "totalParticipants": len(participants_list)
            }
            summaries.append(summary_item)

    return summaries


def get_individual_breakdowns():
    """
    Return a list of participants across all meets/events with their overall stats:
    [
      {
        "studentName": "Alice",
        "gradeLevel": "freshman",
        "meetsEventsParticipated": X,
        "totalCorrect": Y,
        "totalQuestionsAttempted": Z
      },
      ...
    ]

    We'll identify a participant by (studentName, gradeLevel) combo. 
    We'll accumulate stats across meets & events.
    """
    data = load_data()
    # We'll store partial data in a dict keyed by (studentName, gradeLevel)
    participants_map = {}

    for meet in data["meets"]:
        for event in meet["events"]:
            exam_topics = event.get("examTopics", [])
            question_numbers = [q["questionNumber"] for q in exam_topics]
            total_questions_for_event = len(question_numbers)

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
                # If you treat unattempted as a third category or as incorrect is up to you.
                # We'll count "attempted" as correct+incorrect for simplicity.
                # If you want to count "all possible questions" for the event, do that instead.

                # We'll define "totalQuestionsAttempted" = correct + incorrect
                p_data["totalCorrect"] += len(correct_qs)
                p_data["totalQuestionsAttempted"] += (len(correct_qs) + len(incorrect_qs))

    # Now convert that map into a list
    breakdowns = []
    for key, val in participants_map.items():
        breakdowns.append(val)

    return breakdowns
