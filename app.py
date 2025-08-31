import os
from cs50 import SQL
from flask import flash, Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, is_valid_email, process_files, usd, is_valid_order_id, get_form_data, user_or_admin

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Folder to store uploaded files
UPLOAD_FOLDER = 'static/uploads'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///orders.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """View past orders for admins and users"""

    user_id = session["user_id"]
    is_admin = user_or_admin(user_id)

    if is_admin:
        past_orders = db.execute("""
                                SELECT order_id,
                                order_name,
                                price,
                                status,
                                order_due_date,
                                created_at
                                FROM orders
                                ORDER BY order_due_date ASC
                                """)

    else:
        past_orders = db.execute("""
                                SELECT order_id,
                                order_name,
                                price,
                                status,
                                order_due_date,
                                created_at
                                FROM orders
                                WHERE user_id = ?
                                ORDER BY order_due_date ASC
                                """, user_id)

    for order in past_orders:
        if not order["price"]:
            order["price"] = '-'

    return render_template("index.html", action_required=True, is_admin=is_admin,
                           past_orders=past_orders, page_title="Orders!" if is_admin else "Your Orders!")


@app.route("/handle-action", methods=["POST"])
def handle_action():
    user_id = session["user_id"]
    is_admin = user_or_admin(user_id)

    order_id = request.form.get("order_id")
    if not is_valid_order_id(is_admin, order_id):
        if is_admin:
            return apology("unauthorized action", True)
        else:
            return apology("unauthorized action")
    else:
        # Get the action (accept, reject, or remove)
        action = request.form.get("action")

        if action == "accept":
            # Handle the accept action
            db.execute("UPDATE orders SET status = 'accepted' WHERE order_id = ?", order_id)
            flash("Order accepted!")
        elif action == "remove" or action == "reject":
            # Handle the remove action
            # Retrieve the file paths for the order
            character_files = db.execute(
                "SELECT file_path FROM character_references WHERE order_id = ?", order_id
            )
            background_files = db.execute(
                "SELECT file_path FROM background_references WHERE order_id = ?", order_id
            )

            # Delete the files from the filesystem
            for file in character_files:
                try:
                    os.remove(file["file_path"])  # Delete the character reference files
                except FileNotFoundError:
                    pass  # Ignore if file doesn't exist

            for file in background_files:
                try:
                    os.remove(file["file_path"])  # Delete the background reference files
                except FileNotFoundError:
                    pass  # Ignore if file doesn't exist

            # Remove the order from the database
            db.execute("DELETE FROM orders WHERE order_id = ?", order_id)
            flash("Order deleted!")

        elif action == "complete":
            db.execute("UPDATE orders SET status = 'completed' WHERE order_id = ?", order_id)
            flash("Order completed!")
        else:
            # Handle unexpected cases
            if is_admin:
                return apology("unauthorized action", True)
            else:
                return apology("unauthorized action")

        return redirect("/")


@app.route("/view-details")
def view_details():
    order_id = request.args.get("order_id")

    user_id = session["user_id"]
    is_admin = user_or_admin(user_id)

    if not is_valid_order_id(is_admin, order_id):
        if is_admin:
            return apology("unauthorized action", True)
        else:
            return apology("unauthorized action")

    else:
        order = db.execute("SELECT * FROM orders WHERE order_id = ?", order_id)

        order = order[0]
        order["has_background"] = order["has_background"] == 'TRUE'

        colors = db.execute("SELECT DISTINCT color_hex FROM color_palette WHERE order_id = ?", order_id)

        character_references = db.execute(
            "SELECT file_path FROM character_references WHERE order_id = ?", order_id)
        background_references = db.execute(
            "SELECT file_path FROM background_references WHERE order_id = ?", order_id)

        user_id = db.execute("""
                                SELECT user_id
                                FROM orders
                                WHERE order_id = ?
                                """, order_id)
        user_id = user_id[0]["user_id"]

        user_info = db.execute("""
                                SELECT username, email
                                FROM users
                                WHERE id = ?
                                """, user_id)
        user_info = user_info[0]

        return render_template("edit-order-price.html", view_only=True, user_info=user_info, order=order, colors=colors, character_references=character_references,
                               background_references=background_references, page_title="View Order!", is_admin=is_admin)


@app.route("/accepted-orders")
@login_required
def view_accepted_orders():
    user_id = session["user_id"]
    is_admin = user_or_admin(user_id)

    if not is_admin:
        return apology("unauthorized action")

    past_orders = db.execute("""
                                SELECT
                                order_id,
                                order_name,
                                price,
                                status,
                                order_due_date,
                                created_at
                                FROM orders
                                WHERE status = 'accepted'
                                ORDER BY order_due_date ASC
                                """)

    for order in past_orders:
        if not order["price"]:
            order["price"] = '-'

    return render_template("index.html", action_required=False, is_admin=True, past_orders=past_orders, page_title="Accepted Orders!")


@app.route("/place-order", methods=["GET", "POST"])
def place_order():
    """ Place order """

    user_id = session["user_id"]
    is_admin = user_or_admin(user_id)

    if is_admin:
        return apology("unauthorized action", True)

    if request.method == "POST":
        form_data = get_form_data()

        if not isinstance(form_data, dict):
            return form_data  # Return the apology response directly

        # Assign individual values to variables
        order_name = form_data["order_name"]
        character_part = form_data["character_part"]
        preferred_style = form_data["preferred_style"]
        pose_view = form_data["pose_view"]
        pose_description = form_data["pose_description"]
        character_features_description = form_data["character_features_description"]
        outfit_description = form_data["outfit_description"]
        has_background = form_data["has_background"]
        background_description = form_data["background_description"]
        due_date = form_data["due_date"]
        colors = form_data["colors"]
        # Handle the submitted images
        character_references = process_files('character_references[]', os.path.join(
            app.config['UPLOAD_FOLDER'], 'character_references'))
        if has_background:
            background_references = process_files('background_references[]', os.path.join(
                app.config['UPLOAD_FOLDER'], 'background_references'))
        else:
            background_references = []

        # Insert data to the database
        db.execute("""
                    INSERT INTO orders (
                    user_id,
                    order_name,
                    character_part,
                    preferred_style,
                    pose_view,
                    pose_description,
                    character_features_description,
                    outfit_description,
                    has_background,
                    background_description,
                    order_due_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, user_id,
                   order_name,
                   character_part,
                   preferred_style,
                   pose_view,
                   pose_description,
                   character_features_description,
                   outfit_description,
                   has_background,
                   background_description,
                   due_date)

        # Get the last order
        order_id = db.execute("SELECT MAX(order_id) AS order_id FROM orders")
        order_id = order_id[0]["order_id"]

        # Add the color pallet of the order
        for color in colors:
            db.execute("""
                    INSERT INTO color_palette (order_id, color_hex)
                    VALUES (?, ?)
                    """, order_id, color)

        # Save file paths to the character references table
        for path in character_references:
            db.execute("""
                    INSERT INTO character_references (order_id, file_path)
                    VALUES (?, ?)
                    """, order_id, path)

        # Save file paths to the background references table
        for path in background_references:
            db.execute("""
                    INSERT INTO background_references (order_id, file_path)
                    VALUES (?, ?)
                    """, order_id, path)

        # Handle valid form submission
        flash("Order submitted successfully!")

        return redirect("/")

    else:
        return render_template("place-order.html", page_title="Place Your Order!")


@app.route("/edit-order", methods=["GET", "POST"])
def edit_order():
    """ Edit order """
    user_id = session["user_id"]
    is_admin = user_or_admin(user_id)

    if is_admin:
        return apology("unauthorized action", True)

    if request.method == "POST":
        form_data = get_form_data()

        if not isinstance(form_data, dict):
            return form_data  # Return the apology response directly

        # Assign individual values to variables
        order_name = form_data["order_name"]
        character_part = form_data["character_part"]
        preferred_style = form_data["preferred_style"]
        pose_view = form_data["pose_view"]
        pose_description = form_data["pose_description"]
        character_features_description = form_data["character_features_description"]
        outfit_description = form_data["outfit_description"]
        has_background = form_data["has_background"]
        background_description = form_data["background_description"]
        due_date = form_data["due_date"]
        colors = form_data["colors"]
        # Handle the submitted images
        character_references = process_files('character_references[]', os.path.join(
            app.config['UPLOAD_FOLDER'], 'character_references'))
        if has_background:
            background_references = process_files('background_references[]', os.path.join(
                app.config['UPLOAD_FOLDER'], 'background_references'))
        else:
            background_references = []

        order_id = request.form.get("order_id")
        if not is_valid_order_id(False, order_id):
            return apology("unauthorized action")

        # Update the order
        db.execute("""
                    UPDATE orders
                    SET
                    order_name = ?,
                    character_part = ?,
                    preferred_style = ?,
                    pose_view = ?,
                    pose_description = ?,
                    character_features_description = ?,
                    outfit_description = ?,
                    has_background = ?,
                    background_description = ?,
                    order_due_date = ?
                    WHERE order_id = ?;
                    """, order_name, character_part, preferred_style,
                   pose_view, pose_description, character_features_description,
                   outfit_description, has_background, background_description,
                   due_date, order_id)

        # Add the color pallet of the order
        for color in colors:
            db.execute("""
                        INSERT INTO color_palette (order_id, color_hex)
                        VALUES (?, ?)
                        """, order_id, color)

        # Save file paths to the character references table
        for path in character_references:
            db.execute("""
                    INSERT INTO character_references (order_id, file_path)
                    VALUES (?, ?)
                    """, order_id, path)

        # Save file paths to the background references table
        for path in background_references:
            db.execute("""
                    INSERT INTO background_references (order_id, file_path)
                    VALUES (?, ?)
                    """, order_id, path)

        # Handle valid form submission
        flash("Order edited successfully!")

        return redirect("/")

    else:
        order_id = request.args.get("order_id")
        if not is_valid_order_id(False, order_id):
            return apology("unauthorized action")
        else:
            order = db.execute("SELECT * FROM orders WHERE order_id = ?", order_id)
            order = order[0]
            order["has_background"] = order["has_background"] == 'TRUE'

            colors = db.execute("SELECT DISTINCT color_hex FROM color_palette WHERE order_id = ?", order_id)

            character_references = db.execute(
                "SELECT file_path FROM character_references WHERE order_id = ?", order_id)
            background_references = db.execute(
                "SELECT file_path FROM background_references WHERE order_id = ?", order_id)

            return render_template("edit-order.html", order=order, colors=colors, character_references=character_references,
                                   background_references=background_references, page_title="Edit Your Order!")


@app.route("/edit-order-price", methods=["GET", "POST"])
@login_required
def edit_order_price():
    user_id = session["user_id"]
    is_admin = user_or_admin(user_id)

    if not is_admin:
        return apology("unauthorized action")

    # The admin edited the price
    if request.method == 'POST':
        new_price = request.form.get("order_price")

        # If empty, no action
        if not new_price:
            return redirect("/")

        # Check for errors
        # Negative price
        try:
            if float(new_price) < 0:
                return apology("price must be positive", True)
        except ValueError:
            return apology("invalid price", True)

        order_id = request.form.get("order_id")
        if not is_valid_order_id(True, order_id):
            return apology("unauthorized action", True)

        else:
            # Update price and status
            db.execute("UPDATE orders SET price = ?, status = ? WHERE order_id = ?",
                       new_price, 'reviewed', order_id)
            flash("Price edited!")
            return redirect("/")

    else:
        order_id = request.args.get("order_id")
        if not is_valid_order_id(True, order_id):
            return apology("unauthorized action", True)

        else:
            order = db.execute("SELECT * FROM orders WHERE order_id = ?", order_id)
            order = order[0]
            order["has_background"] = order["has_background"] == 'TRUE'

            colors = db.execute("SELECT DISTINCT color_hex FROM color_palette WHERE order_id = ?", order_id)

            character_references = db.execute(
                "SELECT file_path FROM character_references WHERE order_id = ?", order_id)
            background_references = db.execute(
                "SELECT file_path FROM background_references WHERE order_id = ?", order_id)

            user_id = db.execute("""
                                 SELECT user_id
                                 FROM orders
                                 WHERE order_id = ?
                                 """, order_id)
            user_id = user_id[0]["user_id"]

            user_info = db.execute("""
                                    SELECT username, email
                                    FROM users
                                    WHERE id = ?
                                    """, user_id)
            user_info = user_info[0]

            return render_template("edit-order-price.html", view_only=False, user_info=user_info, order=order, colors=colors, character_references=character_references,
                                   background_references=background_references, page_title="Edit Order!", is_admin=True)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Check for errors
        # Error 1: leaving any field blank
        if not request.form.get("username"):
            return apology("must provide username")

        elif not request.form.get("password"):
            return apology("must provide password")

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html", page_title="Login!")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        # Check for errors
        # Error 1: leaving any field blank
        if not request.form.get("username"):
            return apology("must provide username")

        elif not request.form.get("password"):
            return apology("must provide password")

        elif not request.form.get("email"):
            return apology("must provide email")

        elif not request.form.get("confirmation"):
            return apology("must provide password confirmation")

        # Error 2: Two password do not match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("password and confirmation must match")

        # Error 3: Invalid email address
        if not is_valid_email(request.form.get("email")):
            return apology("invalid email")

        # Error 4: Email is already taken
        emails = db.execute("SELECT email FROM users")
        emails = [email["email"] for email in emails]
        if request.form.get("email") in emails:
            return apology("email already taken")

        # Error 5: If username is already taken, if not insert the user
        try:
            db.execute(
                "INSERT INTO users (username, hash, email) VALUES (?, ?, ?)",
                request.form.get("username"), generate_password_hash(
                    request.form.get("password")), request.form.get("email")
            )
        except ValueError:
            return apology("username already taken")

        # Log the user in
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        session["user_id"] = rows[0]["id"]

        flash("Registered!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # Change page to a form where users can register for a new account
        return render_template("register.html", page_title="Register!")


@app.route("/contact-me")
def contact_me():
    """Show the contact information"""

    return render_template("contact-me.html")
