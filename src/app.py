import os
import uuid
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

from src.data_manager import (
    load_data,
    create_meet,
    get_meet,
    create_event,
    get_event,
    add_topic_list_files,
    add_exam_files,
    add_score_files
)

# Fixed event choices for the dropdown
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

    # Ensure there's a folder to store uploads
    BASE_UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
    os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)

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
                return redirect(url_for("view_meet", meet_id=new_meet_id))
        return render_template("add_meet.html")

    @app.route("/meet/<meet_id>")
    def view_meet(meet_id):
        meet = get_meet(meet_id)
        if not meet:
            return "Meet not found", 404
        return render_template("meet.html", meet=meet)

    @app.route("/meet/<meet_id>/create_event", methods=["GET", "POST"])
    def create_event_route(meet_id):
        meet = get_meet(meet_id)
        if not meet:
            return "Meet not found", 404

        if request.method == "POST":
            event_name = request.form.get("event_name")
            if event_name in FIXED_EVENTS:
                event_id = create_event(meet_id, event_name)
                if event_id:
                    return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))
            return redirect(url_for("create_event_route", meet_id=meet_id))

        return render_template("create_event.html", 
                               meet_id=meet_id,
                               possible_events=FIXED_EVENTS)

    @app.route("/meet/<meet_id>/event/<event_id>")
    def view_event(meet_id, event_id):
        event = get_event(meet_id, event_id)
        if not event:
            return "Event not found", 404
        return render_template("event.html", meet_id=meet_id, event=event)

    # ----------- FILE UPLOAD ROUTES ------------

    @app.route("/meet/<meet_id>/upload_topic_list", methods=["POST"])
    def upload_topic_list(meet_id):
        """
        Handle uploading topic-list images for a meet, store them on disk,
        and record file paths in store.json
        """
        meet = get_meet(meet_id)
        if not meet:
            return "Meet not found", 404

        uploaded_files = request.files.getlist("files")
        saved_file_paths = []

        # Create a folder specifically for this meet's topic list
        topic_list_folder = os.path.join(BASE_UPLOAD_FOLDER, "topic_list", meet_id)
        os.makedirs(topic_list_folder, exist_ok=True)

        for file in uploaded_files:
            if file and file.filename:
                # Use a safe filename
                original_filename = secure_filename(file.filename)
                # Generate a unique name to avoid collisions
                unique_name = f"{uuid.uuid4()}_{original_filename}"
                # Build the full path
                full_path = os.path.join(topic_list_folder, unique_name)
                file.save(full_path)
                # We'll store a relative path or absolute—your choice
                # For clarity, let's store the relative path from "uploads/"
                relative_path = os.path.relpath(full_path, BASE_UPLOAD_FOLDER)
                saved_file_paths.append(relative_path)

        # Save these file paths to the meet data
        if saved_file_paths:
            add_topic_list_files(meet_id, saved_file_paths)

        return redirect(url_for("view_meet", meet_id=meet_id))

    @app.route("/meet/<meet_id>/event/<event_id>/upload_exam", methods=["POST"])
    def upload_exam_images(meet_id, event_id):
        """
        Handle uploading exam images for an event, storing them on disk,
        and record file paths in store.json
        """
        event = get_event(meet_id, event_id)
        if not event:
            return "Event not found", 404

        uploaded_files = request.files.getlist("files")
        saved_file_paths = []

        # Create a folder for this event's exam images
        exam_folder = os.path.join(BASE_UPLOAD_FOLDER, "exams", meet_id, event_id)
        os.makedirs(exam_folder, exist_ok=True)

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

        return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

    @app.route("/meet/<meet_id>/event/<event_id>/upload_scores", methods=["POST"])
    def upload_student_scores(meet_id, event_id):
        """
        Handle uploading score sheets for an event, storing them on disk,
        and record file paths in store.json
        """
        event = get_event(meet_id, event_id)
        if not event:
            return "Event not found", 404

        uploaded_files = request.files.getlist("files")
        saved_file_paths = []

        # Create a folder for this event's score sheets
        scores_folder = os.path.join(BASE_UPLOAD_FOLDER, "scores", meet_id, event_id)
        os.makedirs(scores_folder, exist_ok=True)

        for file in uploaded_files:
            if file and file.filename:
                original_filename = secure_filename(file.filename)
                unique_name = f"{uuid.uuid4()}_{original_filename}"
                full_path = os.path.join(scores_folder, unique_name)
                file.save(full_path)
                relative_path = os.path.relpath(full_path, BASE_UPLOAD_FOLDER)
                saved_file_paths.append(relative_path)

        if saved_file_paths:
            add_score_files(meet_id, event_id, saved_file_paths)

        return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

    return app


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(debug=True)
