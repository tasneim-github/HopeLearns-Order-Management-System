import re
import os
from flask import redirect, render_template, session, request
from functools import wraps
from werkzeug.utils import secure_filename
from cs50 import SQL
from datetime import datetime

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///orders.db")

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def apology(message, is_admin=False, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", is_admin=is_admin, top=escape(message), bottom=code), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def is_valid_email(email):
    # Basic regex for email validation
    email_regex = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_files(file_key, upload_folder):
    file_paths = []
    # If a reference was submitted
    if file_key in request.files:
        # Retrieve all files in a list
        files = request.files.getlist(file_key)

        for file in files:
            if file and allowed_file(file.filename):
                # Secure filename
                filename = secure_filename(file.filename)
                # Make sure filename is unique
                unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                # Save the file in the file path
                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)
                # Store the file path
                file_paths.append(file_path)
    return file_paths


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"


def is_valid_order_id(is_admin, order_id):
    """ Takes the order_id from the hidden input and determines whether it is valid"""
    user_id = session["user_id"]
    # Get the submitted order_id
    try:
        # Ensure order_id is provided and can be converted to an integer
        if not order_id:
            return False

        order_id = int(order_id)

        if not is_admin:
            # Verify the order exists and is owned by the user
            true_order_id = db.execute(
                "SELECT order_id FROM orders WHERE order_id = ? AND user_id = ?",
                order_id,
                user_id,
            )

            # If no matching order is found, unauthorized action
            if len(true_order_id) == 0:
                return False

        else:
            order = db.execute("SELECT * FROM orders WHERE order_id = ?", order_id)
            if len(order) == 0:
                return False

    # If order id was not an integer
    except ValueError:
        return False
    return True


def get_form_data():
    """ Get and validate data from an order form """

    # Extract data from the form
    order_name = request.form.get("order_name")
    character_part = request.form.get("character_part")
    character_part_options = ["Head", "Half Body", "Full Body"]
    preferred_style = request.form.get("preferred_style")
    preferred_style_options = ["Chibi", "Normal"]
    pose_view = request.form.get("pose_view")
    pose_view_options = ["Front View", "3/4 View", "Side View"]
    pose_description = request.form.get("pose_description")
    character_features_description = request.form.get("character_features_description")
    outfit_description = request.form.get("outfit_description")
    background_preference = request.form.get("background")
    background_options = ["with-background", "without-background"]
    background_description = request.form.get("background_description")
    due_date = request.form.get("due_date")
    colors = request.form.getlist("colors[]")

    # Check for errors
    # Error 1: leaving any field blank
    if not order_name:
        return apology("must provide order name")
    if not character_part:
        return apology("must provide character part")
    if not preferred_style:
        return apology("must provide preferred style")
    if not pose_view:
        return apology("must provide pose view")
    if not pose_description:
        return apology("must provide pose description")
    if not character_features_description:
        return apology("must provide character features description")
    if not outfit_description:
        return apology("must provide outfit description")

     # If user inserted invalid colors
    for color in colors:
        if not is_valid_color(color):
            return apology("invalid color(s)")

    # If user did not choose a color pallet
    if len(set(colors)) < 2:
        return apology("must provide at least two different colors")

    if not background_preference:
        return apology("must select background preference")
    if background_preference == "with-background" and not background_description:
        return apology("must provide background description")
    if not due_date:
        return apology("must provide due date")

    # Error 2: drop down menues and radio buttons were submitted incorrectly
    if character_part not in character_part_options:
        return apology("invalid character part")
    if preferred_style not in preferred_style_options:
        return apology("invalid preferred style")
    if pose_view not in pose_view_options:
        return apology("invalid pose view")
    if background_preference not in background_options:
        return apology("invalid background preference")

    # Error 3: Date is in the past
    # Parse the provided date and get the current date
    try:
        due_date_obj = datetime.strptime(due_date, "%Y-%m-%d")
        today = datetime.now()
    except ValueError:
        return apology("invalid due date")

    # Check if the due date is in the past
    if due_date_obj < today:
        return apology("due date is in the past")

    if background_preference == "with-background":
        has_background = 'TRUE'
    else:
        has_background = 'FALSE'
        background_description = None

    return {
        "order_name": order_name,
        "character_part": character_part,
        "preferred_style": preferred_style,
        "pose_view": pose_view,
        "pose_description": pose_description,
        "character_features_description": character_features_description,
        "outfit_description": outfit_description,
        "has_background": has_background,
        "background_description": background_description,
        "due_date": due_date,
        "colors": colors,
    }


def user_or_admin(user_id):
    """ Returns True if user is an admin, False otherwise """

    is_admin = db.execute("SELECT is_admin FROM users WHERE id = ?", user_id)
    is_admin = is_admin[0]["is_admin"]
    return is_admin


def is_valid_color(color):
    """ Validate if the input is a valid hex color code. """
    color_regex = r'^#[0-9A-Fa-f]{6}$'
    return bool(re.match(color_regex, color))
