# 📘 Mode d'Emploi : Déploiement et Configuration de SecureShare via le Tunnel VPN Kerio (Site-à-Site)

Ce document fournit les instructions de déploiement et de configuration de l'application de messagerie sécurisée **SecureShare** basées sur l'architecture réseau exacte du projet (tunnel VPN Kerio entre le site de **Charbonnage** et le site de **Damas**).

---

## 📐 1. Architecture Réseau et Cartographie des Composants

L'architecture s'appuie sur deux sites distincts reliés par un **Tunnel VPN Site à Site** configuré directement entre le **Firewall de Charbonnage** et le **Firewall de Damas**.

```mermaid
graph TD
    subgraph SITE DAMAS (Clients - Utilisateurs)
        PC_Gregg[PC Gregg<br>Script: client/app.py]
        PC_David[PC David<br>Script: client/app.py]
        PC_Delvan[PC Delvan<br>Script: client/app.py]
        
        PA[Point d'Accès P.A]
        SW_Damas[Switch SW-Damas]
        FW_Damas[Firewall Damas<br>LAN: 10.1.1.1]
        Routeur_Damas[Routeur Damas]

        PC_Gregg --> PA
        PC_David --> PA
        PC_Delvan --> PA
        PA --> SW_Damas
        SW_Damas --> FW_Damas
        FW_Damas --> Routeur_Damas
    end

    FW_Damas <== Tunnel VPN Site à Site (Kerio SSL) ==> FW_Charb

    subgraph SITE CHARBONNAGE (Serveur Central & Infrastructure)
        Routeur_GT[Routeur GT]
        FW_Charb[Firewall Charbonnage<br>LAN: 10.2.1.1<br>WAN: 192.168.0.250 / DDNS]
        SW_Core[Switch SW-CORE]
        Serveur_AD[Tour SERVEUR AD<br>IP: 10.2.1.17<br>Script: server/main.py<br>Port: 5000 HTTPS]
        PC_Supervision[PC Supervision]

        Routeur_GT --- FW_Charb
        FW_Charb --> SW_Core
        SW_Core --> Serveur_AD
        SW_Core --> PC_Supervision
    end
```

### Récapitulatif des équipements et scripts associés :

| Équipement (selon schéma) | Localisation | Adresse IP | Rôle & Script à exécuter | Port |
| :--- | :--- | :--- | :--- | :--- |
| **Tour SERVEUR AD** | Site Charbonnage | `10.2.1.17` | **Serveur Central** (`server/main.py`) | `5000` (HTTPS) |
| **PC Portable David** | Site Damas | IP Wi-Fi/LAN Damas | **Client Web local** (`client/app.py`) | `5001` (HTTP local) |
| **PC Portable Delvan** | Site Damas | IP Wi-Fi/LAN Damas | **Client Web local** (`client/app.py`) | `5001` (HTTP local) |
| **PC Portable Gregg** | Site Damas | IP Wi-Fi/LAN Damas | **Client Web local** (`client/app.py`) | `5001` (HTTP local) |
| **Firewall Charbonnage** | Site Charbonnage | LAN: `10.2.1.1` \| WAN: `192.168.0.250` | Serveur VPN Kerio (`imsa1.ddns.net`) | Auto (SSL) |
| **Firewall Damas** | Site Damas | LAN: `10.1.1.1` | Client VPN Kerio Site-à-Site | Auto (SSL) |

---

## 🛠️ 2. Prérequis Systèmes et Dépendances (À exécuter sur CHAQUE PC)

Chaque machine (Tour **SERVEUR AD** et PC portables **Gregg / David / Delvan**) doit disposer de **Python 3.10+**.

### Procédure d'installation des dépendances :
1. Copier le dossier du projet `Projet_securshare` sur la machine.
2. Ouvrir une invite de commandes (`cmd` ou `PowerShell`) dans le dossier du projet.
3. Exécuter la commande :
   ```bash
   pip install -r requirements.txt
   ```
   *(Ou manuellement : `pip install flask cryptography requests pyOpenSSL`)*

---

## 🚀 3. Procédure Pas-à-Pas de Lancement de SecureShare

### ÉTAPE A : Test préliminaire du tunnel VPN
Depuis un PC du site **Damas** (ex: le portable de David ou Delvan), ouvrez un terminal et testez la joignabilité de la tour SERVEUR AD :
```bash
ping 10.2.1.17
```
* **Succès :** Le tunnel VPN Kerio reliant le Firewall de Damas au Firewall de Charbonnage est actif.
* **Échec :** Vérifiez l'état de la connexion VPN entre les deux pare-feux.

---

### ÉTAPE B : Lancement sur le SERVEUR (Tour SERVEUR AD à Charbonnage)

1. **Autoriser le port 5000 dans le pare-feu du serveur :**
   Sur la tour **SERVEUR AD** (`10.2.1.17`), ouvrez **PowerShell en administrateur** et lancez :
   ```powershell
   New-NetFirewallRule -DisplayName "SecureShare Server HTTPS" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
   ```

2. **Lancer le serveur Flask :**
   Dans le terminal à la racine du projet sur la tour **SERVEUR AD**, exécutez :
   ```bash
   python server/main.py
   ```
   *(Le serveur démarre et écoute sur `https://0.0.0.0:5000`)*.

---

### ÉTAPE C : Lancement sur les CLIENTS (PC Portables Gregg, David, Delvan à Damas)

Sur **chaque PC portable client** (ex: le PC de David ou Delvan) :

1. **Lancer le script client local :**
   Dans un terminal sur le portable, exécutez :
   ```bash
   python client/app.py
   ```
   *(Le client local démarre en arrière-plan sur le port `5001`)*.

2. **Accéder à l'interface web :**
   Ouvrez le navigateur web du PC portable et accédez à :
   ```text
   http://localhost:5001
   ```

3. **Se connecter au serveur central via le tunnel VPN :**
   Dans le panneau de configuration de l'interface web :
   * Choisissez le profil utilisateur (ex: David, Delvan, etc.).
   * Dans le champ **IP du Serveur Central**, entrez l'IP de la tour **SERVEUR AD** :
     ```text
     10.2.1.17
     ```
   * Cliquez sur **Connexion / Enregistrer**.

---

## 🔒 4. Modèle de Sécurité en Couches (Défense en Profondeur)

La communication entre les PC de Damas (David/Delvan/Gregg) et le SERVEUR AD de Charbonnage est protégée à 3 niveaux :

```text
[PC Client (David / Delvan / Gregg à Damas)]
       │
       ▼  (1. Couche Applicative : E2EE SecureShare - Chiffrement AES-256-CBC + Signatures RSA-2048)
[Payload Chiffré]
       │
       ▼  (2. Couche Transport : HTTPS / TLS v1.3 sur Port 5000)
[Requête HTTPS Chiffrée]
       │
       ▼  (3. Couche Réseau : Tunnel VPN Site à Site Kerio SSL entre Firewalls)
[Encapsulation VPN Chiffrée traversant Internet]
       │
       ▼
[Tour SERVEUR AD (Charbonnage)]
```

---

## 📋 5. Guide de Résolution des Erreurs (Troubleshooting)

| Erreur / Symptôme | Cause Probable | Solution |
| :--- | :--- | :--- |
| **`ConnectionRefusedError` ou Timeout** | Le port 5000 est bloqué ou le serveur n'est pas démarré. | 1. Vérifiez que `python server/main.py` est actif sur la tour SERVEUR AD.<br>2. Exécutez la commande PowerShell `New-NetFirewallRule` sur le SERVEUR AD. |
| **Impossible de pinger `10.2.1.17` depuis Damas** | Le tunnel VPN Kerio entre les deux pare-feux est coupé. | Vérifiez les voyants d'état du tunnel VPN sur l'interface du Firewall de Damas et du Firewall de Charbonnage. |
| **Avertissement SSL dans les logs Python (`InsecureRequestWarning`)** | Certificat SSL auto-généré Flask (`ssl_context='adhoc'`). | Comportement normal en environnement de développement. Avertissement géré automatiquement par le client. |
