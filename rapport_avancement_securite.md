# Rapport d'Avancement — Projet SecureShare : Sécurité Réseau et Cryptographique

**Projet de Sécurité des Réseaux Informatiques**  
*Destinataire : Professeur de Sécurité des Réseaux*  
*Date : 11 juillet 2026*  
*Auteurs : Groupe Cryptographie (Spécialité Réseau & Sécurité)*

---

## 📌 Présentation & Contexte du Projet (Université)

Le projet **SecureShare** vise à concevoir et simuler une infrastructure de partage de fichiers et de messages hautement sécurisée pour une **Université** possédant plusieurs succursales (Campus Principal, Faculté de Médecine, Faculté des Sciences).

Nous simulons l'interception et le blocage des menaces par un **Étudiant Pirate** (intrus sur le réseau local ou Internet) tentant d'analyser, de modifier ou d'intercepter les communications entre la **Comptable du Campus** et la **Directrice de l'Université**.

---

## 📊 État d'Avancement Général

Nous avons structuré notre travail selon la méthodologie de sécurité exigée. Voici l'état actuel de nos livrables :

* **Conception Théorique & Analyse des Besoins** : **✅ 100% Terminé**
* **Définition de la Politique de Sécurité** : **✅ 100% Terminé**
* **Modélisation Réseau & Architecture des 3 Scénarios** : **✅ 100% Terminé**
* **Cahier de Recette (Scénarios de test physiques au lab)** : **✅ 100% Terminé**
* **Développement & Codage Python** : **⏳ En cours (Démarrage de la phase de code)**

---

## 🛜 Modélisation des 3 Scénarios Réseau

Pour répondre aux exigences d'accès de l'Université, nous avons conçu **trois scénarios réseau distincts** au sein d'une seule et même application de messagerie.

### Scénario 1 : LAN avec Tunnel VPN (Réseau Interne Universitaire)
* **Description** : Interconnexion confidentielle entre le Campus Principal et la Faculté de Médecine.
* **Exemple Concret** : La **Comptable du Campus** doit envoyer les fichiers de salaires des professeurs à la **Directrice**. Elles sont toutes deux connectées sur le réseau Wi-Fi de l'université. L'**Étudiant Pirate** tente de sniffer le trafic avec Wireshark. 
* **Sécurité Appliquée** : Un tunnel VPN proxy Python fait maison (`vpn_client.py` ➔ `vpn_server.py`) intercepte le trafic sur le port `8001`, le chiffre entièrement avec l'algorithme AES-256 symétrique, et le transmet sur le port `9000` du serveur. L'Étudiant Pirate ne voit passer que des paquets chiffrés illisibles sur le port `9000`.

### Scénario 2 : Serveur Public en DMZ (Accès Externe Cloisonné)
* **Description** : Publication d'un service de dépôt de fichiers (ex: devoirs ou rapports de recherche) accessible depuis l'extérieur tout en protégeant les bases de données internes.
* **Exemple Concret** : Les étudiants ou partenaires externes doivent pouvoir se connecter au serveur de messagerie depuis leur domicile à travers Internet.
* **Sécurité Appliquée** : Le serveur de messagerie (serveur Flask) est placé dans une **DMZ (Zone Démilitarisée)** sur le routeur du lab (`10.1.1.1`). Le pare-feu autorise les requêtes entrantes HTTPS (port `443`/`5000`) vers la DMZ, mais bloque strictement toute tentative de connexion de la DMZ vers le réseau interne d'administration (le LAN). Si le serveur public est piraté, le pirate reste confiné dans la DMZ.

### Scénario 3 : Communication Directe sur Internet (P2P de Bout en Bout)
* **Description** : Échange confidentiel de point à point entre deux entités sans passer par un serveur intermédiaire (qui pourrait être compromis ou indisponible).
* **Exemple Concret** : Un chercheur de la Faculté des Sciences envoie une formule de brevet ultra-secrète directement à la Directrice via une liaison Internet publique.
* **Sécurité Appliquée** : Sécurité garantie à 100% par la cryptographie de bout en bout. La clé AES qui chiffre le fichier est elle-même chiffrée avec la clé publique RSA-2048 de la Directrice (RSA-OAEP). Même si le fichier transite par des routeurs publics non sécurisés sur Internet, personne ne peut intercepter ou déchiffrer le contenu sans la clé privée de la Directrice.

---

## 📝 Réponses aux Questions de la Roadmap du Professeur

Conformément au travail demandé, nous avons conçu notre environnement de test en répondant aux 5 étapes clés de la méthodologie de sécurité :

### 1. Identification du Besoin Explicite
Nous avons identifié 4 vulnérabilités majeures dans le flux d'échange de l'Université :
* **Le besoin de confidentialité des fichiers** : Empêcher l'Étudiant Pirate de lire les rapports administratifs.
* **Le besoin d'intégrité** : Garantir que les notes des étudiants ou les budgets n'ont pas été modifiés pendant le transit.
* **Le besoin d'authenticité (Anti-MITM)** : S'assurer que la Comptable envoie bien le fichier à la Directrice, et non à l'Étudiant Pirate qui se ferait passer pour elle.
* **Le besoin de sécurité réseau (masquage de trafic)** : Masquer les en-têtes IP et HTTP pour empêcher l'analyse de trafic (métadonnées).

### 2. Étude de l'Existant (État de l'Art)
Dans le milieu professionnel, ces menaces sont traitées par des technologies standards :
* **HTTPS / TLS** : Chiffrement du transport des requêtes web.
* **VPN IPSec ou WireGuard** : Tunnelisation chiffrée pour interconnecter des sites distants (site-à-site).
* **Chiffrement PGP / E2EE** : Chiffrement de bout en bout basé sur des paires de clés asymétriques pour assurer la confidentialité en P2P.
* **Normes ANSSI pour les DMZ** : Cloisonnement strict des serveurs publics par des pare-feux physiques.

### 3. Proposition de la Politique de Sécurité
Nous avons rédigé la politique de sécurité de l'application SecureShare, qui impose 5 règles strictes :
1. **Chiffrement Symétrique** : Tout fichier doit être chiffré en **AES-256-CBC** avec un IV (vecteur d'initialisation) aléatoire et unique.
2. **Chiffrement Asymétrique** : La clé AES de session doit obligatoirement être chiffrée en **RSA-OAEP (2048 bits)** avec la clé publique du destinataire.
3. **Signature Numérique** : Chaque envoi doit comporter un hash **SHA-256** du fichier, signé avec la clé privée de l'expéditeur en **RSA-PSS**.
4. **Vérification d'Identité** : Comparaison obligatoire de l'**empreinte de clé (fingerprint)** au format `XXXX-XXXX-XXXX-XXXX` par un canal hors-ligne (téléphone, papier, écran) pour bloquer l'Homme du Milieu.
5. **Tunnelisation VPN** : Obligation d'utiliser le proxy VPN local pour tout échange interne au réseau local.

### 4. Implémentation de la Politique (Structure et Code)
Notre code est structuré en modules Python pour faciliter les tests unitaires et le déploiement sur les équipements réels du lab (Windows Server 2019 à l'adresse IP `192.168.168.23`) :
* **`shared/crypto_utils.py`** : Regroupe les fonctions cryptographiques (RSA, AES, signatures).
* **`server/main.py`** : Serveur Flask hébergeant l'annuaire de clés et la base de messages.
* **`client/app.py`** : Client web local pour la Comptable ou la Directrice.
* **`vpn/vpn_client.py` & `vpn_server.py`** : Scripts de tunnelisation proxy.

### 5. Cahier de Recette (Tests de Sécurité)
Nous avons défini 5 tests physiques à exécuter en direct sur les machines du lab :
* **Test 1 (Normal)** : Envoi d'un fichier comptable. Déchiffrement réussi et validation d'intégrité verte (✅) côté Directrice.
* **Test 2 (Altération)** : Modification volontaire d'un octet en route. Rejet immédiat du fichier et alerte rouge (❌) côté Directrice (échec de la signature RSA-PSS).
* **Test 3 (MITM non protégé)** : L'Étudiant Pirate intercepte la demande de clé de la Comptable, lui envoie sa clé publique. Il intercepte, décrypte et affiche le fichier confidentiel sur son écran.
* **Test 4 (MITM bloqué)** : La Comptable compare l'empreinte de la clé avec celle affichée sur l'écran de la Directrice. L'incohérence est détectée, la Comptable annule l'envoi.
* **Test 5 (Sécurité Réseau VPN)** : Activation du VPN local. Capture de paquets sur Wireshark par l'Étudiant Pirate : les requêtes HTTP en clair ont disparu au profit d'un flux TCP chiffré illisible sur le port `9000`.
