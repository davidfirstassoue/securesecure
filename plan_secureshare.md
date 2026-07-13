# SecureShare — Plan complet du projet (Sécurité des réseaux)

Groupe cryptographie, 4 personnes, ~6 jours avant la présentation. Objectif : une appli fonctionnelle de partage de fichiers sécurisé, démontrable en live devant le prof.

---

## 1. Vue d'ensemble

**Le principe** : Alice envoie un fichier à Bob. Le fichier est chiffré (AES), la clé AES est elle-même chiffrée avec la clé publique RSA de Bob, le fichier est signé pour garantir son intégrité, et une empreinte de clé publique permet de détecter une attaque de type "homme du milieu" (MITM). Une démo live montre l'attaque qui réussit sans protection, puis qui échoue avec protection.

**Ce que chacun doit pouvoir dire au prof, seul, sans les autres** : "voici mon mécanisme, voici pourquoi il existe, voici ce qui se passe si on l'enlève."

---

## 2. Stack technique

- **Langage** : Python 3.10+ pour toute la logique crypto/réseau (une seule lib à apprendre : `cryptography`, cohérent pour les 4).
- **Lib crypto** : `cryptography` (pyca) — RSA 2048 bits, AES-256-CBC, SHA-256, signatures RSA-PSS.
- **Serveur** : Flask — sert d'annuaire de clés publiques + de relais de messages chiffrés (une "boîte aux lettres").
- **Frontend** : HTML/CSS/JS simple (fetch vers l'API Flask). Pas de framework lourd, pas le temps. Bootstrap ou juste du CSS propre pour aller vite visuellement.
- **Git** : un repo commun, une branche par membre, merge sur `main` au Jour 3 et Jour 4.

Installation de base (à faire ce soir, chacun sur sa machine) :
```
pip install flask cryptography requests
```

---

## 3. Architecture générale

```
secureshare/
  server/            -> API Flask : annuaire de clés + relais de messages (Membre 1 + toi pour le contrat)
  client_alice/      -> interface web côté émetteur
  client_bob/        -> interface web côté récepteur
  attacker/          -> script du faux serveur "Eve" (toi)
  shared/            -> fonctions crypto communes, format de l'enveloppe
  README.md
```

Le serveur central expose :
- `GET /publickey/<user>` → clé publique + empreinte
- `POST /send` → dépose un message chiffré pour un destinataire
- `GET /receive/<user>` → récupère le message en attente

Pour la démo, idéalement **3 machines séparées** sur le même réseau (Alice, Bob, Eve) — c'est beaucoup plus parlant pour le prof qu'une seule machine avec plusieurs onglets.

---

## 4. Le contrat de données (À FIGER CE SOIR, priorité absolue)

Tant que ce format n'est pas fixé, personne ne peut intégrer son module avec les autres. C'est le premier point de l'appel de ce soir.

**Format de l'empreinte de clé publique** (Membre 1) :
```
sha256(clé_publique_PEM) → 16 premiers caractères hex, groupés par 4
Exemple : "A1B2-C3D4-E5F6-A7B8"
```

**Enveloppe du message envoyé** (le cœur du contrat) :
```json
{
  "from": "alice",
  "to": "bob",
  "encrypted_aes_key": "base64(...)",
  "iv": "base64(...)",
  "ciphertext": "base64(...)",
  "sha256_hex": "hex(...)",
  "signature": "base64(...)",
  "sender_fingerprint_used": "A1B2-C3D4-E5F6-A7B8"
}
```

**Qui remplit quel champ :**

| Champ | Rempli par | Mécanisme |
|---|---|---|
| `encrypted_aes_key` | Toi (Membre 4) | RSA-OAEP de la clé AES avec la clé publique du destinataire |
| `iv`, `ciphertext` | Membre 2 | AES-256-CBC du fichier |
| `sha256_hex`, `signature` | Membre 3 | SHA-256 + signature RSA-PSS |
| `sender_fingerprint_used` | Membre 1 (généré) + toi (vérifié avant envoi) | empreinte de la clé publique |

Chacun code sa fonction indépendamment en respectant ces noms de champs, et le mardi (Jour 3) on assemble sans friction.

---

## 5. Détail technique par personne

### Membre 1 — Clés et identité
- `generate_keys.py` : génère 2 paires RSA 2048 bits (Alice, Bob), stockées en dur (fichiers PEM ou variables Python) — pas de vrai système de login, pas le temps.
- `compute_fingerprint(public_key_pem) -> str` : SHA-256 de la clé, formaté en `XXXX-XXXX-XXXX-XXXX`.
- Endpoint Flask `GET /publickey/<user>` qui renvoie `{username, public_key_pem, fingerprint}`.
- UI : page "Vous êtes Bob, votre empreinte publique est : XXXX-XXXX-XXXX-XXXX" — affichée bien en évidence, c'est le canal de vérification "hors réseau" utilisé dans la démo d'attaque.

### Membre 2 — Chiffrement du fichier (AES)
- `encrypt_file(file_bytes) -> (aes_key, iv, ciphertext)` : AES-256-CBC, padding PKCS7, clé et IV générés avec `os.urandom` à chaque envoi.
- `decrypt_file(aes_key, iv, ciphertext) -> file_bytes`.
- UI côté Alice : sélection de fichier + indicateur "fichier chiffré ✅" (afficher taille avant/après pour que ce soit visuellement parlant).
- UI côté Bob : bouton déchiffrer + téléchargement du fichier en clair.

### Membre 3 — Intégrité
- `hash_file(file_bytes) -> sha256_hex`.
- `sign_hash(hash_bytes, private_key) -> signature` (RSA-PSS + SHA-256).
- `verify_signature(hash_bytes, signature, public_key) -> bool`.
- UI côté Bob : "Intégrité vérifiée ✅" en vert ou "ALERTE : fichier modifié ❌" en rouge, bien visible.
- Prévoir un bouton caché/mode debug pour modifier volontairement 1 octet du fichier reçu, afin de montrer en direct que la vérification casse.

### Membre 4 (toi) — Échange de clé + démo d'attaque
- `encrypt_aes_key(aes_key, recipient_public_key) -> encrypted_aes_key` (RSA-OAEP).
- `decrypt_aes_key(encrypted_aes_key, private_key) -> aes_key`.
- Logique d'envoi côté Alice : assembler l'enveloppe JSON complète avec les sorties des 3 autres modules + `POST /send`.
- Logique de réception côté Bob : `GET /receive`, puis dans l'ordre `decrypt_aes_key` → `decrypt_file` (Membre 2) → `verify_signature` (Membre 3).
- `eve_rogue_server.py` : un faux serveur Flask qui répond à `GET /publickey/bob` avec la clé publique d'Eve à la place de celle de Bob.
- Démo à deux versions : Alice pointée sur le vrai serveur (échec de l'attaque) vs Alice pointée sur le serveur d'Eve (succès de l'attaque, bloqué seulement par la vérification manuelle d'empreinte).

**Option bonus (si le temps le permet, pas prioritaire)** : un vrai proxy TCP (scapy/mitmproxy) au lieu du faux serveur, plus impressionnant mais plus risqué à faire tourner en live le jour J. La version "faux serveur" est fiable, on ne prend pas de risque avec la fiabilité de la démo.

---

## 6. Planning jour par jour

| Jour | Objectif | Détail |
|---|---|---|
| **J0 (ce soir)** | Cadrage | Appel 30 min : valider le contrat de données (section 4), créer le repo Git, chacun installe son environnement, création des branches |
| **J1** | Dev isolé | Chacun code sa brique en isolation, avec des données factices respectant le contrat. Pas besoin d'attendre les autres. |
| **J2** | Dev isolé + tests | Suite du dev, tests unitaires basiques de chaque fonction (un simple `if __name__ == "__main__":` qui teste sa propre fonction suffit) |
| **J3** | Première intégration | Binômes : Membre 1 + toi (clés → échange), Membre 2 + Membre 3 (chiffrement → intégrité). Puis merge sur `main`. |
| **J4** | Intégration complète | Flux Alice → serveur → Bob de bout en bout, tous les modules connectés. Session de debug collective (prévoir du temps, c'est souvent là que ça casse). Démarrage du script d'attaque Eve. |
| **J5** | Démo + robustesse | Finalisation de l'attaque MITM, répétition du flux complet plusieurs fois, préparation d'un court support visuel (le schéma généré), **enregistrement d'une vidéo de secours** de la démo complète au cas où ça bug en live. |
| **J6 (Jour J)** | Présentation | Répétition finale le matin, présentation au prof. |

---

## 7. Scénario de démo pour le prof

1. **Intro rapide (2 min)** : montrer le schéma du flux, chacun se présente en une phrase avec sa brique.
2. **Cas normal** : Alice envoie un fichier à Bob → chiffrement AES → Bob déchiffre → intégrité vérifiée ✅.
3. **Fichier modifié en transit** : altérer volontairement 1 octet du message avant réception → Bob détecte l'erreur d'intégrité ❌.
4. **Attaque MITM sans vérification d'empreinte** : Alice interroge le serveur d'Eve au lieu du vrai serveur, chiffre avec la mauvaise clé, Eve lit le fichier en clair → montrer le fichier lisible côté Eve.
5. **Attaque bloquée avec vérification d'empreinte** : Alice compare l'empreinte reçue à celle affichée par Bob (canal séparé), mismatch détecté, envoi refusé.
6. **Conclusion (1 min)** : rappel de chaque mécanisme et de ce qu'il empêche concrètement.

---

## 8. Checklist immédiate (ce soir)

- [ ] Appel 30 min avec les 3 autres
- [ ] Valider le contrat de données (section 4) — ne pas en sortir sans accord unanime
- [ ] Créer le repo Git + inviter tout le monde
- [ ] Chacun installe `flask` + `cryptography`
- [ ] Créer les 4 branches (`feature/membre1-auth`, `feature/membre2-aes`, `feature/membre3-integrite`, `feature/membre4-echange`)
- [ ] Fixer le prochain point de sync (fin J2 ou début J3)
