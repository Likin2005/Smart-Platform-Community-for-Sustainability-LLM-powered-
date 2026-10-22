
from flask import Flask, request, render_template, jsonify, url_for, send_from_directory, session
from main import retriever, chain
from langchain_ollama import OllamaLLM
import os
import json

app = Flask(__name__)
app.secret_key = 'Likin@2005'

POINTS_FILE = "points.json"

def load_points():
    """Load points from JSON file."""
    if not os.path.exists(POINTS_FILE):
        return 0
    with open(POINTS_FILE, "r") as f:
        data = json.load(f)
    return data.get("points", 0)

def save_points(points):
    """Save updated points to JSON file."""
    with open(POINTS_FILE, "w") as f:
        json.dump({"points": points}, f)

def count_verified_images():
    verified_folder = "static/uploads"
    if not os.path.exists(verified_folder):
        return 0 
    return len([
        f for f in os.listdir(verified_folder)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ])

UPLOAD_FOLDER = 'static/uploads'
POST_FOLDER =  'static/uploads'

def uploaded_file(filename):
    return send_from_directory(POST_FOLDER, filename)
os.makedirs(POST_FOLDER, exist_ok=True)

vision_model = OllamaLLM(model="llava")

@app.route('/')
def index():
    points = load_points()
    return render_template("index.html", points=points)

@app.route('/action_update', methods=['GET'])
def action_update():
    points = session.get("points", 0)
    return render_template("action_update.html", points=points)

@app.route('/ask_question', methods=['POST'])
def ask_question():
    user_question = request.form['question']
    context = retriever.invoke(user_question)
    result = chain.invoke({"context": context, "question": user_question})
    if hasattr(result, 'content'):
        result = result.content
    points = session.get("points", 0)
    return render_template('index.html', answer=result, user_question=user_question, points=points)

@app.route('/verify_image', methods=['POST'])
def verify_image():
    image = request.files['image']
    if not image:
        points = session.get("points", 0)
        return render_template('action_update.html', image_result="⚠️ No image uploaded.", points=points)

    image_path = os.path.join(UPLOAD_FOLDER, image.filename)
    image.save(image_path)

    prompt = """
    You are an expert sustainability inspector.
    Analyze the uploaded image and determine:
    1. Whether it shows eco-friendly activity (e.g. planting trees, watering plants, recycling, cleaning nature, etc.).
    2. If yes, provide:
        - A short description of the eco-friendly action.
        - A score from 1 to 5 based on environmental impact and sustainability.
        - A brief reason for the score.
    3. If not eco-friendly, respond clearly with "Not Verified" and explain why.

    Respond in this format:
    Status: [Verified or Not Verified]
    Description: [...]
    Score: [x/5]
    Reason: [...]
    """

    try:
        llava_with_image = vision_model.bind(images=[image_path])
        result = llava_with_image.invoke(prompt)

        if hasattr(result, 'content'):
            result = result.content
    except Exception as e:
        result = f"Error analyzing image: {str(e)}"

    try:
        text = (result or "").lower()
        if "verified" in text and "not verified" not in text:
            session["points"] = session.get("points", 0) + 2
    except Exception:
        pass

    points = session.get("points", 0)
    return render_template('action_update.html', image_result=result, points=points)

@app.route('/community', methods=["GET", "POST"])
def community():
    images = [
        f for f in os.listdir(POST_FOLDER)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]
    image_urls = [url_for('static', filename=f"uploads/{f}") for f in images]
    if request.method == "POST":
        points = load_points()
        points += 2
        save_points(points)
        return jsonify({"points": points})
    points = load_points()
    return render_template("community.html", images=image_urls, points=points)

@app.route('/community_post', methods=['POST'])
def community_post():
    session["points"] = session.get("points", 0) + 2
    return jsonify({"points": session.get("points", 0)})

@app.route('/points')
def get_points():
    return jsonify({"points": session.get("points", 0)})

@app.route('/games')
def games():
    return render_template('games.html')

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

@app.route('/waste_sorting')
def waste_sorting():
    return render_template('waste_sorting.html')

@app.route('/leader_board')
def leader_board():
    return render_template('leader_board.html')

@app.route("/profile")
def profile():
    user = {
        "name": "Keerthan",
        "email": "keerthan@gmail.com",
        "age": 20
    }
    points = load_points()
    verified_images = count_verified_images()
    return render_template("profile.html", user=user, points=points, verified_images=verified_images)

if __name__ == '__main__':
    app.run(debug=True)