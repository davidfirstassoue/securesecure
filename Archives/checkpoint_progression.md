# SecureShare — Sauvegarde de Progression (11 juillet 2026)

Ce document sert de point de sauvegarde de notre conversation et valide les choix de conception réseau et cryptographiques pour le projet.

---

## 👥 Rôles et Terminologie Réseau (Université)
Pour coller aux exigences académiques et rendre la présentation réaliste devant le professeur, nous avons remplacé la terminologie classique Alice/Bob/Eve par les rôles d'une université :
* **La Comptable du Campus** (ex-Alice) : Émettrice des fichiers administratifs et financiers confidentiels.
* **La Directrice de l'Université** (ex-Bob) : Destinataire des fichiers et garante de leur intégrité.
* **L'Étudiant Pirate** (ex-Eve) : L'attaquant sur le réseau (écoute passive avec Wireshark, altération de paquets, ou usurpation par Homme du Milieu).
* **Le Serveur central de l'Université** (Windows Server 2019 du lab : `192.168.168.23`).

---

## 🛜 Architecture à 3 Scénarios Intégrés
Les trois scénarios demandés par le professeur seront intégrés au sein de la **même et unique application** via un interrupteur de mode ("VPN / DMZ / Direct") dans l'interface web :

### 1. Mode VPN Local (LAN chiffré)
* **Objectif** : Masquer le trafic et les métadonnées (qui envoie à qui) sur le réseau local de l'université.
* **Fonctionnement** : Un tunnel proxy en Python (`vpn_client.py` ➔ `vpn_server.py` sur le port `9000`) chiffre la connexion en AES-256 symétrique avec clé pré-partagée.
* **Visualisation** : Wireshark ne montre aucun trafic HTTP en clair, uniquement des octets chiffrés sur le port `9000`.

### 2. Mode DMZ (Cloisonnement Serveur)
* **Objectif** : Sécuriser l'accès à un serveur public depuis l'extérieur tout en protégeant les réseaux internes.
* **Fonctionnement** : Le Windows Server 2019 (`192.168.168.23`) est isolé dans une DMZ sur le routeur (`10.1.1.1`). Le pare-feu bloque toute connexion initiée depuis la DMZ vers le LAN interne.
* **Sécurité** : Chiffrement HTTPS/TLS au niveau transport.

### 3. Mode Direct Internet (P2P de bout en bout)
* **Objectif** : Communication directe et confidentielle de PC à PC sans dépendance envers un serveur intermédiaire.
* **Sécurité** : Chiffrement de bout en bout autonome (AES-256 pour les fichiers, clé AES cryptée en RSA-OAEP avec la clé publique de la Directrice, signature RSA-PSS). La sécurité repose uniquement sur la cryptographie, même si le réseau est hostile.

---

## 🛠️ Prochaines étapes de développement
Dès la reprise, nous pourrons dérouler les tâches suivantes :
1. Créer le fichier de tâches `task.md`.
2. Créer le module cryptographique commun `shared/crypto_utils.py`.
3. Développer le serveur central Flask (`server/main.py`).
4. Développer le client web interactif (`client/app.py` + interface HTML/CSS Cyber-Dark).
5. Développer les scripts de proxy VPN (`vpn/vpn_client.py` et `vpn/vpn_server.py`).
