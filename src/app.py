import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()  # Load .env
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
    # Extra for deleting events/participants
    delete_event,
    delete_participant
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

FIXED_EVENTS = [
    "Individual Algebra",
    "Individual Geometry",
    "Individual Algebra II",
    "Individual Precalculus",
    "Frosh-Soph 2-Person",
    "Jr-Sr 2-Person",
    "Frosh-Soph 8-person",
    "Jr-Sr 8-person",
    "Calculator Team"
]

def create_app():
    app = Flask(__name__,
                template_folder="../templates",
                static_folder="../static")

    # For flash messages
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
        return render_template("event.html", meet_id=meet_id, event=event)

    # ---------- FILE UPLOAD + GPT INTEGRATION ----------

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
            # GPT parse
            try:
                parsed_topics = parse_topic_list_images(saved_file_paths)
                update_meet_topic_list(meet_id, parsed_topics)
                flash("Topic list uploaded and parsed successfully!", "success")
            except Exception as e:
                flash(f"GPT parse error: {str(e)}", "error")

        return redirect(url_for("view_meet", meet_id=meet_id))

    @app.route("/meet/<meet_id>/event/<event_id>/upload_exam", methods=["POST"])
    def upload_exam_images(meet_id, event_id):
        event = get_event(meet_id, event_id)
        if not event:
            flash("Event not found.", "error")
            return redirect(url_for("view_meet", meet_id=meet_id))

        uploaded_files = request.files.getlist("files")
        if not uploaded_files or all(f.filename == "" for f in uploaded_files):
            flash("No files selected.", "error")
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
            # GPT parse
            from src.data_manager import get_meet
            meet = get_meet(meet_id)
            known_list = meet.get("topicList", {}) if meet else {}
            try:
                exam_data = parse_exam_images(saved_file_paths, known_list)
                update_event_exam_topics(meet_id, event_id, exam_data)
                flash("Exam images uploaded and parsed successfully!", "success")
            except Exception as e:
                flash(f"GPT parse error: {str(e)}", "error")

        return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

    # ---------- SINGLE-STUDENT SCORE UPLOAD ----------

    @app.route("/meet/<meet_id>/event/<event_id>/upload_single_student_score", methods=["POST"])
    def upload_single_student_score(meet_id, event_id):
        """
        If the user chooses 'manual' in the form, we handle the manual question entry.
        Otherwise, we assume they uploaded an image for GPT parsing.
        """
        from src.data_manager import get_event, add_score_files, add_participant_scores

        event_data = get_event(meet_id, event_id)
        if not event_data:
            flash("Event not found.", "error")
            return redirect(url_for("home_page"))

        student_name = request.form.get("studentName")
        grade_level = request.form.get("gradeLevel")
        score_mode = request.form.get("scoreMode")  # "manual" or "image"

        if not (student_name and grade_level and score_mode):
            flash("Missing form data.", "error")
            return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

        # We'll build these:
        correct_qs = []
        incorrect_qs = []

        if score_mode == "manual":
            # 1. Gather "totalQuestions" and "incorrectList" from the form
            total_questions_str = request.form.get("totalQuestions")
            incorrect_list_str = request.form.get("incorrectList")  # e.g. "3,7" meaning Q3 and Q7 are incorrect

            try:
                total_q = int(total_questions_str)
            except (TypeError, ValueError):
                flash("Invalid total questions number.", "error")
                return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

            if total_q < 1:
                flash("Total questions must be at least 1.", "error")
                return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

            # Convert the user input to a set of question numbers
            incorrect_set = set()
            if incorrect_list_str:
                for item in incorrect_list_str.split(","):
                    item = item.strip()
                    if item.isdigit():
                        q_num = int(item)
                        if q_num >= 1 and q_num <= total_q:
                            incorrect_set.add(q_num)

            # Everything else is correct
            for q_num in range(1, total_q + 1):
                if q_num in incorrect_set:
                    incorrect_qs.append(q_num)
                else:
                    correct_qs.append(q_num)

            flash(f"Manually entered data for {student_name}. Correct={len(correct_qs)}, Incorrect={len(incorrect_qs)}", "success")
            
        else:
            # 2. GPT-based approach: the user uploaded an image
            uploaded_file = request.files.get("scoreFile")
            if not uploaded_file or uploaded_file.filename == "":
                flash("No file selected for image-based parsing.", "error")
                return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

            # Save the file
            scores_folder = os.path.join(BASE_UPLOAD_FOLDER, "scores", meet_id, event_id)
            os.makedirs(scores_folder, exist_ok=True)

            original_filename = secure_filename(uploaded_file.filename)
            unique_name = f"{uuid.uuid4()}_{original_filename}"
            full_path = os.path.join(scores_folder, unique_name)
            uploaded_file.save(full_path)

            relative_path = os.path.relpath(full_path, BASE_UPLOAD_FOLDER)
            add_score_files(meet_id, event_id, [relative_path])

            # GPT parse
            from src.gpt_services import parse_single_student_exam_image
            known_exam_data = event_data.get("examTopics", [])
            try:
                parse_result = parse_single_student_exam_image(relative_path, known_exam_data)
                correct_qs = parse_result.get("correctQuestions", [])
                incorrect_qs = parse_result.get("incorrectQuestions", [])
                flash(f"Image-based parsing for {student_name} completed!", "success")
            except Exception as e:
                flash(f"GPT parse error: {str(e)}", "error")
                return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

        # 3. Now store them the same way as always
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
        topic_accuracy_dict = get_topic_accuracy_across_meets()
        # 1. Sort topics by descending accuracy
        sorted_topic_accuracy = sorted(
            topic_accuracy_dict.items(),
            key=lambda item: item[1]["accuracy"],
            reverse=True
        )
        # Now sorted_topic_accuracy is like:
        # [("Geometry - Circles", {"correct":..., "attempted":..., "accuracy":...}), ...]

        # 2. Build arrays for Chart.js
        topic_labels = [t[0] for t in sorted_topic_accuracy]  # e.g. ["Geometry - Circles", "Algebra - Factoring", ...]
        topic_values = [round(t[1]["accuracy"] * 100, 1) for t in sorted_topic_accuracy]  # e.g. [85.0, 72.3, ...]

        # We also sort event summaries and participant breakdowns.
        event_summaries = get_event_scores_summary()
        # For example, sort them by totalCorrect descending:
        event_summaries.sort(key=lambda e: e["totalCorrect"], reverse=True)

        participant_breakdowns = get_individual_breakdowns()
        # Sort them by totalCorrect descending:
        participant_breakdowns.sort(key=lambda p: p["totalCorrect"], reverse=True)

        return render_template(
            "dashboard.html",
            # The standard data for your tables:
            topic_accuracy=topic_accuracy_dict,  # Might or might not use sorted
            event_summaries=event_summaries,
            participant_breakdowns=participant_breakdowns,
            # The arrays for the chart:
            topic_labels=topic_labels,
            topic_values=topic_values
        )

    # ---------- OPTIONAL: DELETION ROUTES ----------

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