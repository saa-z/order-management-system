# San Giorgio OMS — Guide d'utilisation

## Sommaire

1. [Installation sur le PC principal](#1-installation-sur-le-pc-principal)
2. [Configuration de l'imprimante thermique](#2-configuration-de-limprimante-thermique)
3. [Raccourci bureau et lancement rapide](#3-raccourci-bureau-et-lancement-rapide)
4. [Lancement du système](#4-lancement-du-système)
5. [L'application PC (central)](#5-lapplication-pc-central)
6. [L'accès depuis téléphone / tablette (web)](#6-laccès-depuis-téléphone--tablette-web)
7. [Prendre une commande](#7-prendre-une-commande)
8. [Historique des commandes](#8-historique-des-commandes)
9. [Gestion des stocks](#9-gestion-des-stocks)
10. [Gestion des articles](#10-gestion-des-articles)
11. [Gestion des accès (utilisateurs)](#11-gestion-des-accès-utilisateurs)
12. [Impression des tickets](#12-impression-des-tickets)
13. [Tiroir-caisse](#13-tiroir-caisse)
14. [Transfert sur un autre PC](#14-transfert-sur-un-autre-pc)

---

## 1. Installation sur le PC principal

### Prérequis

- **Python 3.11+** installé sur la machine
- Une **imprimante thermique SAGA SGPR-200II** connectée en USB (voir section 2)
- Le PC principal et les appareils mobiles doivent être sur le **même réseau Wi-Fi**

### Étapes d'installation

1. **Ouvrir un terminal** (PowerShell ou Invite de commandes) dans le dossier du projet.

2. **Créer un environnement virtuel** :

   ```bash
   cd order-management-system
   python -m venv .venv
   ```

3. **Activer l'environnement virtuel** :

   ```bash
   .venv\Scripts\activate
   ```

4. **Installer les dépendances** :

   ```bash
   pip install -r requirements.txt
   ```

5. **Initialiser la base de données** (à faire une seule fois, ou pour réinitialiser) :

   ```bash
   python init_db.py
   ```

   > **Attention** : cette commande recrée la base de données depuis zéro. Toutes les commandes, articles et utilisateurs existants seront supprimés. Un compte administrateur `admin` / `admin` est créé automatiquement.

---

## 2. Configuration de l'imprimante thermique

L'imprimante **SAGA SGPR-200II** est utilisée pour les tickets de cuisine, les reçus clients et l'ouverture du tiroir-caisse. Elle doit être connectée en **USB** au PC principal.

### Étape 1 — Brancher l'imprimante

Connecter l'imprimante au PC via un câble USB. Windows devrait la détecter automatiquement dans les périphériques.

### Étape 2 — Installer le pilote Generic / Text Only

L'imprimante doit être configurée avec le pilote **Generic / Text Only** pour permettre l'envoi de commandes ESC/POS brutes :

1. Ouvrir **Paramètres** > **Bluetooth et appareils** > **Imprimantes et scanners**.
2. Cliquer sur **Ajouter une imprimante** > **L'imprimante souhaitée n'est pas répertoriée**.
3. Choisir **Ajouter une imprimante locale** avec le port **USB001** (ou le port USB détecté).
4. Dans la liste des fabricants, choisir **Generic** puis **Generic / Text Only**.
5. Nommer l'imprimante **`Saga`** (ce nom exact est utilisé par le logiciel).
6. Terminer l'installation.

### Étape 3 — Vérifier

L'imprimante doit apparaître sous le nom **Saga** dans la liste des imprimantes Windows.

> **Important** : le nom de l'imprimante dans Windows doit être exactement **`Saga`**. Si le nom est différent, les impressions ne fonctionneront pas.

### Test rapide

Pour vérifier que l'imprimante fonctionne, lancer dans un terminal :

```bash
cd order-management-system
.venv\Scripts\activate
python -c "from frontend.cash_drawer import send_raw; ok, msg = send_raw(b'\x1B\x40Test impression\n\n\n\x1D\x56\x00'); print('OK' if ok else msg)"
```

Si le ticket s'imprime avec « Test impression », tout est bon.

---

## 3. Raccourci bureau et lancement rapide

### Créer le raccourci (à faire une seule fois)

Double-cliquer sur le fichier **`installer_raccourci.bat`** à la racine du dossier projet. Cela crée un raccourci **« San Giorgio - OMS »** sur le bureau avec le logo du restaurant.

### Lancement quotidien

Double-cliquer sur le raccourci **San Giorgio - OMS** sur le bureau. Le script :

1. Lance le serveur en arrière-plan (fenêtre minimisée)
2. Attend 3 secondes que le serveur démarre
3. Ouvre l'application de bureau
4. Quand l'application est fermée, le serveur s'arrête automatiquement

C'est la méthode recommandée pour le quotidien — un seul clic pour tout lancer.

---

## 4. Lancement du système

### Méthode simple (recommandée)

Utiliser le raccourci bureau (voir section 3).

### Méthode manuelle (avancée)

Le système se compose de **deux parties** à lancer en parallèle.

> **Les données ne sont jamais perdues quand le PC s'éteint.** Tout est stocké dans un fichier `sangiorgio.db` sur le disque. Le relancement du serveur reprend exactement là où on s'est arrêté (commandes, articles, utilisateurs, stocks — tout est conservé).

**Terminal 1 — Serveur :**

```bash
cd order-management-system
.venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 — Application de bureau :**

```bash
cd order-management-system/frontend
..\.venv\Scripts\activate
python app.py
```

> `--host 0.0.0.0` rend le serveur accessible depuis tout le réseau local (téléphones, tablettes).

> **Ne jamais relancer `python init_db.py`** sauf si vous voulez tout remettre à zéro (toutes les commandes, articles et utilisateurs seront supprimés et recréés depuis le menu de base).

### Résumé

| Commande | Quand l'utiliser | Effet sur les données |
|----------|-----------------|----------------------|
| Raccourci bureau | Chaque jour | Aucun — lance serveur + app |
| `uvicorn main:app ...` | Lancement manuel | Aucun — reprend la base existante |
| `python app.py` | Lancement manuel | Aucun — interface seulement |
| `python init_db.py` | Installation initiale uniquement | **Supprime tout** et recrée depuis zéro |

---

## 5. L'application PC (central)

Au lancement, un écran d'accueil « SAN GIORGIO » s'affiche brièvement, puis le **menu principal** apparaît avec les options suivantes :

| Bouton                     | Description                                      |
|---------------------------|--------------------------------------------------|
| **Prendre commande**       | Ouvrir le point de vente (POS) pour saisir une commande |
| **Historique des commandes** | Voir toutes les commandes passées, filtrer, imprimer |
| **Gestion des stocks**     | Modifier les quantités en stock des articles et options |
| **Gestion des articles**   | Ajouter/modifier/supprimer des catégories, articles, ingrédients |
| **Gestion des accès**      | Créer et gérer les comptes utilisateurs (serveurs, admins) |
| **Ouvrir la caisse**       | Envoyer la commande d'ouverture au tiroir-caisse |

---

## 6. L'accès depuis téléphone / tablette (web)

Les serveurs peuvent prendre des commandes depuis leur téléphone ou une tablette, à condition d'être connectés au même réseau Wi-Fi que le PC principal.

### Trouver l'adresse du PC

Sur le PC principal, ouvrir un terminal et taper :

```bash
ipconfig
```

Repérer l'**adresse IPv4** (ex : `192.168.1.42`).

### Se connecter depuis un téléphone

1. Ouvrir le navigateur du téléphone.
2. Aller à l'adresse : `http://192.168.1.42:8000` (remplacer par l'IP du PC).
3. La page de **connexion** s'affiche.
4. Entrer le nom d'utilisateur et le mot de passe fourni par l'administrateur.

### Menu web

Après connexion, deux options sont disponibles :

- **Prendre une commande** — même principe que sur le PC
- **Historique des commandes** — consulter, marquer payée, annuler, ajouter des articles

> Les impressions déclenchées depuis un téléphone sont automatiquement envoyées au PC principal qui les imprime.

---

## 7. Prendre une commande

### Étape 1 — Type de commande

Choisir entre :

- **Sur place** : renseigner le numéro de table, le nombre de couverts et l'emplacement (salle/terrasse)
- **À emporter** : renseigner le nom du client et l'heure de retrait (optionnels)

### Étape 2 — Sélection des articles

1. Cliquer sur une **catégorie** à gauche (Pizzas, Boissons, etc.).
2. Les articles de la catégorie s'affichent au centre.
3. Cliquer sur un article pour l'ajouter au panier (colonne de droite).

**Si l'article a des options** (ex : choix de parfum pour une glace, choix de soda), un popup s'ouvre pour sélectionner les options et la quantité.

### Étape 3 — Modifications d'ingrédients

Pour les articles avec ingrédients (pizzas, panozzos) :

1. Cliquer sur l'icône **crayon** à côté de l'article dans le panier.
2. Le popup de modifications s'ouvre avec les ingrédients de l'article déjà cochés.
3. **Décocher** un ingrédient = retrait (SANS).
4. Dans la section « Suppléments », rechercher et cocher des ingrédients à ajouter (SUPP, +1 € chacun).
5. Pour les pizzas, un choix de **base** est disponible (tomate ou crème fraîche).
6. Valider.

Le panier affiche les modifications au format : `(BASE crème fraîche, SUPP [roquette, chèvre], SANS [olives])`.

### Étape 4 — Commentaires

Cliquer sur l'icône **bulle** à côté d'un article dans le panier pour ajouter un commentaire libre (ex : « bien cuit », « sans sel »).

### Étape 5 — Envoi en cuisine

1. Vérifier le panier et le total.
2. Cliquer sur **Envoyer en cuisine**.
3. Un bon de cuisine est automatiquement imprimé sur l'imprimante SAGA (sans popup).

### Étape 6 — Facturation

Après l'envoi en cuisine, le bouton **Facturer** apparaît :

1. Cliquer sur **Facturer** pour marquer la commande comme payée.
2. Le reçu client est automatiquement imprimé.

---

## 8. Historique des commandes

### Consulter les commandes

L'historique affiche toutes les commandes avec leurs informations (date, type, total, serveur, statut).

**Filtres disponibles** (PC uniquement) :

- Recherche par article
- Plage de dates
- Fourchette de prix
- Tri par date, prix ou statut

### Détail d'une commande

Double-cliquer sur une commande (PC) ou la toucher (web) pour ouvrir le détail.

### Actions possibles

| Action                  | Disponible si        | Ce que ça fait                              |
|------------------------|----------------------|--------------------------------------------|
| **+ Ajouter des articles** | Commande en attente  | Ouvre un mini-POS pour ajouter des articles (nouveau bon) |
| **Marquer payée**       | Commande en attente  | Passe le statut à « Payée »                |
| **Annuler la commande** | Commande en attente  | Passe le statut à « Annulée », un bon d'annulation est imprimé |
| **Imprimer bon(s)**     | Toujours             | Réimprime les bons de cuisine (choix des bons si plusieurs) |
| **Imprimer reçu**       | Toujours             | Imprime le ticket client (facturation)      |

---

## 9. Gestion des stocks

Accessible depuis le menu principal (PC uniquement).

Pour chaque article et chaque option :

- **Quantité** : modifier le stock avec le compteur (+/-).
- **N/A** : cocher la case pour indiquer que le stock est illimité (pas de suivi de quantité).

Quand le stock d'un article tombe à 0, il apparaît comme indisponible dans le POS.

---

## 10. Gestion des articles

Accessible depuis le menu principal (PC uniquement).

### Catégories

- Créer, renommer ou supprimer des catégories.
- Les catégories supprimées sont placées dans la corbeille (suppression douce).
- Cocher **« Inclure la corbeille »** pour voir et restaurer les éléments supprimés.

### Articles

- Ajouter un article avec son nom, son prix et sa catégorie.
- Ajouter des **options** à un article (ex : choix de parfum).
- Supprimer ou restaurer des articles.

### Ingrédients

Accessible via le bouton **« Ingrédients »** dans la gestion des articles.

- Voir tous les ingrédients existants.
- Créer un nouvel ingrédient.
- Cocher **« Base »** pour marquer un ingrédient comme base de pizza (ex : tomate, crème fraîche).
- Supprimer un ingrédient.

Pour associer des ingrédients à un article : modifier l'article et utiliser le champ ingrédients.

---

## 11. Gestion des accès (utilisateurs)

Accessible depuis le menu principal (PC uniquement). **Réservé aux administrateurs.**

### Rôles

| Rôle      | Droits                                                    |
|-----------|-----------------------------------------------------------|
| **Admin** | Tout : commandes, stocks, articles, ingrédients, utilisateurs |
| **Serveur** (server) | Prendre des commandes et consulter l'historique uniquement |

### Créer un utilisateur

1. Aller dans **Gestion des accès**.
2. Cliquer sur **Créer un utilisateur**.
3. Renseigner :
   - **Nom d'utilisateur** (unique)
   - **Mot de passe**
   - **Rôle** (admin ou server)
4. Valider.

Le nouvel utilisateur peut maintenant se connecter depuis un téléphone/tablette avec ces identifiants.

### Modifier un mot de passe

- Cliquer sur l'icône **crayon** à côté du mot de passe pour le modifier directement.
- L'icône **oeil** permet d'afficher/masquer le mot de passe en clair.

### Révoquer / Réactiver

- **Révoquer** : désactive le compte (l'utilisateur ne peut plus se connecter). Le compte n'est pas supprimé, il peut être réactivé.
- **Réactiver** : rétablit un compte révoqué.
- Cocher **« Inclure révoqués »** pour voir les comptes désactivés.

### Compte par défaut

À l'installation, un seul compte existe :

| Utilisateur | Mot de passe | Rôle  |
|-------------|-------------|-------|
| `admin`     | `admin`     | Admin |

> **Il est fortement recommandé de changer le mot de passe du compte admin après l'installation.**

---

## 12. Impression des tickets

L'impression se fait directement sur l'imprimante thermique **SAGA** en ESC/POS natif, sans popup ni dialogue d'impression. Tout est automatique.

### Bon de cuisine

Imprimé automatiquement quand :
- Une commande est envoyée en cuisine
- Des articles sont ajoutés à une commande existante

Contenu :
- En-tête « BON DE CUISINE » en gros caractères
- Numéro de commande, type (sur place / à emporter), table, couverts, serveur
- Articles groupés par catégorie (plats en premier, boissons/desserts en bas)
- Texte agrandi (double hauteur) pour une lecture facile en cuisine
- Marges haut et bas pour faciliter l'accrochage

> Pas de prix sur le bon de cuisine — uniquement les noms et quantités.

### Ticket client (reçu)

Imprimé via le bouton **Facturer** (POS) ou **Imprimer reçu** (historique).

Contenu :
- En-tête : **SAN GIORGIO**, 10 Avenue de la Libération, 63780 Saint Georges de Mons
- SIRET : 95213378300029
- Date, heure, table, serveur
- Articles détaillés avec prix unitaire et total par ligne
- Total HT
- TVA 5,5%
- **TOTAL TTC** en gros caractères
- Total par personne (si couverts renseignés)
- Détail TVA (HT / TVA / TTC)
- Message « Merci et a bientot ! »

### Bon d'annulation

Imprimé automatiquement quand une commande est annulée (pour prévenir la cuisine).

### Depuis un téléphone

Toutes les actions d'impression déclenchées depuis un téléphone sont **mises en file d'attente** et imprimées automatiquement par le PC principal (délai de quelques secondes).

---

## 13. Tiroir-caisse

Le tiroir-caisse est branché sur l'imprimante SAGA via le port **RJ11** (connecteur téléphone à l'arrière de l'imprimante).

### Ouvrir la caisse

Depuis le menu principal de l'application PC, cliquer sur le bouton **Ouvrir la caisse**. La commande ESC/POS d'ouverture est envoyée à l'imprimante qui déclenche l'ouverture du tiroir.

> Le tiroir-caisse ne fonctionne que depuis le PC principal (pas depuis les téléphones).

---

## 14. Transfert sur un autre PC

Pour installer le système sur un nouveau PC (ex : le PC central du restaurant) :

### Étape 1 — Copier le dossier

Copier l'intégralité du dossier `san-gorgio-oms` sur le nouveau PC (clé USB, disque réseau, etc.).

### Étape 2 — Installer Python

Installer **Python 3.11+** sur le nouveau PC si ce n'est pas déjà fait.

### Étape 3 — Recréer l'environnement virtuel

Les environnements virtuels ne sont pas portables. Sur le nouveau PC :

```bash
cd order-management-system
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Étape 4 — Configurer l'imprimante

Suivre les instructions de la [section 2](#2-configuration-de-limprimante-thermique) pour installer l'imprimante SAGA avec le pilote Generic / Text Only sous le nom **Saga**.

### Étape 5 — Créer le raccourci bureau

Double-cliquer sur **`installer_raccourci.bat`** à la racine du dossier. Le raccourci « San Giorgio - OMS » avec le logo apparaît sur le bureau.

### Étape 6 — Lancer

Double-cliquer sur le raccourci. C'est prêt.

> **Note** : le fichier `sangiorgio.db` contient toutes les données. Si vous copiez ce fichier depuis l'ancien PC, vous récupérez toutes les commandes, articles et utilisateurs. Si vous ne le copiez pas, lancez `python init_db.py` pour repartir de zéro.
