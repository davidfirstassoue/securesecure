# Roadmap de Sécurité — Méthodologie, Architecture et Cahier de Test (SecureShare)

Ce document décrit la méthodologie de sécurité demandée par le professeur dans le cadre du projet **SecureShare** (Cours de Sécurité des Réseaux Informatiques) appliquée à notre scénario universitaire.

---

## 📊 État d'avancement du Projet (Pour le Professeur)

| Phase de la Roadmap | Statut | Ce qui a été fait |
| :--- | :--- | :--- |
| **1. Identification du Besoin** | **✅ Terminé** | Analyse des menaces sur le réseau de l'Université et définition des besoins d'isolation. |
| **2. Étude de l'Existant** | **✅ Terminé** | Analyse des briques TLS/HTTPS, VPN (WireGuard/IPSec) et du modèle Zero Trust. |
| **3. Politique de Sécurité** | **✅ Terminé** | Définition des règles cryptographiques (RSA-2048, AES-256, RSA-PSS) et réseau. |
| **4. Architecture & Conception** | **✅ Terminé** | Figeage du contrat de données JSON, modélisation des 3 scénarios (VPN, DMZ, Direct). |
| **5. Cahier de Recette (Tests)** | **✅ Terminé** | Rédaction des 5 scénarios de test physiques à exécuter en direct sur les machines du lab. |
| **6. Codage & Implémentation** | **⏳ En cours** | Initialisation de la structure des dossiers et préparation du code Python. |

---

## 🔍 1. Identification du Besoin Réseau & Menaces

### A. Le Problème Réseau (Cas de l'Université)
La **Comptable du Campus** doit transmettre un document financier confidentiel à la **Directrice de l'Université** via le serveur central. En l'absence de mesures de sécurité :
* **Interception passive (Confidentialité)** : L'**Étudiant Pirate**, connecté sur le Wi-Fi ou le Switch du lab, peut intercepter et lire le document administratif en clair.
* **Altération active (Intégrité)** : L'Étudiant Pirate peut intercepter le fichier de notes/comptabilité en transit et y injecter de fausses valeurs.
* **Usurpation d'identité (Authenticité - MITM)** : L'Étudiant Pirate peut injecter sa propre clé publique à la place de celle de la Directrice, poussant la Comptable à lui envoyer les fichiers directement (Homme du Milieu).

### B. Le Besoin d'Isolation et de Transport
* **Masquage des en-têtes** : Chiffrer le fichier ne suffit pas, les en-têtes HTTP révèlent qui communique avec qui. Il y a un besoin d'**encapsulation** (tunnel VPN).
* **Isolation du serveur public** : Le serveur central de messagerie, exposé sur le réseau, représente une vulnérabilité. Il doit être cloisonné pour éviter qu'une faille ne contamine tout le réseau interne de l'université.

---

## 📚 2. Étude de l'Existant (L'État de l'Art)

Notre proposition s'appuie sur des standards reconnus :
* **Chiffrement Hybride** : Utilisé par TLS/HTTPS et SSH (RSA pour sécuriser la clé de session, AES pour le chiffrement rapide du flux de données).
* **Sécurité de bout en bout (E2EE)** : Inspiré de Signal/WhatsApp, avec échange d'empreintes de clés (fingerprints) sur un canal séparé pour prévenir les attaques de type Homme du Milieu.
* **Architecture DMZ** : Recommandations de l'ANSSI pour l'hébergement de services exposés (Webmail, Moodle) afin de protéger le LAN de l'organisation.

---

## 🛡️ 3. Proposition de la Politique de Sécurité

La politique de sécurité de **SecureShare** repose sur 5 piliers complémentaires :

1. **Confidentialité des Données (AES-256-CBC)** : Chiffrement symétrique obligatoire de chaque fichier avec vecteur d'initialisation (IV) unique et aléatoire.
2. **Confidentialité de l'Échange (RSA-OAEP 2048)** : La clé AES de session ne transite jamais en clair et est chiffrée par la clé publique RSA de la Directrice.
3. **Intégrité et Authenticité (SHA-256 + RSA-PSS)** : Signature électronique de l'empreinte du fichier par la clé privée de la Comptable, vérifiable par la Directrice.
4. **Validation d'Identité (Fingerprint)** : Comparaison hors-ligne de l'empreinte hexadécimale de la clé publique de la Directrice pour interdire l'attaque MITM.
5. **Sécurité Réseau (VPN local & DMZ)** :
   * Transport sécurisé via un tunnel proxy local chiffrant l'en-tête et le corps des requêtes.
   * Hébergement du serveur de messages dans un sous-réseau DMZ isolé du LAN.

---

## 🛠️ 4. Implémentation & Architecture Technique

L'implémentation est structurée en briques logiques indépendantes :
* **Module Commun** : [shared/crypto_utils.py](file:///c:/Users/david/Downloads/PROJETS%20FIRST/SecureShare/shared/crypto_utils.py) pour toute la logique de chiffrement, déchiffrement et signature.
* **Serveur Central** : Flask API déployé sur le Windows Server 2019 du lab (`192.168.168.23`).
* **Clients Web** : Interfaces locales pour la Comptable et la Directrice permettant de choisir dynamiquement le mode réseau.
* **Proxies VPN** :
  * `vpn_client.py` (écoute sur le port `8001` du PC de la Comptable, chiffre le trafic et l'encapsule).
  * `vpn_server.py` (écoute sur le port `9000` du Windows Server 2019, déchiffre et transmet au serveur Flask sur le port `5000`).

---

## 🧪 5. Cahier de Recette (Scénarios de Test)

Ces tests physiques seront joués en direct devant le professeur sur les machines du lab :

### Scénario 1 : Le Flux Normal (Sans attaque)
* **Action** : La Comptable envoie un fichier comptable à la Directrice.
* **Résultat attendu** : La Directrice reçoit et déchiffre automatiquement le document. L'interface affiche : **"Intégrité validée ✅ - Fichier déchiffré"**.

### Scénario 2 : L'Altération de fichier (Test d'intégrité)
* **Action** : L'Étudiant Pirate modifie un octet du fichier chiffré pendant son transit.
* **Résultat attendu** : Le client de la Directrice détecte que la signature numérique RSA-PSS ne correspond pas au hash calculé. L'interface affiche une alerte rouge : **"ALERTE : Signature ou fichier invalide ❌"**.

### Scénario 3 : L'Attaque de l'Homme du Milieu (Sans vérification)
* **Action** : L'Étudiant Pirate redirige le trafic d'enregistrement de clés de la Comptable vers son propre serveur rogue. Il lui envoie sa clé publique. La Comptable envoie le fichier confidentiel.
* **Résultat attendu** : L'Étudiant Pirate intercepte le message, le déchiffre avec sa clé privée, affiche le budget de l'université en clair sur son écran, puis le re-chiffre avec la vraie clé de la Directrice pour masquer son attaque.

### Scénario 4 : Blocage de l'Attaque MITM (Avec vérification)
* **Action** : La Comptable et la Directrice comparent de vive voix les empreintes de clés affichées sur leurs écrans respectifs.
* **Résultat attendu** : La Comptable constate que l'empreinte reçue du serveur diffère de celle fournie par la Directrice. Elle bloque l'envoi du document. L'attaque échoue.

### Scénario 5 : Protection Réseau (Tunnel VPN)
* **Action** : La Comptable active son VPN et envoie le message. L'Étudiant Pirate lance Wireshark sur le réseau local.
* **Résultat attendu** : Sans VPN, l'Étudiant Pirate voit les paquets HTTP en clair circuler vers le port `5000`. Avec le VPN activé, il ne voit que du trafic chiffré sur le port `9000`. Le tunnel est hermétique.
