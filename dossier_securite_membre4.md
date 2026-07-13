# Dossier de Sécurité Individuel — Membre 4 : Échange de Clés & Sécurité Réseau

Ce document constitue ton support de soutenance personnel et répond aux questions de la roadmap du professeur pour ta partie : **l'échange de clés, la sécurité réseau (VPN) et la simulation d'attaque MITM**.

---

## 🔍 1. Identification du Besoin Explicite (Pourquoi ma brique existe ?)

### A. Le problème de l'échange de clés (Confidentialité du secret)
* **Le problème** : La Comptable et la Directrice utilisent le chiffrement symétrique AES-256 pour chiffrer les fichiers. C'est rapide et efficace, mais cela nécessite que les deux possèdent la **même clé AES**. Si la Comptable envoie cette clé en clair sur le réseau, l'Étudiant Pirate l'intercepte et peut déchiffrer tous les fichiers.
* **Le besoin** : Transmettre de manière ultra-sécurisée cette clé AES de session à la Directrice, sans que personne d'autre ne puisse la lire en route.
* **Ma solution** : Le chiffrement asymétrique **RSA-OAEP**. La Comptable chiffre la clé AES avec la clé publique (le cadenas) de la Directrice. Seule la Directrice (avec sa clé privée) pourra la déchiffrer.

### B. Le problème de l'exposition du trafic (Sécurité Réseau)
* **Le problème** : Même si le fichier et la clé sont chiffrés, les paquets HTTP envoyés au serveur contiennent des en-têtes en clair (les adresses IP de la Comptable et de la Directrice, les ports, et le fait qu'elles communiquent). L'Étudiant Pirate peut analyser ce trafic (analyse de métadonnées) pour cartographier le réseau de l'université.
* **Le besoin** : Créer un canal de transport étanche (un tunnel) qui masque l'intégralité du trafic (en-têtes HTTP inclus) entre le client et le serveur.
* **Ma solution** : Le **Tunnel VPN par proxy** en Python.

---

## 📚 2. Étude de l'Existant (Qu'est-ce qui se fait dans l'industrie ?)

Pour résoudre ces problèmes, l'état de l'art utilise :
* **Pour l'échange de clés** : Le protocole **Diffie-Hellman** ou le chiffrement d'enveloppe **RSA-OAEP** (utilisé dans les emails sécurisés PGP ou les premières phases de connexion TLS).
* **Pour le transport sécurisé** : 
  * **TLS (HTTPS)** : Chiffre le flux HTTP pour protéger les requêtes web.
  * **VPN IPSec / WireGuard** : Crée un tunnel au niveau de la couche réseau (couche 3 IP) pour encapsuler et chiffrer l'ensemble du trafic d'une machine ou d'un site.

---

## 🛡️ 3. Proposition de la Politique de Sécurité (Mes règles)

Dans notre application, ma politique de sécurité impose :
1. **Règle d'échange** : Interdiction d'envoyer une clé AES en clair ou de la stocker sur le serveur. Elle doit obligatoirement être chiffrée en **RSA-OAEP (2048 bits)** avec la clé publique du destinataire.
2. **Règle de transport** : Tout trafic vers le serveur de messagerie doit obligatoirement transiter via le proxy VPN local (`vpn_client.py` ➔ `vpn_server.py`) pour être encapsulé et chiffré en AES-256 symétrique.
3. **Règle d'authentification** : Avant d'envoyer un fichier chiffré, le client doit vérifier l'empreinte (fingerprint) de la clé publique de la Directrice pour interdire toute usurpation par l'Étudiant Pirate.

---

## 🛠️ 4. Implémentation de la Politique & Tests par Étapes

Mon implémentation se découpe en 3 briques codées en Python :

### Étape 1 : Le Chiffrement de la Clé (shared/crypto_utils.py)
* **Code** : Utilisation de la librairie `cryptography` pour chiffrer la clé AES.
* **Comment tester cette étape** :
  ```python
  # Test unitaire simple en local :
  cle_aes = os.urandom(32)
  cle_aes_chiffree = encrypt_aes_key(cle_aes, cle_publique_directrice)
  cle_aes_dechiffree = decrypt_aes_key(cle_aes_chiffree, cle_privee_directrice)
  assert cle_aes == cle_aes_dechiffree  # Doit être vrai !
  ```

### Étape 2 : Le Tunnel VPN Proxy (vpn/vpn_client.py et vpn_server.py)
* **Code** :
  * Le client VPN écoute sur `localhost:8001`. Il intercepte la requête HTTP de la Comptable, la chiffre en AES-256 et l'envoie sur le port `9000` du serveur.
  * Le serveur VPN écoute sur le port `9000` du Windows Server, déchiffre le flux et le renvoie au serveur Flask sur le port `5000`.
* **Comment tester cette étape** :
  1. Lancer le serveur Flask sur le port `5000` et le serveur VPN sur le port `9000`.
  2. Lancer le client VPN sur le port `8001`.
  3. Faire une requête HTTP classique (ex: avec `curl` ou `requests`) sur `http://localhost:8001/` et vérifier qu'elle arrive bien déchiffrée sur le serveur Flask.

### Étape 3 : Le Script d'Attaque (attacker/eve_rogue_server.py)
* **Code** : Un serveur Flask pirate qui tourne sur le port `5002` et simule un faux annuaire de clés publiques. Il renvoie la clé publique de l'Étudiant Pirate à la place de celle de la Directrice.
* **Comment tester cette étape** :
  1. Configurer la Comptable pour interroger l'annuaire pirate.
  2. Envoyer un fichier.
  3. Vérifier que l'Étudiant Pirate parvient à intercepter l'enveloppe, à déchiffrer la clé AES avec sa propre clé privée, et à lire le fichier en clair.

---

## 🧪 5. Test de Sécurité (Ma démonstration devant le prof)

Pour prouver l'efficacité de mon travail, je présente deux démonstrations :

### Démo A : L'Attaque MITM et l'Empreinte de Clé
1. **Sans protection** : L'Étudiant Pirate détourne les requêtes d'annuaire. La Comptable lui envoie le fichier chiffré avec sa mauvaise clé. L'Étudiant Pirate affiche le fichier financier secret de l'université en clair sur son écran.
2. **Avec protection** : La Comptable compare l'empreinte de clé affichée sur son écran (`A1B2-C3D4...`) avec celle fournie par la Directrice via un canal hors-ligne (ex: par SMS ou écrit sur un tableau). Les empreintes ne correspondent pas. La Comptable clique sur "Annuler". L'attaque est bloquée.

### Démo B : Le VPN face à l'écoute réseau
1. **VPN Désactivé** : La Comptable envoie le document directement au serveur. Sur l'écran de l'Étudiant Pirate, Wireshark affiche la requête HTTP en clair contenant le JSON complet de l'enveloppe.
2. **VPN Activé** : La Comptable active son VPN. Sur Wireshark, l'Étudiant Pirate ne voit plus aucune requête HTTP vers le port `5000`. Il ne voit passer que des paquets chiffrés et incompréhensibles sur le port `9000`. Le tunnel réseau est validé.
