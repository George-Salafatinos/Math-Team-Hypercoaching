# src/app.py

import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from src.dashboard_logic import get_event_topic_accuracy

load_dotenv()
BASE_UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)

from src.data_manager import (
    load_data,
    create_meet,
    get_meet,
    create_event,
    get_event,
    add_topic_list_files,
    add_exam_files,
    add_score_files,
    update_meet_topic_list,
    update_event_exam_topics,
    add_participant_scores,
    delete_event,
    delete_participant,
    update_event_num_questions,  # new helper
)
from src.gpt_services import (
    parse_topic_list_images,
    parse_exam_images,
    parse_single_student_exam_image
)
from src.dashboard_logic import (
    get_topic_accuracy_across_meets,
    get_event_scores_summary,
    get_individual_breakdowns
)

INDIVIDUAL_EVENTS = {
    "Individual Algebra",
    "Individual Geometry",
    "Individual Algebra II",
    "Individual Precalculus",
}

TEAM_EVENTS = {
    "Frosh-Soph 2-Person",
    "Jr-Sr 2-Person",
    "Frosh-Soph 8-person",
    "Jr-Sr 8-person",
    "Calculator Team"
}

def create_app():
    app = Flask(__name__,
                template_folder="../templates",
                static_folder="../static")
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "some_dev_secret")

    @app.route("/")
    def home_page():
        data = load_data()
        meets = data["meets"]
        return render_template("home.html", meets=meets)

    @app.route("/add_meet", methods=["GET", "POST"])
    def add_meet_route():
        if request.method == "POST":
            title = request.form.get("title")
            if title:
                new_meet_id = create_meet(title)
                flash("Meet created successfully!", "success")
                return redirect(url_for("view_meet", meet_id=new_meet_id))
            else:
                flash("Please enter a valid meet title.", "error")
        return render_template("add_meet.html")

    @app.route("/meet/<meet_id>")
    def view_meet(meet_id):
        meet = get_meet(meet_id)
        if not meet:
            flash("Meet not found.", "error")
            return redirect(url_for("home_page"))
        return render_template("meet.html", meet=meet)

    @app.route("/meet/<meet_id>/create_event", methods=["GET", "POST"])
    def create_event_route(meet_id):
        meet = get_meet(meet_id)
        if not meet:
            flash("Meet not found.", "error")
            return redirect(url_for("home_page"))

        FIXED_EVENTS = sorted(list(INDIVIDUAL_EVENTS | TEAM_EVENTS))

        if request.method == "POST":
            event_name = request.form.get("event_name")
            if event_name in FIXED_EVENTS:
                event_id = create_event(meet_id, event_name)
                if event_id:
                    flash(f"Event '{event_name}' created!", "success")
                    return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))
            flash("Please select a valid event from the list.", "error")
            return redirect(url_for("create_event_route", meet_id=meet_id))

        return render_template("create_event.html",
                               meet_id=meet_id,
                               possible_events=FIXED_EVENTS)

    @app.route("/meet/<meet_id>/event/<event_id>")
    def view_event(meet_id, event_id):
        event = get_event(meet_id, event_id)
        if not event:
            flash("Event not found.", "error")
            return redirect(url_for("view_meet", meet_id=meet_id))

        # Now we compute event-level topic accuracy
        event_topic_stats = get_event_topic_accuracy(meet_id, event_id)
        # sort from lowest to highest
        sorted_topic_stats = sorted(
            event_topic_stats.items(),
            key=lambda x: x[1]["accuracy"]
        )
        chart_labels = [t[0] for t in sorted_topic_stats]
        chart_values = [round(t[1]["accuracy"] * 100, 1) for t in sorted_topic_stats]

        return render_template("event.html",
                            meet_id=meet_id,
                            event=event,
                            event_topic_stats=sorted_topic_stats,
                            chart_labels=chart_labels,
                            chart_values=chart_values)

    @app.route("/meet/<meet_id>/upload_topic_list", methods=["POST"])
    def upload_topic_list(meet_id):
        meet = get_meet(meet_id)
        if not meet:
            flash("Meet not found.", "error")
            return redirect(url_for("home_page"))

        uploaded_files = request.files.getlist("files")
        if not uploaded_files or all(f.filename == "" for f in uploaded_files):
            flash("No files selected.", "error")
            return redirect(url_for("view_meet", meet_id=meet_id))

        saved_file_paths = []
        topic_list_folder = os.path.join(BASE_UPLOAD_FOLDER, "topic_list", meet_id)
        os.makedirs(topic_list_folder, exist_ok=True)

        for file in uploaded_files:
            if file and file.filename:
                original_filename = secure_filename(file.filename)
                unique_name = f"{uuid.uuid4()}_{original_filename}"
                full_path = os.path.join(topic_list_folder, unique_name)
                file.save(full_path)
                relative_path = os.path.relpath(full_path, BASE_UPLOAD_FOLDER)
                saved_file_paths.append(relative_path)

        if saved_file_paths:
            add_topic_list_files(meet_id, saved_file_paths)
            try:
                parsed_topics = parse_topic_list_images(saved_file_paths)
                update_meet_topic_list(meet_id, parsed_topics)
                flash("Topic list uploaded and parsed successfully!", "success")
            except Exception as e:
                flash(f"GPT parse error: {str(e)}", "error")

        return redirect(url_for("view_meet", meet_id=meet_id))


    # ----------Upload Exam Images & Parse Question Topics ----------
    @app.route("/meet/<meet_id>/event/<event_id>/upload_exam", methods=["POST"])
    def upload_exam_images(meet_id, event_id):
        """
        The user uploads the actual exam question photos to parse them with GPT,
        which assigns topics to each questionNumber. We store them in event["examTopics"].
        We also set event["numQuestions"] = the count or max questionNumber from the parse.
        """
        event = get_event(meet_id, event_id)
        if not event:
            flash("Event not found.", "error")
            return redirect(url_for("view_meet", meet_id=meet_id))

        uploaded_files = request.files.getlist("files")
        if not uploaded_files or all(f.filename == "" for f in uploaded_files):
            flash("No exam files selected.", "error")
            return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

        exam_folder = os.path.join(BASE_UPLOAD_FOLDER, "exams", meet_id, event_id)
        os.makedirs(exam_folder, exist_ok=True)

        saved_file_paths = []
        for file in uploaded_files:
            if file and file.filename:
                original_filename = secure_filename(file.filename)
                unique_name = f"{uuid.uuid4()}_{original_filename}"
                full_path = os.path.join(exam_folder, unique_name)
                file.save(full_path)
                relative_path = os.path.relpath(full_path, BASE_UPLOAD_FOLDER)
                saved_file_paths.append(relative_path)

        if saved_file_paths:
            add_exam_files(meet_id, event_id, saved_file_paths)
            from src.data_manager import get_meet
            meet = get_meet(meet_id)
            known_list = meet.get("topicList", {}) if meet else {}
            try:
                exam_data = parse_exam_images(saved_file_paths, known_list, event_name=event.get("eventName",""))
                # store in event["examTopics"]
                update_event_exam_topics(meet_id, event_id, exam_data)

                # set event["numQuestions"] = max questionNumber or length if you prefer
                if exam_data:
                    max_q = max(q["questionNumber"] for q in exam_data)
                    update_event_num_questions(meet_id, event_id, max_q)
                flash("Exam images uploaded & parsed. Topics assigned!", "success")
            except Exception as e:
                flash(f"GPT parse error while uploading exam: {str(e)}", "error")

        return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

    # ---------- Team Scores (Single set for entire team) ----------
    @app.route("/meet/<meet_id>/event/<event_id>/upload_team_scores", methods=["POST"])
    def upload_team_scores(meet_id, event_id):
        from src.data_manager import (
            get_event, update_team_scores, add_score_files
        )

        event_data = get_event(meet_id, event_id)
        if not event_data:
            flash("Event not found.", "error")
            return redirect(url_for("view_meet", meet_id=meet_id))

        event_name = event_data.get("eventName", "")
        if event_name not in TEAM_EVENTS:
            flash("Not a team event, can't upload single team score.", "error")
            return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

        score_mode = request.form.get("scoreMode", "manual")  # default "manual"

        correct_qs = []
        incorrect_qs = []

        if score_mode == "manual":
            # If user never uploaded exam images or never set event["numQuestions"], we might not have it
            num_q = event_data.get("numQuestions", 0)
            if num_q < 1:
                flash("No total # of questions set for this event. Upload exam or set numQuestions manually first!", "error")
                return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

            inc_str = request.form.get("incorrectList")
            inc_set = set()
            if inc_str:
                for item in inc_str.split(","):
                    item = item.strip()
                    if item.isdigit():
                        q_num = int(item)
                        if 1 <= q_num <= num_q:
                            inc_set.add(q_num)

            for q_num in range(1, num_q + 1):
                if q_num in inc_set:
                    incorrect_qs.append(q_num)
                else:
                    correct_qs.append(q_num)

            flash(f"Team scores set manually. correct={len(correct_qs)}, incorrect={len(incorrect_qs)}", "success")

        else:  # GPT approach, single image
            uploaded_file = request.files.get("scoreFile")
            if not uploaded_file or uploaded_file.filename == "":
                flash("No file selected for GPT-based team parse.", "error")
                return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

            scores_folder = os.path.join(BASE_UPLOAD_FOLDER, "scores", meet_id, event_id)
            os.makedirs(scores_folder, exist_ok=True)

            original_filename = secure_filename(uploaded_file.filename)
            unique_name = f"{uuid.uuid4()}_{original_filename}"
            full_path = os.path.join(scores_folder, unique_name)
            uploaded_file.save(full_path)

            relative_path = os.path.relpath(full_path, BASE_UPLOAD_FOLDER)
            add_score_files(meet_id, event_id, [relative_path])

            known_exam_data = event_data.get("examTopics", [])
            try:
                parse_result = parse_single_student_exam_image(relative_path, known_exam_data)
                correct_qs = parse_result.get("correctQuestions", [])
                incorrect_qs = parse_result.get("incorrectQuestions", [])
                flash(f"Team GPT parse success. correct={len(correct_qs)}", "success")
            except Exception as e:
                flash(f"GPT parse error for team event: {str(e)}", "error")
                return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

        update_team_scores(meet_id, event_id, correct_qs, incorrect_qs)
        return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

    # ---------- SINGLE-STUDENT SCORES (INDIVIDUAL EVENTS) ----------
    @app.route("/meet/<meet_id>/event/<event_id>/upload_single_student_score", methods=["POST"])
    def upload_single_student_score(meet_id, event_id):
        from src.data_manager import get_event, add_participant_scores, add_score_files

        event_data = get_event(meet_id, event_id)
        if not event_data:
            flash("Event not found.", "error")
            return redirect(url_for("view_meet", meet_id=meet_id))

        event_name = event_data.get("eventName", "")
        is_team_event = event_name in TEAM_EVENTS

        student_name = request.form.get("studentName")
        grade_level = request.form.get("gradeLevel")

        if not (student_name and grade_level):
            flash("Missing form data (name or grade).", "error")
            return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

        # If it's a team event, adding a participant requires no question-level data
        if is_team_event:
            new_participant = {
                "studentName": student_name,
                "gradeLevel": grade_level,
                "correctQuestions": [],
                "incorrectQuestions": []
            }
            add_participant_scores(meet_id, event_id, [new_participant])
            flash(f"Added {student_name} to team event '{event_name}'.", "success")
            return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

        # Otherwise, it's an individual event => we handle image/manual
        score_mode = request.form.get("scoreMode", "manual")  # default is manual
        correct_qs = []
        incorrect_qs = []

        if score_mode == "manual":
            num_q = event_data.get("numQuestions", 0)
            if num_q < 1:
                flash("No total # of questions set for this event. Upload exam or set event['numQuestions'] first!", "error")
                return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

            inc_str = request.form.get("incorrectList")
            inc_set = set()
            if inc_str:
                for item in inc_str.split(","):
                    item = item.strip()
                    if item.isdigit():
                        qn = int(item)
                        if 1 <= qn <= num_q:
                            inc_set.add(qn)

            for i in range(1, num_q + 1):
                if i in inc_set:
                    incorrect_qs.append(i)
                else:
                    correct_qs.append(i)

            flash(f"Manually entered data for {student_name}. Correct={len(correct_qs)}, Incorrect={len(incorrect_qs)}", "success")

        else:
            # GPT approach
            uploaded_file = request.files.get("scoreFile")
            if not uploaded_file or uploaded_file.filename == "":
                flash("No file selected for image-based parsing.", "error")
                return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

            scores_folder = os.path.join(BASE_UPLOAD_FOLDER, "scores", meet_id, event_id)
            os.makedirs(scores_folder, exist_ok=True)

            original_filename = secure_filename(uploaded_file.filename)
            unique_name = f"{uuid.uuid4()}_{original_filename}"
            full_path = os.path.join(scores_folder, unique_name)
            uploaded_file.save(full_path)

            relative_path = os.path.relpath(full_path, BASE_UPLOAD_FOLDER)
            add_score_files(meet_id, event_id, [relative_path])

            known_exam_data = event_data.get("examTopics", [])
            try:
                parse_result = parse_single_student_exam_image(relative_path, known_exam_data)
                correct_qs = parse_result.get("correctQuestions", [])
                incorrect_qs = parse_result.get("incorrectQuestions", [])
                flash(f"Image-based parsing for {student_name} done! Correct={len(correct_qs)}", "success")
            except Exception as e:
                flash(f"GPT parse error: {str(e)}", "error")
                return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

        new_participant = {
            "studentName": student_name,
            "gradeLevel": grade_level,
            "correctQuestions": correct_qs,
            "incorrectQuestions": incorrect_qs
        }
        add_participant_scores(meet_id, event_id, [new_participant])
        return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

    # ---------- DASHBOARD ----------
    @app.route("/dashboard")
    def dashboard_view():
        # Now includes both team & individual events in the topic coverage
        topic_accuracy_dict = get_topic_accuracy_across_meets(skip_team_events=False)
        sorted_topic_accuracy = sorted(topic_accuracy_dict.items(), key=lambda i: i[1]["accuracy"])

        topic_labels = [t[0] for t in sorted_topic_accuracy]
        topic_values = [round(t[1]["accuracy"] * 100, 1) for t in sorted_topic_accuracy]

        event_summaries = get_event_scores_summary()  # includes both team & individual
        # sort if you like
        event_summaries.sort(key=lambda e: e["totalCorrect"], reverse=True)

        # participant breakdown might skip team events or not, up to you
        participant_breakdowns = get_individual_breakdowns(skip_team_events=True)
        participant_breakdowns.sort(key=lambda p: p["totalCorrect"], reverse=True)

        return render_template(
            "dashboard.html",
            sorted_topic_accuracy=sorted_topic_accuracy,
            topic_accuracy=topic_accuracy_dict,
            event_summaries=event_summaries,
            participant_breakdowns=participant_breakdowns,
            topic_labels=topic_labels,
            topic_values=topic_values
        )

    # ---------- Delete Routes ----------
    @app.route("/meet/<meet_id>/delete_event/<event_id>", methods=["POST"])
    def remove_event(meet_id, event_id):
        ok = delete_event(meet_id, event_id)
        if ok:
            flash("Event deleted successfully!", "success")
        else:
            flash("Unable to delete event.", "error")
        return redirect(url_for("view_meet", meet_id=meet_id))

    @app.route("/meet/<meet_id>/event/<event_id>/delete_participant", methods=["POST"])
    def remove_participant(meet_id, event_id):
        student_name = request.form.get("studentName")
        grade_level = request.form.get("gradeLevel")
        if not (student_name and grade_level):
            flash("Missing participant info.", "error")
            return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

        ok = delete_participant(meet_id, event_id, student_name, grade_level)
        if ok:
            flash("Participant removed successfully!", "success")
        else:
            flash("Could not remove participant.", "error")
        return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

    return app


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(debug=True)
