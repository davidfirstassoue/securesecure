"""
server/main.py — Serveur Central de l'Université (SecureShare)
Port : 5000
Rôle : Annuaire de clés publiques + Boîte aux lettres de messages chiffrés.
Ce serveur ne voit jamais le contenu des messages. Il manipule uniquement
des enveloppes JSON opaques chiffrées de bout en bout.
"""

import os
import sys
import logging
import sqlite3
import json
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify, request, render_template, session
import datetime

# Chemin vers le dossier parent pour accéder au module shared
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE_DIR)

from shared.crypto_utils import compute_fingerprint

# ---------------------------------------------------------------------------
# Configuration des logs du Serveur
# ---------------------------------------------------------------------------
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server.log')
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Fichier rotatif de logs (1 Mo max, conserve 3 fichiers)
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=1000000, backupCount=3, encoding='utf-8')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

# Console de logs
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# Logger dédié à l'application
logger = logging.getLogger('secureshare')
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.propagate = False

# Intégrer également les logs HTTP de Flask/Werkzeug dans le fichier server.log
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.addHandler(file_handler)

app = Flask(__name__, template_folder='../client/templates', static_folder='../client/static')
app.secret_key = "secureshare_central_server_secret_2026"

# ---------------------------------------------------------------------------
# Stockage en base de données SQLite
# ---------------------------------------------------------------------------
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

def init_db():
    """Initialise la base de données SQLite pour stocker les enveloppes chiffrées et les tables scolaires."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table des enveloppes E2EE
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS envelopes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient TEXT NOT NULL,
        sender TEXT NOT NULL,
        envelope_json TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )
    ''')
    
    # Tables de scolarité
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS grades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_username TEXT NOT NULL,
        subject TEXT NOT NULL,
        grade REAL NOT NULL,
        coefficient INTEGER NOT NULL,
        date TEXT NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        day TEXT NOT NULL,
        slot1 TEXT,
        slot2 TEXT,
        slot3 TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payslips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_username TEXT NOT NULL,
        month TEXT NOT NULL,
        amount REAL NOT NULL,
        file_name TEXT NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bulletins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_username TEXT NOT NULL,
        period TEXT NOT NULL,
        gpa REAL NOT NULL,
        file_name TEXT NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admin_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_username TEXT NOT NULL,
        role TEXT NOT NULL,
        subject TEXT NOT NULL,
        message TEXT NOT NULL,
        date TEXT NOT NULL
    )
    ''')
    
    # Données initiales
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # Données de test scolarité
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", ('dupont', 'Jean Dupont', 'dupont123', 'student'))
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", ('martin', 'Claire Martin', 'martin123', 'student'))
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", ('prof_lefevre', 'Dr. Pierre Lefevre', 'lefevre123', 'teacher'))
        
        # Données administratives (pour le lien et les jointures)
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", ('alice', 'Alice (Comptable du Campus)', 'alice123', 'comptable'))
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", ('bob', 'Bob (Directrice de l\'Université)', 'bob123', 'directrice'))
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", ('charlie', 'Charlie (Secrétaire Général)', 'charlie123', 'secretaire'))
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", ('diana', 'Diana (Responsable RH)', 'diana123', 'rh'))
        
        # Notes de test
        cursor.execute("INSERT INTO grades (student_username, subject, grade, coefficient, date) VALUES (?, ?, ?, ?, ?)",
                       ('dupont', 'Mathématiques', 14.5, 3, '2026-06-15'))
        cursor.execute("INSERT INTO grades (student_username, subject, grade, coefficient, date) VALUES (?, ?, ?, ?, ?)",
                       ('dupont', 'Physique', 12.0, 3, '2026-06-18'))
        cursor.execute("INSERT INTO grades (student_username, subject, grade, coefficient, date) VALUES (?, ?, ?, ?, ?)",
                       ('dupont', 'Informatique', 16.5, 4, '2026-07-02'))
        cursor.execute("INSERT INTO grades (student_username, subject, grade, coefficient, date) VALUES (?, ?, ?, ?, ?)",
                       ('martin', 'Mathématiques', 11.0, 3, '2026-06-15'))
        cursor.execute("INSERT INTO grades (student_username, subject, grade, coefficient, date) VALUES (?, ?, ?, ?, ?)",
                       ('martin', 'Physique', 15.5, 3, '2026-06-18'))
        cursor.execute("INSERT INTO grades (student_username, subject, grade, coefficient, date) VALUES (?, ?, ?, ?, ?)",
                       ('martin', 'Informatique', 18.0, 4, '2026-07-02'))
        
        # Emplois du temps
        days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi']
        for day in days:
            cursor.execute("INSERT INTO schedules (username, day, slot1, slot2, slot3) VALUES (?, ?, ?, ?, ?)",
                            ('dupont', day, 'Mathématiques (08h00 - 11h00)', 'Physique (11h00 - 13h00)', 'Informatique (14h00 - 17h00)'))
            cursor.execute("INSERT INTO schedules (username, day, slot1, slot2, slot3) VALUES (?, ?, ?, ?, ?)",
                            ('martin', day, 'Physique (08h00 - 11h00)', 'Informatique (11h00 - 13h00)', 'Mathématiques (14h00 - 17h00)'))
            cursor.execute("INSERT INTO schedules (username, day, slot1, slot2, slot3) VALUES (?, ?, ?, ?, ?)",
                            ('prof_lefevre', day, 'Cours Math - Dupont/Martin (08h00 - 11h00)', 'Recherche Lab (11h00 - 13h00)', 'Encadrement Projet (14h00 - 17h00)'))

        # Bulletins de salaire
        cursor.execute("INSERT INTO payslips (teacher_username, month, amount, file_name) VALUES (?, ?, ?, ?)",
                       ('prof_lefevre', 'Mai 2026', 3240.50, 'bulletin_salaire_mai_2026.pdf'))
        cursor.execute("INSERT INTO payslips (teacher_username, month, amount, file_name) VALUES (?, ?, ?, ?)",
                       ('prof_lefevre', 'Juin 2026', 3240.50, 'bulletin_salaire_juin_2026.pdf'))
        
        # Bulletins trimestriels
        cursor.execute("INSERT INTO bulletins (student_username, period, gpa, file_name) VALUES (?, ?, ?, ?)",
                       ('dupont', '1er Semestre 2026', 14.33, 'bulletin_semestre_1_dupont.pdf'))
        cursor.execute("INSERT INTO bulletins (student_username, period, gpa, file_name) VALUES (?, ?, ?, ?)",
                       ('martin', '1er Semestre 2026', 14.83, 'bulletin_semestre_1_martin.pdf'))

        # Messages scolarité
        cursor.execute("INSERT INTO admin_messages (from_username, role, subject, message, date) VALUES (?, ?, ?, ?, ?)",
                       ('dupont', 'student', 'Demande de relevé officiel', 'Bonjour, je souhaiterais obtenir un relevé de notes officiel signé pour mon dossier de master. Merci.', '2026-07-10'))
        cursor.execute("INSERT INTO admin_messages (from_username, role, subject, message, date) VALUES (?, ?, ?, ?, ?)",
                       ('prof_lefevre', 'teacher', 'Absence exceptionnelle', 'Chers collègues, je serai absent le mardi 21 juillet pour assister à un séminaire externe. Mes cours seront reportés.', '2026-07-12'))
                       
    conn.commit()
    conn.close()

# Initialisation de la base de données au démarrage du serveur
init_db()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return jsonify({
        "service": "SecureShare — Serveur Central",
        "version": "1.0",
        "endpoints": [
            "GET  /publickey/<user>",
            "POST /send",
            "GET  /receive/<user>"
        ]
    })


@app.route('/publickey/<user>', methods=['GET'])
def get_publickey(user: str):
    """
    Annuaire de clés : retourne la clé publique RSA et son empreinte SHA-256.
    Les fichiers PEM sont dans shared/keys/<user>_public.pem.
    """
    user = user.strip().lower()
    pub_key_path = os.path.join(BASE_DIR, 'shared', 'keys', f'{user}_public.pem')

    if not os.path.exists(pub_key_path):
        return jsonify({"error": f"Clé publique introuvable pour l'utilisateur '{user}'."}), 404

    with open(pub_key_path, 'rb') as f:
        pub_pem = f.read()

    fingerprint = compute_fingerprint(pub_pem)

    return jsonify({
        "username": user,
        "public_key_pem": pub_pem.decode('utf-8'),
        "fingerprint": fingerprint
    }), 200


@app.route('/send', methods=['POST'])
def send_envelope():
    """
    Dépose une enveloppe chiffrée dans la boîte aux lettres du destinataire.
    Le serveur ne peut pas lire le contenu — il ne fait que le stocker dans SQLite.
    Format attendu : { "to": "bob", "from": "alice", "encrypted_aes_key": "...", ... }
    """
    envelope = request.get_json(silent=True)

    if not envelope:
        return jsonify({"error": "Corps de la requête JSON invalide ou manquant."}), 400

    recipient = envelope.get("to", "").strip().lower()
    sender = envelope.get("from", "").strip().lower()
    if not recipient:
        return jsonify({"error": "Champ 'to' manquant dans l'enveloppe."}), 400

    timestamp = envelope.get("timestamp", "")
    if not timestamp:
        import datetime
        timestamp = datetime.datetime.now().isoformat()

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO envelopes (recipient, sender, envelope_json, timestamp) VALUES (?, ?, ?, ?)",
            (recipient, sender, json.dumps(envelope), timestamp)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Erreur d'insertion SQLite : {str(e)}")
        return jsonify({"error": "Erreur interne de stockage réseau."}), 500

    logger.info(f"Enveloppe reçue de '{sender}' pour '{recipient}' et sauvegardée en base.")
    return jsonify({"status": "delivered", "recipient": recipient}), 200


@app.route('/receive/<user>', methods=['GET'])
def receive_envelope(user: str):
    """
    Récupère la boîte aux lettres complète d'un utilisateur (historique conservé dans SQLite).
    Le client déchiffrera le contenu localement avec sa clé privée.
    """
    user = user.strip().lower()
    inbox = []

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT envelope_json FROM envelopes WHERE recipient = ? ORDER BY timestamp ASC",
            (user,)
        )
        rows = cursor.fetchall()
        for row in rows:
            inbox.append(json.loads(row[0]))
        conn.close()
    except Exception as e:
        logger.error(f"Erreur de lecture SQLite : {str(e)}")
        return jsonify({"error": "Erreur interne de récupération réseau."}), 500

    logger.info(f"{len(inbox)} enveloppe(s) récupérée(s) pour '{user}'.")
    return jsonify(inbox), 200


# ---------------------------------------------------------------------------
# Helpers pour la base de données (Scolarité)
# ---------------------------------------------------------------------------
def _query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv


def _execute_db(query, args=()):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Routes Scolarité (Portail DMZ)
# ---------------------------------------------------------------------------
@app.route('/scolarite')
def scolarite_index():
    return render_template('scolarite.html')


@app.route('/api/scolarite/login', methods=['POST'])
def scolarite_login():
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip().lower()
    password = data.get('password', '').strip()
    
    user = _query_db("SELECT * FROM users WHERE username = ? AND password = ?", (username, password), one=True)
    if not user:
        return jsonify({"error": "Identifiant ou mot de passe incorrect."}), 401
    
    session['scolarite_user'] = user['username']
    session['scolarite_name'] = user['name']
    session['scolarite_role'] = user['role']
    
    return jsonify({
        "status": "ok",
        "user": {
            "username": user['username'],
            "name": user['name'],
            "role": user['role']
        }
    }), 200


@app.route('/api/scolarite/status', methods=['GET'])
def scolarite_status():
    if 'scolarite_user' not in session:
        return jsonify({"authenticated": False}), 200
    
    return jsonify({
        "authenticated": True,
        "username": session['scolarite_user'],
        "name": session['scolarite_name'],
        "role": session['scolarite_role']
    }), 200


@app.route('/api/scolarite/logout', methods=['POST'])
def scolarite_logout():
    session.pop('scolarite_user', None)
    session.pop('scolarite_name', None)
    session.pop('scolarite_role', None)
    return jsonify({"status": "ok"}), 200


@app.route('/api/scolarite/dashboard', methods=['GET'])
def scolarite_dashboard():
    if 'scolarite_user' not in session:
        return jsonify({"error": "Non authentifié"}), 401
    
    username = session['scolarite_user']
    role = session['scolarite_role']
    
    data = {}
    
    if role == 'student':
        # Grades
        grades_rows = _query_db("SELECT * FROM grades WHERE student_username = ? ORDER BY date DESC", (username,))
        data['grades'] = [dict(row) for row in grades_rows]
        
        # Bulletins
        bulletins_rows = _query_db("SELECT * FROM bulletins WHERE student_username = ?", (username,))
        data['bulletins'] = [dict(row) for row in bulletins_rows]
        
        # Schedule
        schedule_rows = _query_db("SELECT * FROM schedules WHERE username = ?", (username,))
        data['schedules'] = [dict(row) for row in schedule_rows]
        
        # Messages sent
        msg_rows = _query_db("SELECT * FROM admin_messages WHERE from_username = ? ORDER BY date DESC", (username,))
        data['messages'] = [dict(row) for row in msg_rows]
        
    elif role == 'teacher':
        # Payslips
        payslips_rows = _query_db("SELECT * FROM payslips WHERE teacher_username = ?", (username,))
        data['payslips'] = [dict(row) for row in payslips_rows]
        
        # Schedule
        schedule_rows = _query_db("SELECT * FROM schedules WHERE username = ?", (username,))
        data['schedules'] = [dict(row) for row in schedule_rows]
        
        # Messages sent
        msg_rows = _query_db("SELECT * FROM admin_messages WHERE from_username = ? ORDER BY date DESC", (username,))
        data['messages'] = [dict(row) for row in msg_rows]
        
        # Students lists with grades to edit
        student_grades = _query_db(
            "SELECT g.id, g.student_username, u.name as student_name, g.subject, g.grade, g.coefficient, g.date "
            "FROM grades g JOIN users u ON g.student_username = u.username ORDER BY u.name ASC"
        )
        data['class_grades'] = [dict(row) for row in student_grades]
        
        # List of students to add new grades
        students = _query_db("SELECT username, name FROM users WHERE role = 'student'")
        data['students_list'] = [dict(row) for row in students]
        
    return jsonify(data), 200


@app.route('/api/scolarite/add-grade', methods=['POST'])
def scolarite_add_grade():
    if 'scolarite_user' not in session or session['scolarite_role'] != 'teacher':
        return jsonify({"error": "Action réservée aux enseignants."}), 403
    
    data = request.get_json(silent=True) or {}
    student = data.get('student_username')
    subject = data.get('subject')
    grade_val = data.get('grade')
    coeff = data.get('coefficient', 1)
    
    if not student or not subject or grade_val is None:
        return jsonify({"error": "Champs obligatoires manquants."}), 400
    
    try:
        grade_float = float(grade_val)
    except ValueError:
        return jsonify({"error": "Note invalide."}), 400
        
    date_str = datetime.date.today().isoformat()
    
    _execute_db(
        "INSERT INTO grades (student_username, subject, grade, coefficient, date) VALUES (?, ?, ?, ?, ?)",
        (student, subject, grade_float, int(coeff), date_str)
    )
    return jsonify({"status": "ok", "message": "Note ajoutée."}), 200


@app.route('/api/scolarite/send-message', methods=['POST'])
def scolarite_send_message():
    if 'scolarite_user' not in session:
        return jsonify({"error": "Non authentifié."}), 401
    
    data = request.get_json(silent=True) or {}
    subject = data.get('subject', '').strip()
    message = data.get('message', '').strip()
    
    if not subject or not message:
        return jsonify({"error": "L'objet et le message sont requis."}), 400
        
    username = session['scolarite_user']
    role = session['scolarite_role']
    date_str = datetime.date.today().isoformat()
    
    _execute_db(
        "INSERT INTO admin_messages (from_username, role, subject, message, date) VALUES (?, ?, ?, ?, ?)",
        (username, role, subject, message, date_str)
    )
    return jsonify({"status": "ok", "message": "Message envoyé à l'administration."}), 200


# ---------------------------------------------------------------------------
# API Administrative pour la liaison LAN <-> DMZ
# ---------------------------------------------------------------------------
@app.route('/api/admin/messages', methods=['GET'])
def admin_messages():
    """
    [ADMIN] Retourne tous les messages scolaires pour le client local (LAN).
    """
    rows = _query_db(
        "SELECT m.*, u.name as sender_name FROM admin_messages m "
        "JOIN users u ON m.from_username = u.username ORDER BY m.date DESC"
    )
    return jsonify([dict(row) for row in rows]), 200


def write_server_info():
    """
    Détecte automatiquement l'adresse IP locale du serveur sur le WiFi/réseau,
    interroge ngrok pour voir s'il y a un tunnel actif, et écrit ces infos
    dans shared/server_info.json pour que le client s'y connecte de manière transparente.
    """
    import socket
    import requests
    
    local_ip = "127.0.0.1"
    try:
        # Tente de se connecter à un hôte externe pour trouver l'interface réseau active
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            pass

    ngrok_url = None
    try:
        # Ngrok expose ses tunnels actifs sur le port 4040 localement
        resp = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=1)
        if resp.status_code == 200:
            tunnels = resp.json().get('tunnels', [])
            for t in tunnels:
                public_url = t.get('public_url', '')
                if public_url:
                    ngrok_url = public_url.replace("https://", "").replace("http://", "")
    except Exception:
        pass

    preferred_address = ngrok_url if ngrok_url else local_ip
    info = {
        "server_ip": preferred_address,
        "local_ip": local_ip,
        "ngrok_url": ngrok_url,
        "port": 5000,
        "mode": "direct" if not ngrok_url else "vpn",
        "timestamp": datetime.datetime.now().isoformat()
    }

    shared_dir = os.path.join(BASE_DIR, 'shared')
    os.makedirs(shared_dir, exist_ok=True)
    info_path = os.path.join(shared_dir, 'server_info.json')
    try:
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=4)
        logger.info(f"Configuration réseau enregistrée automatiquement dans shared/server_info.json : {info}")
    except Exception as e:
        logger.error(f"Impossible d'écrire la configuration réseau automatique : {e}")


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("  SecureShare — SERVEUR CENTRAL DE L'UNIVERSITÉ")
    logger.info("  Adresse : https://0.0.0.0:5000 (HTTPS Activé)")
    logger.info("  Rôle    : Annuaire de clés + Boîte aux lettres chiffrée (DMZ)")
    logger.info("=" * 60)
    
    # Écrire la configuration automatique de l'IP du serveur
    write_server_info()
    
    # Lancement en HTTPS avec génération de certificat à la volée
    app.run(host='0.0.0.0', port=5000, debug=False, ssl_context='adhoc')
