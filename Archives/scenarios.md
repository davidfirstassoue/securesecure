# 📋 Récapitulatif des Scénarios de Démonstration — SecureShare

Ce document récapitule l'ensemble des scénarios de test et de démonstration académiques de l'application **SecureShare**, intégrant le réseau local, la DMZ, le VPN Kerio, les attaques MITM et la validation cryptographique.

---

### 🟢 SCÉNARIO 1 : Messagerie Légitime & E2EE en Réseau Local Direct (Sans VPN)
* **Objectif :** Valider le fonctionnement de la messagerie chiffrée de bout en bout (E2EE) et de la signature numérique sur un réseau local direct.
* **Acteurs :** Serveur Central (`server/main.py`), Clients (`client/app.py` sur `:5001`).
* **Déroulement :**
  1. Un utilisateur (ex: Alice ou David) envoie un message ou fichier à un autre (ex: Bob ou Delvan).
  2. Le message est chiffré localement en **AES-256-CBC**, la clé AES est chiffrée avec la **clé publique RSA du destinataire**, et le hash SHA-256 est signé avec la **clé privée RSA de l'émetteur**.
  3. Le serveur central stocke l'enveloppe chiffrée sans pouvoir en lire le contenu.
  4. Le destinataire télécharge l'enveloppe, déchiffre la clé AES avec sa **clé privée RSA**, et valide la signature RSA-PSS.
* **Résultat attendu :** Confidentialité et intégrité confirmées en vert sur le tableau de bord.

---

### 🔵 SCÉNARIO 2 : Interconnexion Sécurisée Inter-Sites via le Tunnel VPN Kerio (Site-à-Site)
* **Objectif :** Démontrer la protection du trafic réseau lors du transfert de données entre deux bâtiments distants (**Site Damas** et **Site Charbonnage**).
* **Acteurs :**
  * **Site Charbonnage :** Tour SERVEUR AD (`10.2.1.17:5000`).
  * **Site Damas :** PC Portables clients (David, Delvan, Gregg sur `:5001`).
  * **Interconnexion :** Tunnel VPN Kerio SSL entre le Firewall de Damas (`10.1.1.1`) et le Firewall de Charbonnage (`192.168.0.250` / `imsa1.ddns.net`).
* **Déroulement :**
  1. Les clients de Damas contactent le SERVEUR AD de Charbonnage en utilisant l'IP privée `10.2.1.17`.
  2. Tout le flux est encapsulé de manière transparente dans le tunnel VPN par les pare-feux Kerio.
  3. Une capture **Wireshark sur la carte WAN/Internet** ne montre que des paquets chiffrés du protocole Kerio VPN.
* **Résultat attendu :** Double niveau de protection (Isolation Réseau Couche 3/4 via VPN + Chiffrement Applicatif Couche 7 via E2EE).

---

### 🟠 SCÉNARIO 3 : Démonstration de la DMZ (Zone Démilitarisée) avec ngrok
* **Objectif :** Démontrer la mise en place d'une DMZ pour exposer publiquement le serveur central tout en protégeant le réseau interne.
* **Acteurs :** Serveur Central (`server/main.py`), Tunnel ngrok, Clients externes.
* **Déroulement :**
  1. Le serveur central tourne sur le port `5000` et initie un tunnel **ngrok** (`https://abcd-123.ngrok-free.app`).
  2. L’adresse publique ngrok joue le rôle de l'**IP publique de la DMZ** accessible depuis n'importe quel réseau externe.
  3. **Politique de cloisonnement DMZ :** Les clients se connectent à l'adresse de DMZ, mais le serveur exposé en DMZ a une interdiction stricte d'initier toute connexion vers le réseau privé interne (LAN).
  4. L'URL publique de la DMZ est écrite dans `shared/server_info.json` pour la résolution automatique côté client.
* **Résultat attendu :** Exposition sécurisée en DMZ conforme aux exigences de sécurité réseau.

---

### 🔴 SCÉNARIO 4 : Attaque MITM & Faux Serveur Annuaire (Attaquant Gregg / Eve)
* **Objectif :** Démontrer la détection d'une attaque par Homme du Milieu (*Man-In-The-Middle*) et le détournement de l'annuaire de clés.
* **Acteurs :** Faux Serveur d'Eve (`attacker/eve_rogue_server.py` sur le port `5002`), Client ciblé.
* **Déroulement :**
  1. L'attaquant Gregg (Eve) lance son faux serveur d'annuaire sur le port `5002`.
  2. On simule un empoisonnement DNS/ARP en redirigeant le client vers le port `5002` au lieu du port `5000` officiel.
  3. Le serveur d'Eve délivre la clé publique d'Eve à la place de la vraie clé publique du destinataire.
* **Contre-mesures & Détection :**
  * **Contrôle d'Empreinte (Fingerprint) :** L'interface affiche l'empreinte SHA-256 de la clé reçue (`B4E7-9F12-...`), permettant la détection immédiate de l'usurpation.
  * **Échec de Signature RSA-PSS :** L'application rejette le message avec l'alerte : `"ALERTE : Signature ou hash invalide !"`.
* **Résultat attendu :** L'attaque est repérée et le message corrompu/intercepté est bloqué.

---

### 🟡 SCÉNARIO 5 : Test d'Altération de Fichier / Donnée Erronée (Non-Répudiation & Intégrité)
* **Objectif :** Prouver l'efficacité du hachage SHA-256 et des signatures RSA-PSS pour détecter la modification accidentelle ou malveillante d'une donnée en transit.
* **Acteurs :** Client Émetteur, Client Récepteur, Fonction d'altération de démo.
* **Déroulement :**
  1. L'émetteur envoie un fichier/message chiffré et signé.
  2. Lors de la réception, on simule une modification de 1 seul bit/octet dans le contenu du message.
  3. Le client récepteur recalcule l'empreinte SHA-256 du contenu déchiffré et la compare avec le hash signé.
  4. L'application détecte que le hash calculé diffère du hash reçu.
* **Résultat attendu :** Affichage de l'alerte d'altération, blocage de l'affichage du fichier altéré et garantie de non-répudiation.
