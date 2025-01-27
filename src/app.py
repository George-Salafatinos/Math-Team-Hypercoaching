import os
from flask import Flask, render_template, request, redirect, url_for
from src.data_manager import load_data, create_meet, get_meet

def create_app():
    # Point Flask to the correct template & static folders
    app = Flask(__name__, 
                template_folder="../templates",
                static_folder="../static")

    @app.route("/")
    def home_page():
        """Show the list of meets on the home page."""
        data = load_data()
        meets = data["meets"]
        return render_template("home.html", meets=meets)

    @app.route("/add_meet", methods=["GET", "POST"])
    def add_meet_route():
        """
        GET: Show a form to enter the meet title.
        POST: Create the new meet in the data store, then redirect.
        """
        if request.method == "POST":
            title = request.form.get("title")
            if title:
                # Create the meet in our JSON store
                new_meet_id = create_meet(title)
                # Redirect to the newly created meet detail page
                return redirect(url_for("view_meet", meet_id=new_meet_id))
        return render_template("add_meet.html")

    @app.route("/meet/<meet_id>")
    def view_meet(meet_id):
        """
        Show basic details of a specific meet.
        For now, just display its title and ID.
        """
        meet = get_meet(meet_id)
        if not meet:
            return "Meet not found", 404
        return render_template("meet.html", meet=meet)

    return app


# Optional: If you prefer to run directly with "python app.py"
# you can do so, otherwise you might use 'flask run' after setting FLASK_APP=src/app.py
if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(debug=True)
