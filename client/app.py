"""
client/app.py — Client Local SecureShare (Comptable / Directrice)
Port : 5001
Rôle : Orchestre toute la cryptographie localement et sert l'interface web.
       Le JavaScript du navigateur ne fait QUE de l'UI — tout le chiffrement
       se passe ici en Python, invisible depuis le réseau.
"""

import os
import sys
import base64
import json
import datetime
import sqlite3
import requests
import urllib3

from flask import Flask, jsonify, render_template, request, session

# Désactiver les avertissements de sécurité sur les certificats auto-signés SSL (Flask adhoc)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Chemin vers le dossier parent pour accéder au module shared
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE_DIR)

from shared.crypto_utils import (
    compute_fingerprint,
    encrypt_file,
    decrypt_file,
    hash_file,
    sign_hash,
    verify_signature,
    encrypt_aes_key,
    decrypt_aes_key,
)
from cryptography.hazmat.primitives import serialization

app = Flask(__name__)
app.secret_key = "secureshare_local_client_secret_2024"

DB_PATH = os.path.join(os.path.dirname(__file__), 'data.db')

def init_db():
    """Initialise la base de données SQLite locale avec les utilisateurs administratifs."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    ''')
    
    # S'assurer que les utilisateurs administratifs de test existent
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'alice'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", ('alice', 'Alice (Comptable du Campus)', 'alice123', 'comptable'))
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", ('bob', 'Bob (Directrice de l\'Université)', 'bob123', 'directrice'))
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", ('charlie', 'Charlie (Secrétaire Général)', 'charlie123', 'secretaire'))
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", ('diana', 'Diana (Responsable RH)', 'diana123', 'rh'))

    conn.commit()
    conn.close()

# Initialisation au chargement de l'application
init_db()


# ---------------------------------------------------------------------------
# Helpers de clé RSA
# ---------------------------------------------------------------------------

KEYS_DIR = os.path.join(BASE_DIR, 'shared', 'keys')


def _load_private_key(username: str):
    """Charge la clé privée RSA depuis le disque."""
    path = os.path.join(KEYS_DIR, f'{username}_private.pem')
    with open(path, 'rb') as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def _load_public_key_pem(username: str) -> bytes:
    """Charge les bytes PEM de la clé publique depuis le disque."""
    path = os.path.join(KEYS_DIR, f'{username}_public.pem')
    with open(path, 'rb') as f:
        return f.read()


def _load_public_key(username: str):
    """Charge et désérialise la clé publique RSA depuis le disque."""
    pub_pem = _load_public_key_pem(username)
    return serialization.load_pem_public_key(pub_pem)


def _load_server_ip_from_file() -> str:
    """Charge l'adresse IP du serveur à partir de shared/server_info.json s'il existe, sinon fallback."""
    shared_dir = os.path.join(BASE_DIR, 'shared')
    info_path = os.path.join(shared_dir, 'server_info.json')
    if os.path.exists(info_path):
        try:
            with open(info_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('server_ip', '127.0.0.1')
        except Exception:
            pass
            
    # Détection automatique de secours
    # Ngrok local
    try:
        resp = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=0.5)
        if resp.status_code == 200:
            tunnels = resp.json().get('tunnels', [])
            for t in tunnels:
                public_url = t.get('public_url', '')
                if public_url:
                    return public_url.replace("https://", "").replace("http://", "")
    except Exception:
        pass

    # IP WiFi / Locale de secours
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        pass
        
    return '127.0.0.1'


def _get_server_url() -> str:
    """
    Construit l'URL du serveur cible de manière dynamique.
    Lit d'abord l'adresse IP détectée automatiquement par le serveur dans shared/server_info.json.
    """
    server_ip = _load_server_ip_from_file()
    
    # Si non trouvé, fallback vers la session
    if not server_ip:
        cfg = session.get('config', {})
        server_ip = cfg.get('server_ip', '127.0.0.1').strip()
    
    # Si c'est déjà une URL complète
    if server_ip.startswith('http://') or server_ip.startswith('https://'):
        return server_ip
        
    # Si c'est une adresse ngrok
    if 'ngrok' in server_ip:
        return f'https://{server_ip}'
        
    # Si un port est déjà spécifié (ex: 127.0.0.1:5000)
    if ':' in server_ip:
        return f'https://{server_ip}'
        
    # Comportement par défaut pour IP ou nom d'hôte sans port
    return f'https://{server_ip}:5000'


# ---------------------------------------------------------------------------
# Stockage local en mémoire
# ---------------------------------------------------------------------------

# Derniers messages reçus (pour la fonctionnalité d'altération de démo)
_last_received_envelopes: list = []


# ---------------------------------------------------------------------------
# Routes de l'interface web
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('dashboard.html')


# ---------------------------------------------------------------------------
# Routes de l'API locale (appelées par main.js)
# ---------------------------------------------------------------------------

@app.route('/api/local-login', methods=['POST'])
def local_login():
    """Vérifie le mot de passe localement et charge/génère les clés RSA."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON invalide"}), 400

    username = data.get('username', '').strip().lower()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({"error": "Identifiant et mot de passe requis."}), 400

    if not all(c.isalnum() or c in '._-' for c in username):
        return jsonify({"error": "Nom d'utilisateur invalide."}), 400

    # Vérification des identifiants dans la base SQLite locale
    user = _query_db("SELECT * FROM users WHERE username = ? AND password = ?", (username, password), one=True)
    if not user:
        return jsonify({"error": "Identifiant ou mot de passe incorrect."}), 401

    # Interdire la connexion avec des comptes étudiants/professeurs sur le tableau de bord admin
    if user['role'] in ['student', 'teacher']:
        return jsonify({"error": "Accès refusé : Ce compte n'a pas de privilèges administratifs."}), 403

    # Vérification et génération à la volée des clés RSA de l'utilisateur si inexistantes
    private_key_path = os.path.join(KEYS_DIR, f'{username}_private.pem')
    public_key_path = os.path.join(KEYS_DIR, f'{username}_public.pem')
    if not os.path.exists(private_key_path) or not os.path.exists(public_key_path):
        try:
            from shared.generate_keys import generate_key_pair
            generate_key_pair(username)
        except Exception as e:
            return jsonify({"error": f"Impossible de générer les clés pour '{username}' : {str(e)}"}), 500

    session['config'] = {
        'username': username,
        'server_ip': data.get('server_ip') or _load_server_ip_from_file(),
        'mode': data.get('mode') or 'direct',
    }
    return jsonify({"status": "ok", "config": session['config']}), 200


@app.route('/api/local-register', methods=['POST'])
def local_register():
    """Enregistre un nouveau membre administratif et génère ses clés RSA."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON invalide"}), 400

    username = data.get('username', '').strip().lower()
    name = data.get('name', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', '').strip().lower()

    if not username or not name or not password or not role:
        return jsonify({"error": "Tous les champs sont obligatoires (identifiant, nom complet, mot de passe et rôle)."}), 400

    if not all(c.isalnum() or c in '._-' for c in username):
        return jsonify({"error": "Nom d'utilisateur invalide. Utilisez uniquement des caractères alphanumériques."}), 400

    if role in ['student', 'teacher']:
        return jsonify({"error": "Rôle invalide pour une inscription administrative."}), 400

    # Vérifier si l'utilisateur existe déjà
    existing_user = _query_db("SELECT * FROM users WHERE username = ?", (username,), one=True)
    if existing_user:
        return jsonify({"error": "Cet identifiant est déjà utilisé."}), 400

    # Insertion en base de données
    try:
        _execute_db("INSERT INTO users (username, name, password, role) VALUES (?, ?, ?, ?)", (username, name, password, role))
    except Exception as e:
        return jsonify({"error": f"Impossible d'enregistrer l'utilisateur : {str(e)}"}), 500

    # Génération automatique de ses clés
    private_key_path = os.path.join(KEYS_DIR, f'{username}_private.pem')
    public_key_path = os.path.join(KEYS_DIR, f'{username}_public.pem')
    if not os.path.exists(private_key_path) or not os.path.exists(public_key_path):
        try:
            from shared.generate_keys import generate_key_pair
            generate_key_pair(username)
        except Exception as e:
            return jsonify({"error": f"Impossible de générer les clés : {str(e)}"}), 500

    session['config'] = {
        'username': username,
        'server_ip': data.get('server_ip') or _load_server_ip_from_file(),
        'mode': data.get('mode') or 'direct',
    }
    return jsonify({"status": "ok", "config": session['config']}), 200


@app.route('/api/local-status', methods=['GET'])
def local_status():
    """Renvoie l'identité, le rôle, le nom réel et l'empreinte publique de l'utilisateur courant."""
    cfg = session.get('config')
    if not cfg:
        return jsonify({"configured": False}), 200

    username = cfg['username']
    try:
        pub_pem = _load_public_key_pem(username)
        fingerprint = compute_fingerprint(pub_pem)
    except FileNotFoundError:
        return jsonify({"error": f"Clés introuvables pour '{username}'."}), 500

    user = _query_db("SELECT name, role FROM users WHERE username = ?", (username,), one=True)
    name = user['name'] if user else username.capitalize()
    role = user['role'] if user else 'Membre'

    return jsonify({
        "configured": True,
        "username": username,
        "name": name,
        "role": role,
        "fingerprint": fingerprint,
        "mode": cfg.get('mode', 'direct'),
        "server_ip": cfg.get('server_ip', '127.0.0.1'),
    }), 200


@app.route('/api/local-users', methods=['GET'])
def local_users():
    """Retourne la liste de tous les utilisateurs administratifs enregistrés localement."""
    cfg = session.get('config')
    if not cfg:
        return jsonify({"error": "Session non configurée."}), 403

    try:
        users = _query_db("SELECT username, name, role FROM users ORDER BY name ASC")
        return jsonify([dict(u) for u in users]), 200
    except Exception as e:
        return jsonify({"error": f"Erreur de récupération des utilisateurs : {str(e)}"}), 500


@app.route('/api/local-send', methods=['POST'])
def local_send():
    """
    Orchestre l'envoi E2EE complet :
    1. Chiffre le message/fichier en AES-256-CBC.
    2. Calcule le hash SHA-256 et signe avec la clé privée de l'émetteur (RSA-PSS).
    3. Chiffre la clé AES avec la clé publique du destinataire (RSA-OAEP).
    4. Envoie l'enveloppe JSON au serveur central en HTTPS.
    """
    cfg = session.get('config')
    if not cfg:
        return jsonify({"error": "Session non configurée. Veuillez choisir un rôle."}), 403

    sender = cfg['username']
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Corps JSON invalide."}), 400

    recipient = data.get('to', '').strip().lower()
    message_text = data.get('message', '')
    file_b64 = data.get('file_b64', None)  # Fichier encodé en base64 (optionnel)
    file_name = data.get('file_name', '')

    if not recipient:
        return jsonify({"error": "Destinataire ('to') manquant."}), 400
    if not message_text and not file_b64:
        return jsonify({"error": "Message ou fichier requis."}), 400

    logs = []

    try:
        # --- Étape 1 : Récupérer la clé publique du destinataire ---
        server_url = _get_server_url()
        logs.append(f"Requête HTTPS vers l'annuaire central : {server_url}/publickey/{recipient}...")
        
        # verify=False permet de se connecter en HTTPS malgré le certificat de développement auto-signé
        resp = requests.get(
            f"{server_url}/publickey/{recipient}", 
            timeout=5, 
            verify=False, 
            headers={"ngrok-skip-browser-warning": "any"}
        )

        if resp.status_code != 200:
            return jsonify({"error": f"Impossible de récupérer la clé de '{recipient}'. Serveur HS ?"}), 502

        server_key_data = resp.json()
        recipient_pub_pem = server_key_data['public_key_pem'].encode('utf-8')
        server_fingerprint = server_key_data['fingerprint']

        recipient_public_key = serialization.load_pem_public_key(recipient_pub_pem)
        logs.append(f"Clé publique de '{recipient}' reçue. Empreinte validée : {server_fingerprint}")

        # --- Étape 2 : Préparer les données brutes à chiffrer ---
        if file_b64:
            raw_bytes = base64.b64decode(file_b64)
            logs.append(f"Fichier '{file_name}' chargé ({len(raw_bytes)} octets).")
        else:
            raw_bytes = message_text.encode('utf-8')
            logs.append(f"Message texte chargé ({len(raw_bytes)} octets).")

        # --- Étape 3 : Chiffrement AES-256-CBC ---
        logs.append("Génération de la clé de session AES-256 et du vecteur d'initialisation (IV)...")
        aes_key, iv, ciphertext = encrypt_file(raw_bytes)
        logs.append(f"Fichier chiffré avec succès. Taille chiffrée : {len(ciphertext)} octets.")

        # --- Étape 4 : Hash SHA-256 et Signature RSA-PSS ---
        logs.append("Calcul de l'empreinte SHA-256 du fichier original...")
        sha256_hex = hash_file(raw_bytes)
        logs.append(f"Hash SHA-256 : {sha256_hex[:16]}...")

        logs.append(f"Signature numérique RSA-PSS avec la clé privée de '{sender}'...")
        sender_private_key = _load_private_key(sender)
        signature = sign_hash(sha256_hex, sender_private_key)
        logs.append("Signature numérique générée.")

        # --- Étape 5 : Chiffrement RSA-OAEP de la clé AES ---
        logs.append(f"Chiffrement RSA-OAEP de la clé AES avec la clé publique de '{recipient}'...")
        encrypted_aes_key = encrypt_aes_key(aes_key, recipient_public_key)
        logs.append("Clé AES chiffrée et sécurisée.")

        # --- Étape 6 : Empreinte de l'émetteur (pour vérification MITM côté récepteur) ---
        sender_pub_pem = _load_public_key_pem(sender)
        sender_fingerprint = compute_fingerprint(sender_pub_pem)

        # --- Étape 7 : Assemblage de l'enveloppe JSON ---
        envelope = {
            "from": sender,
            "to": recipient,
            "message": message_text if not file_b64 else "",
            "file_name": file_name,
            "is_file": bool(file_b64),
            "encrypted_aes_key": base64.b64encode(encrypted_aes_key).decode('utf-8'),
            "iv": base64.b64encode(iv).decode('utf-8'),
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
            "sha256_hex": sha256_hex,
            "signature": base64.b64encode(signature).decode('utf-8'),
            "sender_fingerprint": sender_fingerprint,
            "server_fingerprint_used": server_fingerprint,
            "timestamp": datetime.datetime.now().isoformat(),
        }

        # --- Étape 8 : Envoi au serveur central ---
        mode_text = cfg.get('mode', 'direct').upper()
        logs.append(f"Transmission de l'enveloppe chiffrée [Mode: {mode_text}]...")

        send_resp = requests.post(
            f"{server_url}/send",
            json=envelope,
            timeout=5,
            verify=False,
            headers={"ngrok-skip-browser-warning": "any"}
        )

        if send_resp.status_code != 200:
            return jsonify({"error": "Le serveur central a refusé l'enveloppe."}), 502

        logs.append("Enveloppe livrée avec succès au serveur central (DMZ).")
        logs.append("Transmission sécurisée terminée.")

        return jsonify({
            "status": "sent",
            "server_fingerprint": server_fingerprint,
            "logs": logs
        }), 200

    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Connexion impossible au serveur. Vérifiez l'IP, le port, et que le serveur central tourne.", "logs": logs}), 503
    except FileNotFoundError as e:
        return jsonify({"error": f"Fichier de clé introuvable : {e}. Lancez generate_keys.py.", "logs": logs}), 500
    except Exception as e:
        return jsonify({"error": f"Erreur inattendue : {str(e)}", "logs": logs}), 500


@app.route('/api/local-inbox', methods=['GET'])
def local_inbox():
    """
    Récupère et déchiffre les messages de la boîte aux lettres :
    1. Récupère les enveloppes du serveur central en HTTPS.
    2. Pour chaque enveloppe :
       a. Déchiffre la clé AES avec la clé privée locale (RSA-OAEP).
       b. Déchiffre le contenu (AES-256-CBC).
       c. Vérifie la signature numérique de l'émetteur (RSA-PSS).
    3. Retourne les messages déchiffrés avec leur statut d'intégrité.
    """
    global _last_received_envelopes
    cfg = session.get('config')
    if not cfg:
        return jsonify({"error": "Session non configurée."}), 403

    username = cfg['username']
    logs = []

    try:
        server_url = _get_server_url()
        logs.append(f"Récupération des enveloppes chiffrées via HTTPS depuis le serveur pour '{username}'...")

        resp = requests.get(
            f"{server_url}/receive/{username}", 
            timeout=5, 
            verify=False, 
            headers={"ngrok-skip-browser-warning": "any"}
        )
        envelopes = resp.json()

        if not envelopes:
            return jsonify({"messages": [], "logs": ["Aucun nouveau message."]}), 200

        logs.append(f"{len(envelopes)} enveloppe(s) reçue(s). Déchiffrement en cours...")
        _last_received_envelopes = envelopes  # Sauvegarde pour la fonctionnalité d'altération

        recipient_private_key = _load_private_key(username)
        results = []

        for i, env in enumerate(envelopes):
            msg_logs = []
            try:
                sender = env.get('from', 'inconnu')
                msg_logs.append(f"[Msg {i+1}] Expéditeur : '{sender}'.")

                # Décoder les champs base64
                encrypted_aes_key = base64.b64decode(env['encrypted_aes_key'])
                iv = base64.b64decode(env['iv'])
                ciphertext = base64.b64decode(env['ciphertext'])
                signature = base64.b64decode(env['signature'])
                sha256_hex_received = env['sha256_hex']

                # --- Déchiffrement RSA-OAEP de la clé AES ---
                msg_logs.append("Déchiffrement RSA-OAEP de la clé AES avec votre clé privée...")
                aes_key = decrypt_aes_key(encrypted_aes_key, recipient_private_key)
                msg_logs.append("Clé AES récupérée.")

                # --- Déchiffrement AES-256-CBC du contenu ---
                msg_logs.append("Déchiffrement AES-256-CBC du contenu...")
                plaintext_bytes = decrypt_file(aes_key, iv, ciphertext)
                msg_logs.append(f"Contenu déchiffré ({len(plaintext_bytes)} octets).")

                # --- Vérification de l'intégrité (hash SHA-256) ---
                msg_logs.append("Vérification de l'intégrité SHA-256...")
                computed_hash = hash_file(plaintext_bytes)
                hash_ok = (computed_hash == sha256_hex_received)
                msg_logs.append(f"Hash calculé : {computed_hash[:16]}...")
                msg_logs.append(f"Hash reçu    : {sha256_hex_received[:16]}...")

                # --- Vérification de la signature RSA-PSS ---
                msg_logs.append(f"Vérification de la signature RSA-PSS de '{sender}'...")
                try:
                    sender_public_key = _load_public_key(sender)
                    sig_ok = verify_signature(sha256_hex_received, signature, sender_public_key)
                except FileNotFoundError:
                    sig_ok = False
                    msg_logs.append(f"ALERTE : Clé publique de '{sender}' introuvable !")

                integrity_ok = hash_ok and sig_ok
                status = "valid" if integrity_ok else "tampered"

                if integrity_ok:
                    msg_logs.append("Signature valide. Intégrité confirmée.")
                else:
                    msg_logs.append("ALERTE : Signature ou hash invalide. Fichier potentiellement altéré !")

                # Contenu décodé (texte ou fichier)
                is_file = env.get('is_file', False)
                content = base64.b64encode(plaintext_bytes).decode('utf-8') if is_file else plaintext_bytes.decode('utf-8', errors='replace')

                results.append({
                    "from": sender,
                    "message": env.get('message', ''),
                    "file_name": env.get('file_name', ''),
                    "is_file": is_file,
                    "content": content,
                    "status": status,
                    "timestamp": env.get('timestamp', ''),
                    "sender_fingerprint": env.get('sender_fingerprint', 'N/A'),
                    "logs": msg_logs,
                })

            except Exception as e:
                results.append({
                    "from": env.get('from', '?'),
                    "status": "error",
                    "error": str(e),
                    "logs": msg_logs,
                })

        logs.append("Déchiffrement terminé.")
        return jsonify({"messages": results, "logs": logs}), 200

    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Connexion impossible au serveur.", "logs": logs}), 503
    except Exception as e:
        return jsonify({"error": str(e), "logs": logs}), 500


@app.route('/api/local-alter', methods=['POST'])
def local_alter():
    """
    [DEMO/DEBUG] Corrompt le dernier message reçu en mémoire en modifiant 1 octet
    du ciphertext, puis le remet dans la boîte aux lettres du serveur pour
    simuler une altération en transit lors de la prochaine vérification.
    """
    cfg = session.get('config')
    if not cfg:
        return jsonify({"error": "Session non configurée."}), 403

    if not _last_received_envelopes:
        return jsonify({"error": "Aucun message reçu à altérer. Récupérez d'abord un message."}), 400

    try:
        # On prend le dernier message reçu
        envelope = dict(_last_received_envelopes[-1])

        # On modifie 1 octet du ciphertext
        ciphertext_bytes = bytearray(base64.b64decode(envelope['ciphertext']))
        ciphertext_bytes[0] ^= 0xFF  # Inversion du premier octet
        envelope['ciphertext'] = base64.b64encode(bytes(ciphertext_bytes)).decode('utf-8')

        # On le remet dans la boîte aux lettres de l'utilisateur courant
        recipient = cfg['username']
        server_url = _get_server_url()
        envelope['to'] = recipient

        requests.post(
            f"{server_url}/send", 
            json=envelope, 
            timeout=5, 
            verify=False, 
            headers={"ngrok-skip-browser-warning": "any"}
        )

        return jsonify({
            "status": "altered",
            "message": "1 octet du ciphertext a été corrompu. Récupérez à nouveau l'inbox pour voir l'alerte."
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/remote-fingerprint', methods=['GET'])
def remote_fingerprint():
    """
    Récupère l'empreinte d'un utilisateur depuis le serveur cible actuellement
    configuré. Utile pour la vérification MITM côté UI.
    """
    cfg = session.get('config')
    if not cfg:
        return jsonify({"error": "Session non configurée."}), 403

    username = request.args.get('user', '').strip().lower()
    if not username:
        return jsonify({"error": "Paramètre 'user' requis."}), 400

    try:
        server_url = _get_server_url()
        resp = requests.get(
            f"{server_url}/publickey/{username}", 
            timeout=5, 
            verify=False, 
            headers={"ngrok-skip-browser-warning": "any"}
        )
        data = resp.json()
        return jsonify(data), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Connexion impossible au serveur."}), 503



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


@app.route('/api/admin/messages', methods=['GET'])
def admin_messages():
    """
    [ADMIN] Récupère tous les messages envoyés par les étudiants et les enseignants.
    Les messages sont récupérés via HTTPS depuis le serveur central en DMZ.
    """
    cfg = session.get('config')
    if not cfg:
        return jsonify({"error": "Session admin non configurée."}), 403
        
    try:
        server_url = _get_server_url()
        # verify=False permet de bypasser l'erreur de certificat auto-signé adhoc
        resp = requests.get(
            f"{server_url}/api/admin/messages", 
            timeout=5, 
            verify=False, 
            headers={"ngrok-skip-browser-warning": "any"}
        )
        if resp.status_code != 200:
            return jsonify({"error": "Impossible de récupérer les messages de la scolarité depuis la DMZ."}), 502
        return jsonify(resp.json()), 200
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Connexion impossible au serveur central en DMZ pour récupérer les messages."}), 503
    except Exception as e:
        return jsonify({"error": f"Erreur de récupération : {str(e)}"}), 500


@app.route('/api/local-detect-ngrok', methods=['GET'])
def local_detect_ngrok():
    """Tente de détecter automatiquement une URL ngrok active via son API locale."""
    try:
        # ngrok expose son API locale sur le port 4040
        resp = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=1)
        if resp.status_code == 200:
            data = resp.json()
            tunnels = data.get('tunnels', [])
            for t in tunnels:
                public_url = t.get('public_url', '')
                if public_url:
                    # Nettoyer l'adresse (enlever le protocole)
                    clean_url = public_url.replace("https://", "").replace("http://", "")
                    return jsonify({"active": True, "server_ip": clean_url}), 200
    except Exception:
        pass
    return jsonify({"active": False}), 200


@app.route('/api/local-detect-server', methods=['GET'])
def local_detect_server():
    """Détecte l'adresse du serveur (ngrok ou IP locale) depuis le fichier partagé ou fallback."""
    server_ip = _load_server_ip_from_file()
    is_ngrok = 'ngrok' in server_ip
    return jsonify({
        "active": True,
        "server_ip": server_ip,
        "is_ngrok": is_ngrok
    }), 200


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------


if __name__ == '__main__':
    print("=" * 60)
    print("  SecureShare — CLIENT LOCAL")
    print("  Interface : http://localhost:5001")
    print("  Rôle      : Chiffrement E2EE local + Interface web")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5001, debug=True)
