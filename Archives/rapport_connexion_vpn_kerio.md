# Rapport de Connexion – Tunnel VPN Site à Site (Kerio VPN)

**Sites concernés :** Charbonnage & Damas  
**Protocole :** Kerio VPN (site-to-site, authentification par certificat)  
**Date :** 19/07/2026  

---

## 1. Objectif

Mettre en place un tunnel VPN site à site entre le Firewall du site **Charbonnage** et le Firewall du site **Damas**, en utilisant le protocole **Kerio VPN**, afin d'interconnecter les réseaux locaux des deux sites et de permettre l'accès aux ressources internes (notamment le serveur AD/Application) de manière sécurisée.

---

## 2. Configuration du Firewall - Site Charbonnage

### 2.1 Interface WAN
* **Interface WAN autorisée :** `192.168.0.250`
* Trafic entrant et sortant vers Internet autorisé sur cette interface.

### 2.2 Interface LAN
* **Réseau LAN :** `10.2.1.1`

### 2.3 Interconnexion via DDNS
* Le Firewall a été relié à un service DDNS afin de garantir une résolution de nom fixe malgré une IP publique dynamique.
* **Nom de domaine DDNS :** `imsa1.ddns.net`
* Cette interconnexion permet d'établir le tunnel directement via le nom de domaine plutôt que via une IP publique fixe.

### 2.4 Certificat SSL
* Génération d'un certificat SSL local disponible pour le Firewall.
* Certificat déployé sur le serveur VPN de Charbonnage, servant de base à l'authentification du tunnel.

---

## 3. Configuration du Firewall - Site Damas

### 3.1 Adressage réseau

| Réseau | Adresse |
| :--- | :--- |
| **LAN** | `10.1.1.1` |
| **VLAN 10** | `172.31.131.1` |
| **VLAN 99** | `192.168.168.1` |

### 3.2 Connexion au site Charbonnage
* Connexion établie directement vers Charbonnage grâce à l'empreinte (*fingerprint*) du certificat Kerio VPN généré côté Charbonnage.
* Les routes sont créées automatiquement entre les deux sites une fois le tunnel monté (pas de configuration manuelle des routes statiques nécessaire).

---

## 4. Ressource applicative accessible via le tunnel

* **Serveur Active Directory :** `10.2.1.17`
* **Accès :** Accessible via RDP
* Ce serveur héberge également le serveur applicatif de l'entreprise.

---

## 5. Synthèse du fonctionnement

1. Le FW Charbonnage expose son WAN (`192.168.0.250`) et est résolu via le DDNS `imsa1.ddns.net`.
2. Le certificat SSL local généré à Charbonnage est installé sur le serveur VPN.
3. Le FW Damas se connecte à Charbonnage en utilisant l'empreinte de ce certificat comme méthode d'authentification du tunnel Kerio VPN.
4. Une fois le tunnel établi, les routes entre les réseaux `10.2.1.0/24` (Charbonnage), `10.1.1.0/24`, `172.31.131.0/24` et `192.168.168.0/24` (Damas) sont créées automatiquement.
5. Le site Damas peut ainsi accéder au serveur AD/Application (`10.2.1.17`) via RDP à travers le tunnel sécurisé.

---

## 6. Points de vigilance / Suivi recommandé

* **Certificat SSL :** Vérifier le renouvellement du certificat SSL local avant expiration (risque de coupure du tunnel).
* **Service DDNS :** Surveiller la disponibilité du DDNS `imsa1.ddns.net` (dépendance critique pour la résolution du tunnel).
* **Plages IP :** Documenter les plages IP de chaque site pour éviter tout chevauchement futur en cas d'ajout de site.
* **Routage :** Vérifier la stabilité de la table de routage automatique en cas d'ajout d'un nouveau VLAN côté Damas.
