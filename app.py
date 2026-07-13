import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "secure_share_mock_key"
app.config['UPLOAD_FOLDER'] = 'static/uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Mock Data
MEMBERS = [
    {"id": 1, "name": "Alice Dupont", "role": "Étudiant", "online": True},
    {"id": 2, "name": "Bob Martin", "role": "Administration", "online": False},
    {"id": 3, "name": "Charlie Dubois", "role": "Étudiant", "online": True},
    {"id": 4, "name": "Dr. Alan Turing", "role": "Administration", "online": True},
]

MESSAGES = {
    "1": [
        {"sender": "Alice Dupont", "text": "Bonjour, pouvez-vous m'envoyer le cours de cryptographie ?", "time": "10:30", "file_url": None},
        {"sender": "Me", "text": "Bien sûr, je le dépose tout de suite sur le canal sécurisé.", "time": "10:32", "file_url": None}
    ],
    "2": [
        {"sender": "Bob Martin", "text": "N'oubliez pas la réunion de demain concernant les accès serveurs.", "time": "09:15", "file_url": None}
    ]
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email', '')
    name = email.split('@')[0].capitalize() if '@' in email else email.capitalize()
    if not name:
        name = "Utilisateur"
    session['user'] = {"name": name, "role": "Étudiant"}
    return redirect(url_for('dashboard'))

@app.route('/signup', methods=['POST'])
def signup():
    name = request.form.get('name', 'Nouveau Membre')
    role = request.form.get('role', 'Étudiant')
    if role == 'admin':
        role = 'Administration'
    session['user'] = {"name": name, "role": role}
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    current_user = session.get('user', {"name": "Anonyme", "role": "Visiteur"})
    return render_template('dashboard.html', current_user=current_user)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        url = url_for('static', filename=f'uploads/{filename}')
        return jsonify({"url": url, "filename": filename})

@app.route('/api/members')
def api_members():
    query = request.args.get('q', '').lower()
    if query:
        filtered = [m for m in MEMBERS if query in m['name'].lower()]
        return jsonify(filtered)
    return jsonify(MEMBERS)

@app.route('/api/messages/<member_id>', methods=['GET', 'POST'])
def api_messages(member_id):
    if request.method == 'POST':
        data = request.json
        if str(member_id) not in MESSAGES:
            MESSAGES[str(member_id)] = []
        MESSAGES[str(member_id)].append({
            "sender": data.get("sender", "Me"),
            "text": data.get("text", ""),
            "file_url": data.get("file_url", None),
            "file_name": data.get("file_name", None),
            "time": data.get("time", "")
        })
        return jsonify({"status": "ok"})
    return jsonify(MESSAGES.get(str(member_id), []))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
