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
        from src.data_manager import (
            get_event, add_score_files, add_participant_scores
        )

        event_data = get_event(meet_id, event_id)
        if not event_data:
            flash("Event not found.", "error")
            return redirect(url_for("view_meet", meet_id=meet_id))

        student_name = request.form.get("studentName")
        grade_level = request.form.get("gradeLevel")
        uploaded_file = request.files.get("scoreFile")

        if not (student_name and grade_level and uploaded_file):
            flash("Missing form data or file.", "error")
            return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

        scores_folder = os.path.join(BASE_UPLOAD_FOLDER, "scores", meet_id, event_id)
        os.makedirs(scores_folder, exist_ok=True)

        original_filename = secure_filename(uploaded_file.filename)
        unique_name = f"{uuid.uuid4()}_{original_filename}"
        full_path = os.path.join(scores_folder, unique_name)
        uploaded_file.save(full_path)

        relative_path = os.path.relpath(full_path, BASE_UPLOAD_FOLDER)
        add_score_files(meet_id, event_id, [relative_path])

        # GPT parse
        known_exam_data = event_data.get("examTopics", [])
        try:
            parse_result = parse_single_student_exam_image(relative_path, known_exam_data)
            correct_qs = parse_result.get("correctQuestions", [])
            incorrect_qs = parse_result.get("incorrectQuestions", [])

            new_participant = {
                "studentName": student_name,
                "gradeLevel": grade_level,
                "correctQuestions": correct_qs,
                "incorrectQuestions": incorrect_qs
            }
            add_participant_scores(meet_id, event_id, [new_participant])
            flash(f"Score sheet parsed for {student_name}!", "success")
        except Exception as e:
            flash(f"GPT parse error: {str(e)}", "error")

        return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

    # ---------- DASHBOARD ----------

    @app.route("/dashboard")
    def dashboard_view():
        topic_accuracy = get_topic_accuracy_across_meets()
        event_summaries = get_event_scores_summary()
        participant_breakdowns = get_individual_breakdowns()

        return render_template(
            "dashboard.html",
            topic_accuracy=topic_accuracy,
            event_summaries=event_summaries,
            participant_breakdowns=participant_breakdowns
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