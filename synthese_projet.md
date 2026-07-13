# SecureShare — Synthèse du Projet, Technologies et Architecture VPN

Ce document rassemble toutes les explications clés, analogies et choix techniques de notre projet **SecureShare** pour servir de guide à toute l'équipe et de support pour les livrables / présentations devant le professeur.

---

## 👥 1. Répartition des Rôles & 4 Barrières Cryptographiques

| Membre | Rôle / Pilier | Technologies & Algorithmes | Rôle dans la démo live |
| :--- | :--- | :--- | :--- |
| **Membre 1** | **Authentification & Gestion des clés** | - **RSA 2048 bits** (Génération des paires)<br>- **SHA-256** (Calcul d'empreinte)<br>- **Flask** (Serveur d'annuaire de clés) | Affiche son empreinte de clé publique à l'écran. Explique pourquoi les clés privées ne quittent jamais le client. |
| **Membre 2** | **Confidentialité** | - **AES-256-CBC** (Chiffrement du fichier)<br>- `os.urandom(16)` (Génération d'IV aléatoire)<br>- **PKCS7** (Padding / Remplissage) | Montre le fichier chiffré illisible. Explique pourquoi AES est choisi pour la rapidité sur les gros fichiers. |
| **Membre 3** | **Intégrité & Signature** | - **SHA-256** (Hachage du fichier)<br>- **RSA-PSS** (Signature numérique)<br>- Mode debug (Altération forcée de fichier) | Montre la détection d'une modification de fichier (Alerte rouge ❌). Explique que confidentialité ≠ intégrité. |
| **Membre 4 (Toi)** | **Échange de clés & Sécurité Réseau** | - **RSA-OAEP** (Chiffrement de la clé AES)<br>- Communication **HTTP / JSON** (lib `requests`) | Orchestre le flux Alice/Bob. Gère l'envoi de l'enveloppe chiffrée. Présente l'attaque MITM d'Eve. |

---

## 🔒 2. Le Chiffrement Hybride (L'analogie des Cadenas)

Pour expliquer le fonctionnement des clés et du chiffrement hybride de manière simple :

1. **Les cadenas de Bob** : Bob fabrique un cadenas unique et sa clé. Il distribue des copies de son **cadenas ouvert** (Clé Publique RSA) sur le serveur. Il garde la seule **clé en métal** (Clé Privée RSA) dans sa poche.
2. **Le Coffre (Fichier)** : Alice met son gros fichier dans un coffre en bois et le verrouille avec un cadenas à code généré au hasard (Clé AES-256). C'est rapide et gère toutes les tailles de fichiers.
3. **L'Enveloppe (Clé AES)** : Pour transmettre le code du cadenas à Bob sans qu'un espion ne le lise, Alice écrit le code sur un papier, le met dans une enveloppe, et la ferme avec le **cadenas ouvert de Bob** (RSA-OAEP).
4. **La Réception** : Bob reçoit le tout, ouvre l'enveloppe avec sa **clé en métal** (Clé Privée), récupère le code, et ouvre le coffre contenant le fichier.

> **Pourquoi ne pas chiffrer directement le fichier avec RSA ?** 
> RSA a une limite physique stricte sur la taille des données qu'il peut chiffrer (quelques octets maximum) et est très lourd en calculs. AES est ultra-rapide et n'a pas de limite de taille.

---

## 🏴‍☠️ 3. Les Attaques d'Eve (L'Homme du Milieu - MITM)

Eve utilise 3 techniques pour tenter de casser le système :

1. **L'Interception Passive** : Elle écoute le trafic réseau. Elle est bloquée par le chiffrement AES (le fichier est illisible).
2. **L'Altération de Données** : Elle modifie un octet du fichier chiffré en route. Elle est bloquée par la signature numérique RSA-PSS (Bob détecte que la signature ne correspond plus).
3. **L'Homme du Milieu Actif (MITM)** : Eve intercepte la demande de clé d'Alice et lui renvoie son propre cadenas. Alice chiffre le code AES pour Eve. Eve le décrypte avec sa clé privée, lit le fichier, le modifie, puis le re-chiffre avec le vrai cadenas de Bob pour masquer son attaque.

### 🛡️ La Parade : L'Empreinte (Fingerprint)
Le cadenas de Bob possède un numéro de série unique (`A1B2-C3D4...`). Alice et Bob comparent ce numéro hors-ligne (par téléphone ou sur leurs écrans). Si le numéro reçu par Alice est celui d'Eve, l'attaque est détectée et l'envoi est bloqué. C'est le même principe que les **Safety Numbers (QR Code de chiffrement)** de WhatsApp.

---

## 🛜 4. L'Architecture du Tunnel VPN en Python

Pour répondre à la demande du professeur d'ajouter un **VPN d'Accès** et **VPN Site-à-Site**, nous simulons un tunnel d'encapsulation chiffré directement dans notre code Python à l'aide de scripts proxies locaux.

```text
[ CLIENT ALICE ] 
       │  (Envoie ses requêtes en clair à son VPN local)
       ▼  
[ VPN_Client.py ]  <─── Écoute sur localhost:8001. Chiffre tout le trafic.
       │
       │  ====== LE TUNNEL CHIFFRÉ (Port 9000) ======
       │  (Si Eve intercepte ici, elle ne voit que des octets indéchiffrables)
       ▼
[ VPN_Server.py ]  <─── Écoute sur le serveur (Port 9000). Déchiffre le trafic.
       │
       │  (Transmet en clair localement au serveur Flask)
       ▼
[ SERVEUR CENTRAL (Flask) ] (Port 5000)
```

### Fonctionnement technique :
* **vpn_client.py** : Reçoit les requêtes HTTP d'Alice sur le port `8001`, chiffre l'en-tête et le corps de la requête, et l'encapsule dans un paquet envoyé au port `9000`.
* **vpn_server.py** : Reçoit les paquets chiffrés sur le port `9000`, les déchiffre, et les transmet en local au serveur Flask sur le port `5000`.
* **Visualisation** :
  * Si le VPN est **Désactivé** : Alice communique directement sur le port `5000`. Le dashboard d'Eve intercepte les requêtes en clair.
  * Si le VPN est **Activé** : Alice communique via le port `8001`. Le trafic passe chiffré par le tunnel (port `9000`). Eve ne voit que du trafic incompréhensible sur le réseau.
