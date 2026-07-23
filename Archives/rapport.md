# 📡 Briefing Équipe — Architecture de l'App & Simulation DMZ (ngrok)

 

Comme convenu, voici le rapport sur ma partie (le **développement de l'application** et la **mise en place de la DMZ via ngrok**). L'objectif est de vous présenter comment le code est structuré, comment déployer les différents fichiers sur nos machines de test, et comment la DMZ est simulée avec ngrok pour que vous puissiez facilement fusionner vos parties (**tunnel VPN ** et **Attaque de Gregg**).

---

## 👥 1. Rappel des Rôles du Scénario

*   **Mme DIBA** (ex-Alice) : La Comptable du Campus (émettrice des fichiers confidentiels).
*   **M. Akendengue** (ex-Bob) : Le Directeur de l'Université (destinataire et vérificateur d'intégrité).
*   **Gregg** (ex-Eve) : L'Étudiant Pirate (qui va tenter l'écoute passive ou l'attaque MITM active).

---

## 🏗️ 2. Architecture du Code & Déploiement

Le code est structuré de manière propre pour séparer les rôles et faciliter la répartition sur les machines physiques du lab ou des VM :

```text
secureshare/
  ├── client/             # Interface et logique de Mme DIBA / M. Akendengue
  │    ├── app.py         # Client Flask local (Port 5001)
  │    ├── templates/     # Pages HTML (dashboard et scolarité)
  │    └── static/        # Fichiers CSS (Cyber-Dark) et JS (main.js, scolarite.js)
  ├── server/             # Serveur central universitaire (DMZ)
  │    ├── main.py        # API Flask centrale (Port 5000) et SQLite
  │    └── database.db    # Base de données de messagerie et de scolarité
  ├── shared/             # Code commun et annuaire de clés
  │    ├── crypto_utils.py# Logique de chiffrement (AES, RSA-OAEP, RSA-PSS)
  │    ├── generate_keys.py # Script de génération des paires de clés RSA
  │    └── keys/          # Dossier de stockage des clés publiques/privées
  └── attacker/           # Partie de Gregg
       └── eve_rogue_server.py # Faux annuaire pirate (Port 5002)
```

### 🚀 Guide de déploiement (Qui prend quoi ?)

Pour faire tourner la maquette, il faut répartir les dossiers de cette façon :

1.  **Sur le Serveur central de l'Université (la DMZ)** :
    *   Fichiers requis : Dossiers `server/` et `shared/`.
    *   Lancement : Exécuter `py server/main.py`. Le serveur tourne sur le port `5000` en HTTPS.
2.  **Sur les postes clients (Mme DIBA et M. Akendengue)** :
    *   Fichiers requis : Dossiers `client/` et `shared/`.
    *   Lancement : Exécuter `py client/app.py`. L'interface s'ouvre sur `http://localhost:5001`.
3.  **Sur le poste de l'attaquant (Gregg)** :
    *   Fichiers requis : Dossier `attacker/`.
    *   Lancement : Exécuter `py attacker/eve_rogue_server.py`. Le serveur d'attaque tourne sur le port `5002`.

---

## 🛜 3. Notre Simulation de DMZ avec ngrok

Pour répondre à l'exigence d'une **DMZ (Zone Démilitarisée)** sans avoir à configurer de vrais pare-feu physiques complexes pendant notre TP, j'ai mis en place une infrastructure hybride utilisant **ngrok**. 

### Comment ça marche ?
1.  **Exposition Publique** : Le serveur central Flask (`server/main.py`) tourne localement sur le port `5000`. On lance un tunnel ngrok pour exposer ce port sur Internet (ex: `https://abcd-123.ngrok-free.app`).
2.  **Simulation DMZ** :
    *   L'adresse publique ngrok joue le rôle de notre **IP publique de DMZ**. Elle est accessible par n'importe quel client depuis l'extérieur (Internet).
    *   Toutefois, le serveur Flask en lui-même n'a aucun droit d'accès initié vers les machines locales des clients (Mme DIBA et M. Akendengue). C'est le principe du cloisonnement de la DMZ : **le trafic va des clients vers le serveur exposé, mais jamais le serveur exposé ne peut initier de connexion vers le réseau privé interne**.
3.  **Liaison Automatique** : Lors de son démarrage, le serveur interroge l'API locale de ngrok. S'il détecte un tunnel actif, il écrit automatiquement l'URL publique dans le fichier `shared/server_info.json`. Quand le client se lance, il lit ce fichier et se connecte automatiquement à l'adresse de la DMZ (ngrok) sans saisie manuelle.

---

## 🔌 4. Points d'intégration pour vos parties

Voici comment brancher vos travaux sur l'application existante :

*   **Pour le tunnel VPN** :
    *   L'application est conçue pour envoyer des requêtes HTTP/HTTPS à l'adresse définie dans le fichier `shared/server_info.json` ou saisie sur le dashboard.
    *   Pour intégrer votre VPN (WireGuard), vous devez configurer le tunnel réseau au niveau de l'OS de manière à ce que tout le trafic destiné à l'IP du serveur (ou à la passerelle ngrok) passe de manière transparente par votre interface VPN virtuelle.
*   **Pour Gregg (l'Attaquant)** :
    *   Votre script `attacker/eve_rogue_server.py` simule le détournement de l'annuaire de clés.
    *   Pour que la démo d'attaque fonctionne, l'utilisateur (Mme DIBA) doit simplement changer le port du serveur dans l'interface (passer du port `5000` légitime au port `5002` de Gregg), simulant ainsi une attaque par empoisonnement DNS ou ARP sur le réseau local.
