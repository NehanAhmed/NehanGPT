from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    redirect,
    url_for,
    session,
    flash,
    Response,
    stream_with_context,
)
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
import os
import secrets

from dotenv import load_dotenv
from mistralai import Mistral
import mistune
from werkzeug.utils import secure_filename

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# MongoDB Atlas connection string
app.config["MONGO_URI"] = (
    "mongodb+srv://flaskuser:flaskUser@nehangpt.wvuhxnq.mongodb.net/gpt?retryWrites=true&w=majority&appName=nehangpt"
)
mongo = PyMongo(app)

# File upload settings
UPLOAD_FOLDER = os.path.join(os.getcwd(), "static", "profile_pics")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Default system prompt
DEFAULT_SYSTEM_PROMPT = """You are Nehan GPT, a highly capable AI assistant. Your responses should be:
1. Helpful and informative
2. Clear and well-structured
3. Friendly but professional
4. Direct and concise
5. Safe and ethical

When coding:
- Provide complete, working solutions
- Include comments for clarity
- Follow best practices
- Explain complex concepts simply

Always maintain a helpful and positive tone while being accurate and honest in your responses."""

# Create indexes for better performance
with app.app_context():
    mongo.db.chat_sessions.create_index("owner")
    mongo.db.chat_messages.create_index([("session_id", 1), ("timestamp", 1)])


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Home route - show all previous chat sessions
@app.route("/")
def home():
    if "email" not in session:
        return redirect(url_for("login"))

    # Get all chat sessions for the user, ordered by most recent
    chat_sessions = list(
        mongo.db.chat_sessions.find({"owner": session["email"]}).sort("updated_at", -1)
    )

    # Fetch the user document
    user = mongo.db.users.find_one({"email": session["email"]})

    return render_template("index.html", chat_sessions=chat_sessions, user=user)


# Start new chat session
@app.route("/new_chat", methods=["POST"])
def new_chat():
    if "email" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    from datetime import datetime

    # Create new chat session
    session_data = {
        "owner": session["email"],
        "title": "New Chat",  # Default title, will be updated with first message
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "message_count": 0,
    }

    session_id = mongo.db.chat_sessions.insert_one(session_data).inserted_id

    return jsonify(
        {
            "success": True,
            "session_id": str(session_id),
            "message": "New chat session created",
        }
    )


# Chat route - handle chat requests
from datetime import datetime


@app.route("/chat", methods=["POST"])
def chat():
    if "email" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    user_message = data.get("message")
    session_id = data.get("session_id")

    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    # Convert session_id to ObjectId if it's a string
    if isinstance(session_id, str):
        try:
            session_id = ObjectId(session_id)
        except:
            return jsonify({"error": "Invalid session ID"}), 400

    # Verify session exists and belongs to user
    chat_session = mongo.db.chat_sessions.find_one(
        {"_id": session_id, "owner": session["email"]}
    )

    if not chat_session:
        return jsonify({"error": "Chat session not found"}), 404

    # Send message to Mistral
    api_key = "etDHTVbCUetZdU5ib3i8jBKfcTKOwERe"
    model = "mistral-small-2503"
    client = Mistral(api_key=api_key)

    try:
        chat_response = client.chat.complete(
            model=model,
            messages=[{"role": "user", "content": user_message}],
        )
        bot_response = chat_response.choices[0].message.content
    except Exception as e:
        return jsonify({"error": "Failed to get AI response"}), 500

    # Save user message
    user_msg = {
        "session_id": session_id,
        "message_type": "user",
        "content": user_message,
        "timestamp": datetime.utcnow(),
    }
    mongo.db.chat_messages.insert_one(user_msg)

    # Save bot response
    bot_msg = {
        "session_id": session_id,
        "message_type": "bot",
        "content": bot_response,
        "timestamp": datetime.utcnow(),
    }
    mongo.db.chat_messages.insert_one(bot_msg)

    # Update session info
    update_operations = {
        "$set": {"updated_at": datetime.utcnow()},
        "$inc": {"message_count": 2},  # User message + bot response
    }

    # Update title with first message if it's still "New Chat"
    if chat_session.get("title") == "New Chat":
        update_operations["$set"]["title"] = user_message[:50] + (
            "..." if len(user_message) > 50 else ""
        )

    mongo.db.chat_sessions.update_one({"_id": session_id}, update_operations)

    return jsonify({"reply": bot_response, "session_id": str(session_id)})


# Get chat history for a specific session
@app.route("/chat_history/<session_id>")
def get_chat_history(session_id):
    if "email" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        session_obj_id = ObjectId(session_id)
    except:
        return jsonify({"error": "Invalid session ID"}), 400

    # Verify session belongs to user
    chat_session = mongo.db.chat_sessions.find_one(
        {"_id": session_obj_id, "owner": session["email"]}
    )

    if not chat_session:
        return jsonify({"error": "Chat session not found"}), 404

    # Get all messages for this session
    messages = list(
        mongo.db.chat_messages.find({"session_id": session_obj_id}).sort("timestamp", 1)
    )

    # Convert ObjectIds to strings for JSON serialization
    for msg in messages:
        msg["_id"] = str(msg["_id"])
        msg["session_id"] = str(msg["session_id"])

    return jsonify(
        {
            "session_info": {
                "id": str(chat_session["_id"]),
                "title": chat_session["title"],
                "created_at": chat_session["created_at"].isoformat(),
                "message_count": chat_session.get("message_count", 0),
            },
            "messages": messages,
        }
    )


# Delete a chat session and all its messages
@app.route("/delete_session/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    if "email" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        session_obj_id = ObjectId(session_id)
    except:
        return jsonify({"error": "Invalid session ID"}), 400

    # Verify session belongs to user
    chat_session = mongo.db.chat_sessions.find_one(
        {"_id": session_obj_id, "owner": session["email"]}
    )

    if not chat_session:
        return jsonify({"error": "Chat session not found"}), 404

    # Delete all messages for this session
    mongo.db.chat_messages.delete_many({"session_id": session_obj_id})

    # Delete the session
    mongo.db.chat_sessions.delete_one({"_id": session_obj_id})

    return jsonify({"success": True, "message": "Chat session deleted"})


# Update session title
@app.route("/update_session_title/<session_id>", methods=["PUT"])
def update_session_title(session_id):
    if "email" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    new_title = data.get("title", "").strip()

    if not new_title:
        return jsonify({"error": "Title cannot be empty"}), 400

    try:
        session_obj_id = ObjectId(session_id)
    except:
        return jsonify({"error": "Invalid session ID"}), 400

    # Update session title
    result = mongo.db.chat_sessions.update_one(
        {"_id": session_obj_id, "owner": session["email"]},
        {"$set": {"title": new_title, "updated_at": datetime.utcnow()}},
    )

    if result.matched_count == 0:
        return jsonify({"error": "Chat session not found"}), 404

    return jsonify({"success": True, "message": "Title updated"})


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        session["email"] = request.form["email"]
        session["password"] = bcrypt.generate_password_hash(
            request.form["password"]
        ).decode("utf-8")
        return redirect(url_for("onboarding_step2"))
    return render_template("register.html")


@app.route("/onboarding/step2", methods=["GET", "POST"])
def onboarding_step2():
    if request.method == "POST":
        session["name"] = request.form["name"]
        return redirect(url_for("onboarding_step3"))
    return render_template("onboard_name.html")


@app.route("/onboarding/step3", methods=["GET", "POST"])
def onboarding_step3():
    if request.method == "POST":
        profile_pic = request.files.get("profile_pic")  # optional
        user = {
            "email": session["email"],
            "password": session["password"],
            "name": session["name"],
        }
        if profile_pic and allowed_file(profile_pic.filename):
            if not os.path.exists(app.config["UPLOAD_FOLDER"]):
                os.makedirs(app.config["UPLOAD_FOLDER"])
            filename = secure_filename(session["email"] + "_" + profile_pic.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            profile_pic.save(filepath)
            user["profile_pic"] = f"profile_pics/{filename}"
        mongo.db.users.insert_one(user)
        session["email"] = user["email"]  # auto-login
        flash("Registration complete!")
        return redirect(url_for("home"))
    return render_template("onboard_more.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = mongo.db.users.find_one({"email": email})
        if user and bcrypt.check_password_hash(user["password"], password):

            session["email"] = user["email"]
            flash("Logged in successfully!")
            return redirect(url_for("home"))
        flash("Invalid credentials!")
        return redirect(url_for("login"))

    return render_template("login.html")


# Update the settings route to handle system prompt
@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "email" not in session:
        return redirect(url_for("login"))

    user = mongo.db.users.find_one({"email": session["email"]})

    if request.method == "POST":
        name = request.form.get("name")
        system_prompt = request.form.get("system_prompt")
        profile_pic = request.files.get("profile_pic")

        update_data = {
            "name": name,
            "system_prompt": system_prompt if system_prompt.strip() else None
        }

        if profile_pic and allowed_file(profile_pic.filename):
            if not os.path.exists(app.config["UPLOAD_FOLDER"]):
                os.makedirs(app.config["UPLOAD_FOLDER"])
            filename = secure_filename(session["email"] + "_" + profile_pic.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            profile_pic.save(filepath)
            update_data["profile_pic"] = f"profile_pics/{filename}"

        mongo.db.users.update_one({"email": session["email"]}, {"$set": update_data})
        flash("Profile updated successfully!")
        return redirect(url_for("settings"))

    return render_template("setting.html", 
                         user=user, 
                         default_system_prompt=DEFAULT_SYSTEM_PROMPT)


@app.route("/logout")
def logout():
    session.pop("email", None)
    flash("Logged out successfully.")
    return redirect(url_for("login"))


# Update the stream_chat function to use custom system prompt
@app.route("/stream_chat", methods=["POST"])
def stream_chat():
    if "email" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    user_message = data.get("message")
    session_id = data.get("session_id")

    # Get user's custom system prompt or use default
    user = mongo.db.users.find_one({"email": session["email"]})
    system_prompt = user.get("system_prompt") or DEFAULT_SYSTEM_PROMPT

    def generate():
        from mistralai import Mistral
        import os

        api_key = os.environ.get("MISTRAL_API_KEY", "etDHTVbCUetZdU5ib3i8jBKfcTKOwERe")
        model = "mistral-small-2503"
        client = Mistral(api_key=api_key)

        stream_response = client.chat.stream(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ]
        )
        for chunk in stream_response:
            content = chunk.data.choices[0].delta.content
            if content:
                yield f"data: {content}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@app.route("/change_password", methods=["POST"])
def change_password():
    if "email" not in session:
        return redirect(url_for("login"))
    
    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")
    
    user = mongo.db.users.find_one({"email": session["email"]})
    
    if not user or not bcrypt.check_password_hash(user["password"], current_password):
        flash("Current password is incorrect", "danger")
        return redirect(url_for("settings"))
        
    if new_password != confirm_password:
        flash("New passwords don't match", "danger")
        return redirect(url_for("settings"))
        
    hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")
    mongo.db.users.update_one(
        {"email": session["email"]},
        {"$set": {"password": hashed_password}}
    )
    
    flash("Password updated successfully", "success")
    return redirect(url_for("settings"))


if __name__ == "__main__":
    app.run(debug=True)
