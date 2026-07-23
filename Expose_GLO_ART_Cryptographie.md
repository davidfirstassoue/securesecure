# La Cryptographie : Conception, développement et sécurisation réseau d'une plateforme universitaire de partage de fichiers chiffrés

**Institut de Management et des Sciences Appliquées (IMSA)**
Établissement d'enseignement supérieur
Licence 3 Professionnelle en Génie Logiciel / Administration Réseau (GLO/ART)
Génie Numériques

**Année académique 2025-2026**

**Rédigé et présenté par :**
- M. Glenn-Dany ESSONE MEYO
- M. Emmanuel Delvane LEBOUMA-LEGNIMA
- M. David First ASSOUE ASSOUE
- M. Greg Stéphane ELLA NDONG

**Formateur :** M. Eric NGOMA DIUNGA

---

## 1. Introduction et contexte du projet

### 1.1 Problématique

Dans le cadre de notre module de réseaux et sécurité des systèmes d'information, nous avons choisi de traiter un scénario que l'on rencontre dans toute organisation qui échange des documents sensibles : comment garantir la confidentialité, l'intégrité et l'authenticité d'un fichier lorsqu'il transite entre un émetteur et un destinataire, alors même que le réseau qui les relie n'est pas maîtrisé de bout en bout et peut être la cible d'un attaquant interne ou externe.

Nous avons construit notre scénario autour d'un campus universitaire fictif : Mme DIBA, comptable du campus, doit transmettre des documents confidentiels à M. AKENDENGUE, directeur de l'université, qui doit pouvoir vérifier que le fichier reçu n'a été ni altéré ni intercepté. Un troisième acteur, Gregg, étudiant malveillant, tente de s'introduire dans cet échange pour en intercepter ou en corrompre le contenu.

Ce projet nous a permis de travailler simultanément sur deux plans que l'on sépare trop souvent en cours : le développement logiciel d'une application web sécurisée, et l'ingénierie réseau permettant de faire transiter cette application dans des conditions réalistes (accès WiFi contrôlé, interconnexion de sites distants, exposition maîtrisée d'un service vers Internet). Notre application, baptisée **SecureShare**, matérialise cette convergence.

### 1.2 Objectifs

- Concevoir et développer une application de partage de fichiers reposant sur un chiffrement de bout en bout robuste.
- Simuler une architecture réseau réaliste combinant une segmentation par VLANs, un contrôle d'accès WiFi centralisé et une interconnexion de sites distants.
- Démontrer, par une phase d'attaque volontaire, la résistance réelle des mécanismes cryptographiques et réseau mis en place.
- Documenter chaque brique afin qu'elle soit reproductible et transposable à un contexte professionnel réel.

### 1.3 Choix technologiques

Nous avons retenu Python et le micro-framework Flask pour le développement, à la fois pour la clarté du code et pour la richesse de son écosystème cryptographique (bibliothèque `cryptography`). Côté chiffrement, nous combinons un algorithme symétrique rapide, **AES-256-CBC**, pour le contenu des fichiers, avec un schéma asymétrique **RSA-2048** (OAEP pour le chiffrement de la clé de session, PSS pour la signature) afin de gérer l'échange de clés et l'authenticité, le tout adossé à des empreintes **SHA-256** pour le contrôle d'intégrité.

Côté réseau, nous nous appuyons sur **ngrok** comme proxy inverse pour exposer notre service applicatif via une zone d'accès sécurisée, sans avoir à déployer un pare-feu de périmètre physique, sur **Kerio VPN** pour l'interconnexion chiffrée de deux sites, et sur **Kerio Control** couplé à **Active Directory** pour l'authentification WiFi Entreprise (802.1X).

---

## 2. Architecture globale et interconnexion réseau

### 2.1 Vue d'ensemble

Notre architecture applicative sépare clairement trois responsabilités : les postes clients (`client/`), le serveur central (`server/`), et les utilitaires cryptographiques partagés (`shared/`), auxquels s'ajoute le module attaquant (`attacker/`) utilisé pour les tests offensifs. Les clients de Mme DIBA et de M. AKENDENGUE exposent une interface Flask locale sur le port 5001, tandis que le serveur central héberge l'API applicative et la base SQLite sur le port 5000 en HTTPS. Cette séparation nous a permis de répartir le travail de développement sans créer de dépendances croisées difficiles à intégrer.

> **Figure 1 — Architecture globale de SecureShare.** Postes clients (VLAN Clients) → Point d'accès WiFi WPA3-Enterprise (802.1X, RADIUS Kerio, sync AD) → Tunnel site-à-site IPsec Kerio (AES-256 GCM, certificats) → Zone d'accès sécurisée (proxy inverse ngrok) → Serveur Flask central sécurisé (AES-256, RSA-2048, SHA-256) + base SQLite chiffrée. Un chemin en pointillés rouges représente la bascule simulée vers le faux serveur de Gregg (port 5002) lors de la phase de crash-test.

### 2.2 La zone d'accès sécurisée par proxy inverse avec ngrok

Faute de pouvoir déployer un pare-feu de périmètre physique pendant nos séances de travaux pratiques, nous avons reproduit le comportement d'une zone d'accès sécurisée par proxy inverse à l'aide d'un tunnel ngrok. Le serveur Flask tourne localement sur le port 5000, dans le VLAN Serveur ; ngrok expose ce port via une URL HTTPS publique qui joue le rôle de point d'entrée unique de cette zone d'accès sécurisée, sans exposer directement l'adresse du serveur interne.

Le principe de cloisonnement propre à une architecture segmentée par VLANs est respecté dans le sens applicatif : le trafic part toujours des clients vers le serveur exposé, jamais l'inverse — le serveur n'a aucune capacité d'initier une connexion vers le réseau privé des clients. Au démarrage, le serveur interroge l'API locale de ngrok, détecte le tunnel actif et publie automatiquement l'URL dans `shared/server_info.json` ; le client lit ce fichier au lancement et s'y connecte sans configuration manuelle, ce qui a considérablement fluidifié nos tests en équipe.

### 2.3 Interconnexion de sites par VPN et contrôle d'accès WiFi

Pour donner corps à la dimension multi-sites de notre scénario universitaire, nous avons mis en place un tunnel VPN site à site entre deux implantations, **Charbonnage** et **Damas**, à l'aide du protocole propriétaire Kerio VPN. Le pare-feu de Charbonnage expose son interface WAN (`192.168.0.250`), résolue par un service DDNS (`imsa1.ddns.net`) afin de survivre au changement d'adresse IP publique dynamique. Un certificat SSL généré localement sur ce pare-feu sert de base d'authentification : le site de Damas s'y connecte en utilisant l'empreinte (fingerprint) de ce certificat, sans qu'aucune configuration manuelle de routes statiques ne soit nécessaire — les routes entre les réseaux `10.2.1.0/24` (Charbonnage) et `10.1.1.0/24`, `172.31.131.0/24`, `192.168.168.0/24` (Damas) se créent automatiquement une fois le tunnel monté. Cette interconnexion donne accès, depuis Damas, au serveur Active Directory et applicatif de Charbonnage (`10.2.1.17`) via RDP.

En parallèle, nous avons remplacé l'authentification WiFi par clé partagée (WPA-PSK), intrinsèquement faible car unique et partagée par tous, par une authentification individuelle WPA-Enterprise (802.1X) adossée à l'annuaire Active Directory. Kerio Control joue ici le rôle de serveur RADIUS : un certificat SSL local sécurise la négociation EAP-TLS/PEAP, le point d'accès est déclaré comme client RADIUS avec une clé secrète partagée, et chaque utilisateur s'authentifie avec son compte de domaine plutôt qu'avec une clé commune. Cette architecture garantit une traçabilité nominative des connexions et permet de révoquer un accès WiFi instantanément en désactivant le compte AD correspondant.

> **Figure 2 — Interconnexion site à site Charbonnage ↔ Damas.** Tunnel Kerio VPN (authentification par certificat) et contrôle d'accès WiFi RADIUS/Active Directory déployé de manière homogène sur les deux sites.

---

## 3. Développement appliqué et modules applicatifs

### 3.1 Répartition du code et des rôles applicatifs

Notre arborescence de projet reflète directement la répartition des rôles du scénario. Le dossier `client/` porte l'interface et la logique de Mme DIBA et de M. AKENDENGUE (`app.py`, gabarits HTML de tableau de bord et de scolarité, feuilles de style et scripts JavaScript). Le dossier `server/` héberge l'API centrale (`main.py`) et la base SQLite qui conserve les messages échangés et les données de scolarité. Le dossier `shared/` regroupe le code commun aux deux extrémités : les fonctions de chiffrement (`crypto_utils.py`), le script de génération des paires de clés RSA (`generate_keys.py`) et l'annuaire de clés publiques/privées. Cette mutualisation nous a évité toute duplication de code cryptographique, source classique d'erreurs de sécurité.

### 3.2 Déploiement sur les postes de travail

Pour dérouler la démonstration, nous répartissons les dossiers sur trois rôles physiques ou virtuels : le serveur central de l'université reçoit `server/` et `shared/` et lance `py server/main.py` sur le port 5000 en HTTPS ; les postes clients reçoivent `client/` et `shared/` et lancent `py client/app.py`, exposant l'interface sur `http://localhost:5001` ; le poste de l'attaquant reçoit uniquement `attacker/` et lance `py attacker/eve_rogue_server.py`, qui simule un faux annuaire de clés sur le port 5002.

### 3.3 Table de synthèse des contributions

| Membre | Périmètre | Livrable technique |
|---|---|---|
| Membre 1 — ASSOUE David | Développement applicatif & réseau | Application Flask (client/serveur), pipeline cryptographique, exposition sécurisée via proxy inverse ngrok, liaison automatique client-serveur |
| Membre 2 — ESSONE Dany | Interconnexion réseau | Tunnel VPN site à site Kerio (Charbonnage ↔ Damas), authentification par certificat, DDNS |
| Membre 3 — LEBOUMA Emmanuel | Contrôle d'accès réseau | Authentification WiFi WPA-Enterprise via Kerio Control (RADIUS) et Active Directory |
| Membre 4 — ELLA NDONG Greg | Audit offensif | Scénario d'attaque MITM (`eve_rogue_server.py`), tests d'intégrité et de résistance de l'application |

---

## 4. Implémentation cryptographique et sécurité réseau

### 4.1 Chiffrement du contenu : AES-256-CBC

Chaque fichier transmis par Mme DIBA est chiffré avec AES en mode CBC et une clé de session de 256 bits, générée aléatoirement pour chaque envoi. Ce choix nous permet de bénéficier d'un chiffrement symétrique rapide, adapté au volume des documents administratifs échangés, tout en isolant chaque transaction : la compromission d'une clé de session ne remet jamais en cause les échanges passés ou futurs, propriété que l'on qualifie de confidentialité persistante partielle à l'échelle de la session.

### 4.2 Échange de clé et confidentialité : RSA-2048 / OAEP

La clé de session AES ne circule jamais en clair : elle est chiffrée avec la clé publique RSA-2048 du destinataire selon le schéma de complétion OAEP (Optimal Asymmetric Encryption Padding), qui élimine les faiblesses du padding RSA historique (PKCS#1 v1.5) face aux attaques de type Bleichenbacher. Seul M. AKENDENGUE, détenteur de la clé privée correspondante, peut déchiffrer la clé de session puis le fichier.

### 4.3 Authenticité et intégrité : RSA-PSS et SHA-256

Avant l'envoi, Mme DIBA calcule une empreinte SHA-256 du fichier original puis la signe avec sa clé privée RSA selon le schéma PSS (Probabilistic Signature Scheme), plus robuste que le schéma déterministe PKCS#1 v1.5 face aux attaques par falsification existentielle. À réception, M. Akendengue recalcule l'empreinte du fichier déchiffré et vérifie la signature avec la clé publique de Mme DIBA : toute altération du contenu ou usurpation d'émetteur est détectée avant l'ouverture du document.

### 4.4 Sécurisation de la couche transport et de l'accès réseau

La sécurité applicative que nous venons de décrire s'appuie sur une couche transport et une couche d'accès également chiffrées. Le serveur central expose son API en HTTPS grâce à un certificat SSL propre ; le tunnel ngrok qui matérialise la zone d'accès sécurisée ne fait que relayer ce trafic déjà chiffré. À l'échelle du campus, le tunnel Kerio VPN entre Charbonnage et Damas est lui-même authentifié par certificat, et l'accès WiFi des postes clients est filtré en amont par l'authentification RADIUS/AD en 802.1X (EAP-TLS/PEAP), ce qui interdit à un poste non enregistré dans l'annuaire de rejoindre le réseau, indépendamment de la sécurité applicative de SecureShare.

### 4.5 Synthèse des mécanismes cryptographiques

| Mécanisme | Objectif | Rôle dans SecureShare |
|---|---|---|
| AES-256-CBC | Confidentialité | Chiffrement symétrique du contenu du fichier avec une clé de session unique par envoi |
| RSA-2048 / OAEP | Confidentialité de la clé | Chiffrement asymétrique de la clé de session AES à destination du destinataire |
| RSA-2048 / PSS | Authenticité | Signature numérique du fichier par l'émetteur, vérifiable par le destinataire |
| SHA-256 | Intégrité | Empreinte du fichier utilisée dans la signature et vérifiée à réception |
| TLS / certificat SSL | Transport | Chiffrement du canal HTTPS serveur, du tunnel VPN Kerio et de la négociation RADIUS |

---

## 5. Phase de crash-test et sécurisation (rôle de Gregg — Membre 4)

### 5.1 Démarche du membre 4

Le quatrième membre de notre équipe a endossé le rôle de Gregg, l'étudiant pirate du scénario, avec pour mission de tester en conditions réelles la résistance de l'application face à des scénarios d'écoute passive et d'attaque active de type man-in-the-middle (MITM). Contrairement aux trois autres contributions, ce travail n'a pas produit de document de configuration mais un script opérationnel, `attacker/eve_rogue_server.py`, ainsi qu'une série de scénarios d'attaque exécutés directement contre notre infrastructure de test.

### 5.2 Scénario d'attaque : détournement de l'annuaire de clés

Le script `eve_rogue_server.py` fait tourner un faux serveur sur le port 5002, qui imite l'API du serveur légitime (port 5000) et sert un annuaire de clés publiques falsifié. Le vecteur d'attaque retenu simule un empoisonnement ARP ou DNS local : sur le poste de Mme DIBA, l'adresse du serveur est basculée manuellement du port légitime 5000 vers le port pirate 5002. Si l'application faisait confiance à n'importe quelle clé publique reçue sans validation, Gregg pourrait alors substituer sa propre clé publique à celle de M. AKENDENGUE, intercepter la clé de session chiffrée à son intention, la déchiffrer avec sa propre clé privée, lire le fichier en clair, puis le re-chiffrer et le retransmettre au destinataire légitime sans que rien ne le trahisse — une attaque MITM classique sur un échange de clés non authentifié.

### 5.3 Vulnérabilités identifiées et correctifs apportés

- **Absence initiale de vérification de provenance des clés publiques** : nous avons renforcé l'annuaire partagé (`shared/keys/`) pour qu'une clé publique ne soit acceptée que si elle correspond à l'identité déclarée, limitant la fenêtre d'exploitation d'un faux annuaire.
- **Détection d'intégrité a posteriori** : même lorsque la substitution de clé a été simulée avec succès en amont, la vérification de signature RSA-PSS côté destinataire échoue si le fichier a été altéré ou si l'émetteur ne correspond pas à la clé attendue, ce qui a permis de détecter systématiquement les tentatives d'interception lors de nos tests.
- **Confiance implicite dans l'adresse du serveur** : le mécanisme de liaison automatique via `shared/server_info.json`, initialement conçu pour le confort d'usage, aurait pu faciliter une redirection silencieuse vers le faux serveur ; nous recommandons, en évolution du projet, de vérifier l'empreinte du certificat du serveur au moment de la connexion (certificate pinning), à l'image de ce que fait déjà le tunnel Kerio VPN entre nos deux sites.
- **Absence de journalisation des tentatives de connexion suspectes** : nous avons identifié le besoin d'ajouter, côté serveur légitime, un journal des adresses sources et des échecs de vérification de signature, afin de transformer un incident détecté a posteriori en alerte exploitable en temps réel.

### 5.4 Bilan de la phase offensive

Cette phase de crash-test a confirmé que la robustesse de SecureShare ne repose pas sur l'hypothèse optimiste qu'aucun attaquant ne peut atteindre le réseau, mais sur la combinaison de plusieurs couches indépendantes : contrôle d'accès réseau en amont (RADIUS/AD), confidentialité du transport (TLS, VPN), et surtout vérification cryptographique de bout en bout au niveau applicatif (signature RSA-PSS et empreinte SHA-256), qui reste la dernière ligne de défense même si les couches réseau amont étaient contournées.

---

## 6. Analyse détaillée des images

### 6.1 Figure 1 — Architecture globale de SecureShare

Cette image retrace le trajet complet d'une information depuis le poste d'un utilisateur jusqu'au serveur central, en passant par les trois couches de sécurité que nous avons mises en place. En partant du haut du schéma, les postes de Mme DIBA et de M. AKENDENGUE, regroupés dans le VLAN Clients, exécutent chacun le client Flask local sur le port 5001 : c'est à cet endroit que les fichiers sont chiffrés avant envoi, ou déchiffrés et vérifiés après réception. Ces postes ne peuvent rejoindre le réseau qu'après authentification individuelle auprès du point d'accès WiFi WPA-Enterprise, lui-même adossé à Kerio Control agissant comme serveur RADIUS et interrogeant l'Active Directory — première barrière du schéma, purement réseau, indépendante du contenu applicatif échangé.

Une fois cette authentification réseau franchie, le trafic applicatif emprunte le tunnel VPN site à site Kerio, matérialisé au centre du schéma, qui chiffre et authentifie par certificat la liaison entre les deux implantations du campus. Le flux traverse ensuite la zone d'accès sécurisée matérialisée par le proxy inverse : l'URL publique ngrok y reçoit les requêtes HTTPS et les relaie vers le serveur Flask central du VLAN Serveur (port 5000), qui applique les vérifications cryptographiques (AES, RSA, SHA-256) avant d'écrire ou de lire dans la base SQLite. Le bloc rouge en bas du schéma représente Gregg et son faux serveur sur le port 5002 : la flèche en pointillés rouges illustre la bascule manuelle du port 5000 vers le port 5002 que nous avons utilisée pour simuler, sans disposer d'un vrai empoisonnement ARP, l'effet d'une attaque MITM locale sur le poste de Mme DIBA.

### 6.2 Figure 2 — Interconnexion Charbonnage ↔ Damas

Cette seconde image détaille la partie strictement réseau de notre infrastructure, indépendamment de l'application SecureShare elle-même. Les deux encadrés latéraux représentent les sites de Charbonnage (à gauche) et de Damas (à droite), chacun disposant de son propre pare-feu Kerio, de son propre plan d'adressage IP et de son propre point d'accès WiFi. Le pare-feu de Charbonnage expose son interface WAN (`192.168.0.250`), résolue en permanence via le service DDNS `imsa1.ddns.net` malgré une adresse IP publique dynamique, et porte un certificat SSL local dont l'empreinte sert de justificatif d'authentification pour le tunnel.

La flèche verte centrale symbolise le tunnel Kerio VPN proprement dit : le pare-feu de Damas s'y connecte en présentant l'empreinte du certificat généré côté Charbonnage, ce qui établit une relation de confiance mutuelle sans échange manuel de mots de passe. Une fois le tunnel actif, l'encadré jaune en bas du schéma illustre la création automatique des routes entre les quatre réseaux en présence — `10.2.1.0/24` côté Charbonnage, puis `10.1.1.0/24`, `172.31.131.0/24` et `192.168.168.0/24` côté Damas — sans intervention manuelle sur les tables de routage. Enfin, le bloc violet en bas de schéma représente le serveur applicatif SecureShare : les flèches violettes en pointillés montrent que ce serveur, une fois les réseaux interconnectés, devient accessible indifféremment depuis les deux sites, chacun protégé en amont par sa propre politique RADIUS/Active Directory représentée dans les encadrés inférieurs de chaque site.

---

## 7. Conclusion et perspectives

Ce projet nous a permis de mettre en cohérence, sur un scénario unique, des compétences que nous abordons habituellement de manière cloisonnée : développement applicatif, cryptographie appliquée, ingénierie réseau et audit offensif. La complémentarité de nos quatre contributions — application et sécurisation réseau, interconnexion VPN, contrôle d'accès RADIUS/AD, et audit Red Team — nous a montré concrètement qu'aucune de ces briques prise isolément ne suffit à garantir la sécurité d'un échange de documents sensibles : c'est leur superposition, chacune couvrant un vecteur d'attaque différent, qui rend l'ensemble robuste.

La phase de crash-test conduite par notre camarade a été particulièrement formatrice : elle a validé que notre couche cryptographique applicative (signature RSA-PSS et empreinte SHA-256) constitue une défense en profondeur efficace même en cas de compromission partielle des couches réseau. Elle a également mis en lumière des axes d'amélioration concrets pour la suite du projet, en particulier la vérification systématique de l'empreinte du certificat serveur (certificate pinning) côté client et la mise en place d'une journalisation centralisée des tentatives d'authentification échouées, tant au niveau applicatif qu'au niveau RADIUS.

À plus long terme, nous envisagerions de remplacer notre simulation ngrok par un véritable pare-feu de périmètre physique pour la zone d'accès sécurisée, d'étendre le tunnel VPN à un troisième site afin de tester le passage à l'échelle du routage automatique, et d'automatiser la phase de crash-test sous la forme de tests d'intégration rejoués à chaque évolution du code, afin que la sécurité de SecureShare reste vérifiée en continu plutôt que validée ponctuellement.
