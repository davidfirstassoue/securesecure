from flask import Flask, jsonify
import sys
import os

app = Flask(__name__)

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(base_dir)
from shared.crypto_utils import compute_fingerprint

# Faux Serveur (Serveur d'Eve)
# Il intercepte les demandes et retourne SA PROPRE clé publique au lieu de la clé de Bob, 
# ce qui permet une attaque Man In The Middle (MITM).

@app.route('/')
def index():
    return "<h1> Serveur d'Eve (Rogue Server) </h1><p>Je suis prêt à intercepter les clés sur /publickey/&lt;user&gt; !</p>"

@app.route('/publickey/<user>')
def get_publickey(user):
    print(f"[ATTENTION] Demande interceptée pour la clé de {user} ! Renvoi de la clé d'EVE (Attaquant).")
    
    user = user.lower()
    
    # Au lieu de charger la clé de l'utilisateur, Eve charge SA propre clé !
    pub_key_path = os.path.join(base_dir, 'shared', 'keys', 'eve_public.pem')
    
    # Si la clé de Eve n'existe pas, il faut la générer avec generate_keys.py
    if not os.path.exists(pub_key_path):
        return jsonify({"error": "Clé d'Eve introuvable. Avez-vous lancé generate_keys avec 'eve' ?"}), 404
        
    with open(pub_key_path, 'rb') as f:
        eve_pub_pem = f.read()
        
    # Retourne malicieusement son identifiant sous le nom demandé...
    return jsonify({
        "username": user, 
        "public_key_pem": eve_pub_pem.decode('utf-8'),
        "fingerprint": compute_fingerprint(eve_pub_pem)
    })

if __name__ == '__main__':
    print("-----------------------------------------------------")
    print("⚠️  DÉMARRAGE DU SERVEUR ROGUE (EVE) SUR LE PORT 5001 ⚠️")
    print("Ce serveur simule une attaque Man-In-The-Middle.")
    print("-----------------------------------------------------")
    app.run(debug=True, port=5001)
