import os
from flask import Flask, render_template, request, redirect, url_for
from src.data_manager import (
    load_data,
    create_meet,
    get_meet,
    create_event,
    get_event
)

# Fixed event choices
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
        """
        Shows basic details of a specific meet, and list of events.
        Also provides a link to create a new event.
        """
        meet = get_meet(meet_id)
        if not meet:
            return "Meet not found", 404
        return render_template("meet.html", meet=meet)

    @app.route("/meet/<meet_id>/create_event", methods=["GET", "POST"])
    def create_event_route(meet_id):
        """
        GET: Show a form with a dropdown of fixed events.
        POST: Create the event, redirect to the event detail page.
        """
        meet = get_meet(meet_id)
        if not meet:
            return "Meet not found", 404

        if request.method == "POST":
            event_name = request.form.get("event_name")
            if event_name in FIXED_EVENTS:
                event_id = create_event(meet_id, event_name)
                if event_id:
                    return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))
            # If event_name isn't in the fixed list or creation failed, just reload
            return redirect(url_for("create_event_route", meet_id=meet_id))

        # GET request: show the dropdown
        return render_template("create_event.html", 
                               meet_id=meet_id, 
                               possible_events=FIXED_EVENTS)

    @app.route("/meet/<meet_id>/event/<event_id>")
    def view_event(meet_id, event_id):
        """
        Show basic info about this event, plus placeholders for file uploads.
        """
        event = get_event(meet_id, event_id)
        if not event:
            return "Event not found", 404
        return render_template("event.html", meet_id=meet_id, event=event)

    # Below are stubs for file uploads. They won't do any GPT parsing yet.

    @app.route("/meet/<meet_id>/upload_topic_list", methods=["POST"])
    def upload_topic_list(meet_id):
        """
        Stub for uploading topic-list images for a meet (NOT for a single event).
        For now, it does nothing except confirm receipt.
        """
        if "files" in request.files:
            uploaded_files = request.files.getlist("files")
            print(f"Received {len(uploaded_files)} file(s) for topic list (meet ID = {meet_id})")
        return redirect(url_for("view_meet", meet_id=meet_id))

    @app.route("/meet/<meet_id>/event/<event_id>/upload_exam", methods=["POST"])
    def upload_exam_images(meet_id, event_id):
        """
        Stub for uploading exam images for an event.
        Currently just logs the files.
        """
        if "files" in request.files:
            uploaded_files = request.files.getlist("files")
            print(f"Received {len(uploaded_files)} exam file(s) for event {event_id}")
        return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

    @app.route("/meet/<meet_id>/event/<event_id>/upload_scores", methods=["POST"])
    def upload_student_scores(meet_id, event_id):
        """
        Stub for uploading graded student score sheets for an event.
        Currently just logs the files.
        """
        if "files" in request.files:
            uploaded_files = request.files.getlist("files")
            print(f"Received {len(uploaded_files)} score file(s) for event {event_id}")
        return redirect(url_for("view_event", meet_id=meet_id, event_id=event_id))

    return app


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(debug=True)
