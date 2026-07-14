"""
server/main.py — Serveur Central de l'Université (SecureShare)
Port : 5000
Rôle : Annuaire de clés publiques + Boîte aux lettres de messages chiffrés.
Ce serveur ne voit jamais le contenu des messages. Il manipule uniquement
des enveloppes JSON opaques chiffrées de bout en bout.
"""

import os
import sys

from flask import Flask, jsonify, request

# Chemin vers le dossier parent pour accéder au module shared
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE_DIR)

from shared.crypto_utils import compute_fingerprint

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Stockage en mémoire — Dans un vrai système : base de données persistante
# ---------------------------------------------------------------------------

# Boîte aux lettres : { "bob": [envelope1, envelope2, ...], ... }
ENVELOPES_INBOX: dict[str, list] = {}


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
    Le serveur ne peut pas lire le contenu — il ne fait que le stocker.
    Format attendu : { "to": "bob", "from": "alice", "encrypted_aes_key": "...", ... }
    """
    envelope = request.get_json(silent=True)

    if not envelope:
        return jsonify({"error": "Corps de la requête JSON invalide ou manquant."}), 400

    recipient = envelope.get("to", "").strip().lower()
    if not recipient:
        return jsonify({"error": "Champ 'to' manquant dans l'enveloppe."}), 400

    if recipient not in ENVELOPES_INBOX:
        ENVELOPES_INBOX[recipient] = []

    ENVELOPES_INBOX[recipient].append(envelope)

    print(f"[SERVEUR] Enveloppe reçue de '{envelope.get('from', '?')}' pour '{recipient}'.")
    return jsonify({"status": "delivered", "recipient": recipient}), 200


@app.route('/receive/<user>', methods=['GET'])
def receive_envelope(user: str):
    """
    Récupère et vide la boîte aux lettres d'un utilisateur.
    Le client déchiffrera le contenu localement avec sa clé privée.
    """
    user = user.strip().lower()
    inbox = ENVELOPES_INBOX.pop(user, [])

    print(f"[SERVEUR] {len(inbox)} enveloppe(s) récupérée(s) pour '{user}'.")
    return jsonify(inbox), 200


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print("=" * 60)
    print("  SecureShare — SERVEUR CENTRAL DE L'UNIVERSITÉ")
    print("  Adresse : https://0.0.0.0:5000 (HTTPS Activé)")
    print("  Rôle    : Annuaire de clés + Boîte aux lettres chiffrée (DMZ)")
    print("=" * 60)
    # Lancement en HTTPS avec génération de certificat à la volée
    app.run(host='0.0.0.0', port=5000, debug=False, ssl_context='adhoc')
