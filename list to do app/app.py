import os
import random
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "dev-secret-change-this"
)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bloomtasks.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Mail configuration
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME", "")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD", "")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv(
    "MAIL_DEFAULT_SENDER",
    app.config["MAIL_USERNAME"]
)

db = SQLAlchemy(app)
mail = Mail(app)


# =========================================================
# MOTIVATIONAL QUOTES
# =========================================================

MOTIVATION_QUOTES = [
    "One task done. Nine more opportunities to make today amazing! 🌸",
    "Small progress is still progress. Keep going! 💗",
    "You finished one task — that's a win. Celebrate it and continue! 🎉",
    "Every completed task brings you closer to the life you want. ✨",
    "You don't have to finish everything at once. Just keep moving. 🌷",
    "One step completed. Your future self is already proud of you. 💕",
    "Done is better than perfect. Keep building your day! 🌸",
    "You started it, you finished it — now keep that momentum going! 🔥",
    "A peaceful life is built one completed task at a time. 🌿",
    "Your consistency today becomes your confidence tomorrow. 💖",
    "Progress looks beautiful on you. Keep going! 🌺",
    "One less task, one more reason to smile. 😊",
    "Focus on the next task, not the whole mountain. 🏔️",
    "You are doing better than you think. Keep moving forward! 🌷",
    "Your goals deserve your effort. You've got this! 💪"
]


# =========================================================
# DATABASE MODELS
# =========================================================

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    is_admin = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    tasks = db.relationship(
        "Task",
        backref="owner",
        lazy=True,
        cascade="all, delete-orphan"
    )


class Task(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    priority = db.Column(
        db.String(20),
        default="Medium"
    )

    due_date = db.Column(
        db.String(20),
        nullable=True
    )

    status = db.Column(
        db.String(20),
        default="pending"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    completed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def create_database():

    with app.app_context():

        db.create_all()

        admin_email = os.getenv("ADMIN_EMAIL")
        admin_password = os.getenv("ADMIN_PASSWORD")

        if admin_email and admin_password:

            existing_admin = User.query.filter_by(
                email=admin_email
            ).first()

            if not existing_admin:

                admin = User(
                    username="Administrator",
                    email=admin_email,
                    password_hash=generate_password_hash(
                        admin_password
                    ),
                    is_admin=True
                )

                db.session.add(admin)
                db.session.commit()

            elif not existing_admin.is_admin:

                existing_admin.is_admin = True
                db.session.commit()


# =========================================================
# LOGIN DECORATORS
# =========================================================

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:

            flash(
                "Please login to continue.",
                "warning"
            )

            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


def admin_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:

            return redirect(url_for("login"))

        user = db.session.get(
            User,
            session["user_id"]
        )

        if not user or not user.is_admin:

            flash(
                "Admin access required.",
                "danger"
            )

            return redirect(url_for("dashboard"))

        return function(*args, **kwargs)

    return wrapper


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    if "user_id" in session:

        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# =========================================================
# SIGNUP
# =========================================================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not username or not email or not password:

            flash(
                "Please fill in all fields.",
                "danger"
            )

            return redirect(url_for("signup"))

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(url_for("signup"))

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )

            return redirect(url_for("signup"))

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash(
                "An account with this email already exists.",
                "danger"
            )

            return redirect(url_for("login"))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )

        db.session.add(user)
        db.session.commit()

        flash(
            "Account created successfully! Please login.",
            "success"
        )

        return redirect(url_for("login"))

    return render_template("signup.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password_hash,
            password
        ):

            session.clear()

            session["user_id"] = user.id
            session["username"] = user.username
            session["is_admin"] = user.is_admin

            return redirect(url_for("dashboard"))

        flash(
            "Invalid email or password.",
            "danger"
        )

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(url_for("login"))


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    user_id = session["user_id"]

    tasks = Task.query.filter_by(
        user_id=user_id
    ).order_by(
        Task.created_at.desc()
    ).all()

    total_tasks = len(tasks)

    completed_tasks = sum(
        1 for task in tasks
        if task.status == "completed"
    )

    pending_tasks = total_tasks - completed_tasks

    if total_tasks > 0:

        progress = round(
            (completed_tasks / total_tasks) * 100
        )

    else:

        progress = 0

    completed_quote = session.pop(
        "completed_quote",
        None
    )

    daily_quote = random.choice(
        MOTIVATION_QUOTES
    )

    return render_template(
        "dashboard.html",
        username=session.get("username"),
        tasks=tasks,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        progress=progress,
        completed_quote=completed_quote,
        daily_quote=daily_quote,
        is_admin=session.get("is_admin", False)
    )


# =========================================================
# ADD TASK
# =========================================================

@app.route("/add-task", methods=["GET", "POST"])
@login_required
def add_task():

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        priority = request.form.get(
            "priority",
            "Medium"
        )

        due_date = request.form.get(
            "due_date",
            ""
        )

        if not title:

            flash(
                "Task title is required.",
                "danger"
            )

            return redirect(url_for("add_task"))

        task = Task(
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            status="pending",
            user_id=session["user_id"]
        )

        db.session.add(task)
        db.session.commit()

        flash(
            "Task added successfully! 🌸",
            "success"
        )

        return redirect(url_for("dashboard"))

    return render_template("add_task.html")


# =========================================================
# COMPLETE TASK
# =========================================================

@app.route("/complete-task/<int:task_id>")
@login_required
def complete_task(task_id):

    task = Task.query.filter_by(
        id=task_id,
        user_id=session["user_id"]
    ).first_or_404()

    if task.status != "completed":

        task.status = "completed"
        task.completed_at = datetime.utcnow()

        db.session.commit()

        session["completed_quote"] = random.choice(
            MOTIVATION_QUOTES
        )

    return redirect(url_for("dashboard"))


# =========================================================
# DELETE TASK
# =========================================================

@app.route("/delete-task/<int:task_id>")
@login_required
def delete_task(task_id):

    task = Task.query.filter_by(
        id=task_id,
        user_id=session["user_id"]
    ).first_or_404()

    db.session.delete(task)
    db.session.commit()

    flash(
        "Task deleted.",
        "success"
    )

    return redirect(url_for("dashboard"))


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
@admin_required
def admin():

    users = User.query.order_by(
        User.created_at.desc()
    ).all()

    tasks = Task.query.order_by(
        Task.created_at.desc()
    ).all()

    total_users = User.query.count()
    total_tasks = Task.query.count()

    completed_tasks = Task.query.filter_by(
        status="completed"
    ).count()

    pending_tasks = Task.query.filter_by(
        status="pending"
    ).count()

    return render_template(
        "admin.html",
        users=users,
        tasks=tasks,
        total_users=total_users,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks
    )


# =========================================================
# FORGOT PASSWORD
# =========================================================

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        user = User.query.filter_by(
            email=email
        ).first()

        if not user:

            flash(
                "If this email is registered, a verification code will be sent.",
                "info"
            )

            return redirect(
                url_for("forgot_password")
            )

        otp = str(
            random.randint(100000, 999999)
        )

        session["reset_email"] = email
        session["reset_otp"] = otp
        session["reset_otp_expiry"] = (
            datetime.utcnow() + timedelta(minutes=10)
        ).isoformat()

        try:

            if app.config["MAIL_USERNAME"]:

                message = Message(
                    subject="BloomTasks Password Reset",
                    recipients=[email]
                )

                message.body = f"""
Hello {user.username},

Your BloomTasks password reset verification code is:

{otp}

This code expires in 10 minutes.

If you did not request this, please ignore this email.

BloomTasks 🌸
"""

                mail.send(message)

                flash(
                    "Verification code sent to your email.",
                    "success"
                )

            else:

                print(
                    f"\n[BLOOMTASKS DEVELOPMENT OTP] {email}: {otp}\n"
                )

                flash(
                    "Mail is not configured. Development OTP was printed in the terminal.",
                    "info"
                )

        except Exception:

            print(
                f"\n[BLOOMTASKS OTP] {email}: {otp}\n"
            )

            flash(
                "Email could not be sent. Development OTP was printed in the terminal.",
                "warning"
            )

        return redirect(
            url_for("reset_password")
        )

    return render_template(
        "forgot_password.html"
    )


# =========================================================
# RESET PASSWORD
# =========================================================

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():

    if "reset_email" not in session:

        return redirect(
            url_for("forgot_password")
        )

    if request.method == "POST":

        entered_otp = request.form.get(
            "otp",
            ""
        ).strip()

        new_password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        saved_otp = session.get(
            "reset_otp"
        )

        expiry_string = session.get(
            "reset_otp_expiry"
        )

        if not saved_otp or not expiry_string:

            flash(
                "Verification session expired.",
                "danger"
            )

            return redirect(
                url_for("forgot_password")
            )

        expiry = datetime.fromisoformat(
            expiry_string
        )

        if datetime.utcnow() > expiry:

            session.pop("reset_otp", None)
            session.pop("reset_email", None)
            session.pop("reset_otp_expiry", None)

            flash(
                "OTP expired. Please request a new one.",
                "danger"
            )

            return redirect(
                url_for("forgot_password")
            )

        if entered_otp != saved_otp:

            flash(
                "Invalid verification code.",
                "danger"
            )

            return redirect(
                url_for("reset_password")
            )

        if len(new_password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )

            return redirect(
                url_for("reset_password")
            )

        if new_password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for("reset_password")
            )

        email = session["reset_email"]

        user = User.query.filter_by(
            email=email
        ).first()

        if not user:

            flash(
                "Account not found.",
                "danger"
            )

            return redirect(
                url_for("forgot_password")
            )

        user.password_hash = generate_password_hash(
            new_password
        )

        db.session.commit()

        session.pop("reset_otp", None)
        session.pop("reset_email", None)
        session.pop("reset_otp_expiry", None)

        flash(
            "Password changed successfully! Please login.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "reset_password.html",
        email=session.get("reset_email")
    )


# =========================================================
# CREATE DATABASE
# =========================================================

create_database()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )

