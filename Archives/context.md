# SecureShare — Contexte du Projet

Ce fichier sert de mémoire et de fil conducteur pour le développement de l'application **SecureShare**. Il doit être lu au début de chaque session de travail pour s'assurer du respect des objectifs académiques et techniques.

---

## 📋 Présentation Générale
* **Cours** : Sécurité des Réseaux Informatiques
* **Objectif** : Créer une application pratique et fonctionnelle de partage de fichiers sécurisée, avec une démonstration d'attaque de l'Homme du Milieu (MITM) en direct.
* **Échéance** : Moins d'une semaine (~6 jours).
* **Contrainte clé** : Pas de simple PowerPoint. Le prof veut du concret. Chaque membre du groupe (4 personnes) doit implémenter et maîtriser un pilier de la cryptographie pour pouvoir le défendre individuellement en soutenance.

---

## 👥 Répartition des Rôles (Piliers Cryptographiques)

| Membre | Rôle / Pilier | Mécanismes implémentés | Démo / Explication devant le prof |
| :--- | :--- | :--- | :--- |
| **Membre 1** | **Authentification & Gestion des clés** | Génération de clés RSA/ECC, serveur d'annuaire de clés publiques, calcul et affichage de l'empreinte (fingerprint). | Pourquoi le chiffrement asymétrique ? Rôle de la clé publique vs privée. Pourquoi la clé privée reste côté client. |
| **Membre 2** | **Confidentialité** | Chiffrement et déchiffrement symétrique AES-256-CBC des fichiers avec génération d'IV et clé aléatoire. | Pourquoi AES pour les gros fichiers (performances) vs RSA. Notion de chiffrement symétrique. |
| **Membre 3** | **Intégrité & Signature** | Calcul de hash SHA-256 et signature numérique (RSA-PSS). Vérification de signature côté récepteur. | Comment prouver qu'un fichier n'a pas été modifié. Pourquoi confidentialité ≠ intégrité. Bouton debug de modification forcée. |
| **Membre 4 (L'Utilisateur)** | **Échange de clés & Sécurité réseau** | Chiffrement RSA-OAEP de la clé AES, intégration du flux client complet, et développement du script d'attaque MITM. | Rôle du chiffrement hybride. Comment fonctionne l'attaque MITM (spoofing d'annuaire) et comment la parer grâce à l'empreinte. |


## 🛠️ Stack Technique
* **Langage** : Python 3.10+ (Framework Flask pour le serveur et les clients locaux).
* **Librairie de Cryptographie** : `cryptography` (pyca).
* **Frontend** : HTML5 / CSS3 (Vanilla avec style Cyber-Dark / Glassmorphism premium) / JavaScript (Vanilla Fetch).
* **Environnement** : HTTP local (ports distincts pour la simulation de réseaux séparés).

---

## 🚨 Scénario de la Démonstration Live
1. **Flux normal** : Alice envoie un fichier à Bob. Bob le déchiffre et l'application valide l'intégrité (vert ✅).
2. **Altération en transit** : Bob clique sur "altérer le fichier" (simulant une modification sur le réseau), l'application rejette le fichier (rouge ❌ - signature invalide).
3. **Attaque MITM réussie** : Alice bascule sur le serveur d'Eve (l'attaquant). Eve intercepte le fichier, le déchiffre en clair sur son dashboard de hacker, et le transmet modifié à Bob.
4. **Attaque MITM bloquée** : Alice compare l'empreinte de clé affichée sur son écran avec celle fournie par Bob via un canal sécurisé. L'incohérence est détectée, Alice refuse l'envoi.

---

## 📌 État d'avancement
* [ ] Initialisation du projet et création du fichier de tâches `task.md`.
* [ ] Création du module de cryptographie commun `shared/crypto_utils.py`.
* [ ] Développement du serveur central Flask.
* [ ] Développement des clients Alice et Bob (logique + UI Cyber-Dark).
* [ ] Développement de l'attaquant Eve.
* [ ] Intégration globale et tests de démonstration.
