# 📡 Guide de Configuration des Tests Réseau — SecureShare

Ce guide résume la configuration à adopter pour tester la messagerie sécurisée **SecureShare** en réseau local (Wi-Fi ou Ethernet) entre plusieurs ordinateurs.

---

## 📦 1. Installation des dépendances (Sur chaque PC)

Avant de lancer les scripts sur vos ordinateurs, assurez-vous d'avoir installé toutes les dépendances requises en ouvrant une invite de commandes (cmd/PowerShell) à la racine du projet et en exécutant :
```bash
py -m pip install -r requirements.txt
```

---

## 🔍 2. Trouver l'adresse IP du PC Serveur

Le PC qui fait tourner le **Serveur Central** (`server/main.py`) est le nœud vers lequel tous les autres vont envoyer leurs requêtes. Vous devez connaître son adresse IP locale.

1. Sur le PC Serveur, ouvrez une invite de commandes (cmd) ou PowerShell.
2. Tapez la commande suivante :
   ```bash
   ipconfig
   ```
3. Repérez la ligne **Adresse IPv4** sous votre carte réseau active (ex: *Carte réseau sans fil Wi-Fi*).
   * *Exemple : `192.168.1.235`*
   * Dans ce guide, nous appellerons cette adresse **`<IP_SERVEUR>`**.

---

## 👥 3. CONFIGURATION A : Test avec 2 ordinateurs
* **PC 1** : Fait tourner le **Serveur Central** ET l'interface d'**Alice**.
* **PC 2** : Fait tourner l'interface de **Bob**.

### Tableau récapitulatif des adresses et rôles

| Poste | Script à lancer | URL dans le navigateur | Identifiant | IP du Serveur à saisir |
| :--- | :--- | :--- | :--- | :--- |
| **PC 1** (Serveur + Alice) | `py server/main.py`<br>`py client/app.py` | `http://localhost:5001` | **alice** (mdp: `alice123`) | `127.0.0.1` *(ou `<IP_SERVEUR>`)* |
| **PC 2** (Bob) | `py client/app.py` | `http://localhost:5001` | **bob** (mdp: `bob123`) | **`<IP_SERVEUR>`** |

### Procédure pas à pas :
1. **Sur le PC 1** :
   * Ouvrez un terminal et lancez le serveur central : `py server/main.py`
   * Ouvrez un autre terminal et lancez le client local : `py client/app.py`
   * Ouvrez `http://localhost:5001` sur le navigateur, connectez-vous en tant qu'**alice** avec l'IP **`127.0.0.1`**.
2. **Sur le PC 2** :
   * Copiez le dossier complet `Projet_securshare` sur cette machine.
   * Lancez le client local : `py client/app.py`
   * Ouvrez `http://localhost:5001` sur le navigateur, connectez-vous en tant qu'**bob** avec l'IP **`<IP_SERVEUR>`** (celle du PC 1).

---

## 👥 4. CONFIGURATION B : Test avec 3 ordinateurs
* **PC 1** : Fait tourner **uniquement** le **Serveur Central**.
* **PC 2** : Fait tourner l'interface d'**Alice**.
* **PC 3** : Fait tourner l'interface de **Bob**.

### Tableau récapitulatif des adresses et rôles

| Poste | Script à lancer | URL dans le navigateur | Identifiant | IP du Serveur à saisir |
| :--- | :--- | :--- | :--- | :--- |
| **PC 1** (Serveur seul) | `py server/main.py` | Aucun | Aucun | Aucun |
| **PC 2** (Alice) | `py client/app.py` | `http://localhost:5001` | **alice** (mdp: `alice123`) | **`<IP_SERVEUR>`** (PC 1) |
| **PC 3** (Bob) | `py client/app.py` | `http://localhost:5001` | **bob** (mdp: `bob123`) | **`<IP_SERVEUR>`** (PC 1) |

### Procédure pas à pas :
1. **Sur le PC 1** :
   * Ouvrez un terminal et lancez uniquement le serveur central : `py server/main.py`.
2. **Sur le PC 2** :
   * Copiez le dossier du projet, lancez `py client/app.py`.
   * Ouvrez le navigateur sur `http://localhost:5001` et connectez-vous en tant qu'**alice** avec l'IP **`<IP_SERVEUR>`** (PC 1).
3. **Sur le PC 3** :
   * Copiez le dossier du projet, lancez `py client/app.py`.
   * Ouvrez le navigateur sur `http://localhost:5001` et connectez-vous en tant qu'**bob** avec l'IP **`<IP_SERVEUR>`** (PC 1).

---

## 🛡️ 5. Résolution des problèmes de connexion (Pare-feu Windows)

Par défaut, le Pare-feu de Windows bloque les connexions réseau entrantes sur les ports personnalisés (comme le port `5000`). Si Alice ou Bob ne parviennent pas à joindre le serveur :

### Option 1 : La méthode rapide (Recommandée pour le TP)
Désactivez temporairement le Pare-feu Windows Defender sur le **PC 1 (Serveur)** :
1. Cherchez **Pare-feu Windows Defender** dans le menu démarrer.
2. Cliquez sur **Activer ou désactiver le pare-feu Windows Defender** (dans le panneau de gauche).
3. Cochez **Désactiver** pour les réseaux privés et publics, puis validez.
*(Réactivez-le après la séance).*

### Option 2 : La méthode propre (Ajouter une règle d'entrée)
Sur le **PC 1**, ouvrez **PowerShell en administrateur** et exécutez la commande suivante pour autoriser le port du serveur :
```powershell
New-NetFirewallRule -DisplayName "SecureShare Server" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

---

## 🛠️ 6. Aide au diagnostic (Journal de Synchronisation)
Si vous rencontrez une erreur, utilisez le volet de diagnostic intégré :
* Sur l'interface web, tout en bas de l'écran, cliquez sur **"Journal de Synchronisation Réseau (Aide technique) ▲"**.
* Les messages détaillés vous montreront l'adresse IP exacte et l'URL que le client tente de contacter.
