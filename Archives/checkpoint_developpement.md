# Point de Sauvegarde — Session de Développement SecureShare (14 Juillet 2026)

Ce fichier sert de mémoire pour notre prochaine session de travail. Il résume l'état du projet et les choix de conception réseau validés.

---

## 🚀 Travail accompli aujourd'hui

1. **Restructuration Professionnelle (Client/Serveur)** :
   * Séparation du code en dossiers propres : `server/` (serveur universitaire), `client/` (logique locale + UI) et `attacker/` (serveur pirate d'Eve).
   * Suppression de la simulation VPN Python obsolète.
   * Centralisation des dépendances dans `requirements.txt`.
   * Rangement des anciens documents secondaires dans le dossier `Archives/`.
2. **Serveur Central Sécurisé (`server/main.py`)** :
   * Lancement en **HTTPS (SSL)** via `ssl_context='adhoc'`.
   * Prêt pour le déploiement en **Zone DMZ** (avec règles d'interdiction de connexion initiée de la DMZ vers le LAN).
3. **Client Local (`client/app.py`)** :
   * Intégration complète de la cryptographie de bout en bout (E2EE) lors de l'envoi de messages/fichiers (Chiffrement AES-256-CBC, signature RSA-PSS, chiffrement de clé RSA-OAEP).
   * Prise en charge des communications HTTPS transparentes avec désactivation sécurisée des avertissements de certificats auto-signés de développement (`verify=False`).
   * Orchestration locale prête à alimenter le futur frontend.
4. **Validation de l'Attaquant (`attacker/eve_rogue_server.py`)** :
   * Port configuré sur `5002` pour éviter tout conflit avec le client légitime (port `5001`).
5. **Documentation Réseau Académique (`guide_deploiement_reseau.md`)** :
   * Schéma d'architecture multi-PC complet pour la soutenance.
   * Procédure d'installation système d'un **vrai tunnel VPN Site-à-Site (WireGuard)**.
   * Rôle précis de la DMZ (anti-rebond du pare-feu) et cahier de recette pour la démonstration devant le professeur.

---

## 🔮 Prochaine Session : Refonte complète du Frontend

Dès la reprise, nous nous concentrerons à 100% sur l'interface graphique :
1. **Intégration du template HTML** : Implémenter le fichier `client/templates/dashboard.html` pour intégrer la structure à 3 panneaux (Identité/Configuration réseau, Émetteur/Récepteur, Console Crypto en temps réel).
2. **Style CSS Cyber-Dark Premium** : Mettre en ligne la feuille de style `client/static/css/style.css` (Glassmorphic, effets de flou néon, harmonie de couleurs sombres et accents colorés, micro-animations).
3. **Logique JavaScript (`client/static/js/main.js`)** : Connecter l'UI aux API locales du client Flask pour orchestrer visuellement les opérations cryptographiques et alimenter dynamiquement les logs de la console.
