# Maquette Esthétique & Design de SecureShare

Voici la maquette de l'interface utilisateur (UI) que nous allons implémenter. Le design adopte une charte **Cyber-Dark** et du **Glassmorphism (effet verre dépoli)** pour donner un aspect moderne, premium et rassurant face aux enjeux de sécurité.

---

## 🎨 Aperçu Visuel de la Maquette

![Maquette de l'Interface de SecureShare](file:///C:/Users/david/.gemini/antigravity-ide/brain/812211cc-761b-4f3e-92f6-ac54a5d7e675/secureshare_ui_mockup_1783957342121.png)

---

## 📐 Description des Composants de l'Interface

L'interface est structurée en 3 zones majeures pour que l'étudiant (et le professeur) comprenne instantanément ce qui se passe :

### 1. Le Panneau de Gauche : Identité & Configuration Réseau
* **Sélecteur de Rôle** : Permet de choisir entre **"Comptable du Campus"** et **"Directrice de l'Université"**. Le changement de rôle adapte dynamiquement les actions disponibles.
* **Empreinte Publique (Fingerprint)** : Affiche l'empreinte de la clé publique de la machine sous la forme `XXXX-XXXX-XXXX-XXXX` dans une police monospace rétro-éclairée en bleu. C'est l'empreinte qu'Alice et Bob comparent de vive voix.
* **Configuration Réseau (Le sélecteur de mode)** : 
  * Trois gros boutons (chips) rétro-éclairés pour choisir le mode : **Direct (P2P)**, **DMZ (Serveur Public)**, ou **VPN Local**.
  * Un champ de saisie pour renseigner l'adresse IP du serveur de l'université (par défaut `192.168.168.23`).

### 2. Le Panneau de Droite : Tableau d'Actions
* **Pour la Comptable** :
  * Une zone de **Drag & Drop (Glisser-Déposer)** avec une bordure en pointillés luminescents pour choisir le fichier comptable/RH à envoyer.
  * Un bouton **"Altérer le fichier"** (bouton de debug/démo) qui permet d'insérer volontairement une erreur de 1 octet dans le fichier chiffré.
  * Un gros bouton d'action **"Chiffrer et Envoyer"** avec un effet de gradient progressif au survol.
* **Pour la Directrice** :
  * La liste des fichiers reçus sous forme de cartes.
  * Un bouton **"Déchiffrer"**.
  * Un bandeau d'alerte dynamique : **Vert Lumineux ("Intégrité Validée ✅ - Document Authentique")** ou **Rouge Clignotant ("ALERTE : Signature Invalide ❌ - Contenu Altéré")**.

### 3. La Barre Inférieure : Console Crypto en temps réel
* Une mini-console au style terminal affiche toutes les opérations cryptographiques en arrière-plan à chaque clic.
* *Exemple :*
  ```text
  [16:40:02] Génération de la clé de session AES-256...
  [16:40:03] Chiffrement du fichier avec la clé AES...
  [16:40:03] Calcul du hash SHA-256 et signature numérique RSA-PSS...
  [16:40:04] Chiffrement RSA-OAEP de la clé AES avec la clé publique de la Directrice...
  [16:40:04] Envoi de l'enveloppe JSON via le proxy VPN local (port 8001)...
  ```
