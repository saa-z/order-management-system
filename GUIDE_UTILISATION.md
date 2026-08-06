# San Giorgio OMS — Guide d'utilisation

## Sommaire

1. [Installation sur le PC principal](#1-installation-sur-le-pc-principal)
2. [Lancement du système](#2-lancement-du-système)
3. [L'application PC (central)](#3-lapplication-pc-central)
4. [L'accès depuis téléphone / tablette (web)](#4-laccès-depuis-téléphone--tablette-web)
5. [Prendre une commande](#5-prendre-une-commande)
6. [Historique des commandes](#6-historique-des-commandes)
7. [Gestion des stocks](#7-gestion-des-stocks)
8. [Gestion des articles](#8-gestion-des-articles)
9. [Gestion des accès (utilisateurs)](#9-gestion-des-accès-utilisateurs)
10. [Impression des tickets](#10-impression-des-tickets)

---

## 1. Installation sur le PC principal

### Prérequis

- **Python 3.11+** installé sur la machine
- Une **imprimante** configurée comme imprimante par défaut (pour les tickets)
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

## 2. Lancement du système

Le système se compose de **deux parties** à lancer en parallèle.

> **Les données ne sont jamais perdues quand le PC s'éteint.** Tout est stocké dans un fichier `sangiorgio.db` sur le disque. Le relancement du serveur reprend exactement là où on s'est arrêté (commandes, articles, utilisateurs, stocks — tout est conservé).

### Lancement quotidien (après l'installation)

Chaque jour (ou après un redémarrage du PC), il suffit de :

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

C'est tout. La base de données existante est réutilisée automatiquement.

> `--host 0.0.0.0` rend le serveur accessible depuis tout le réseau local (téléphones, tablettes).

> **Ne jamais relancer `python init_db.py`** sauf si vous voulez tout remettre à zéro (toutes les commandes, articles et utilisateurs seront supprimés et recréés depuis le menu de base).

### À propos de l'application de bureau

L'application se connecte automatiquement au serveur local (`127.0.0.1:8000`) — **aucune connexion n'est requise** sur le PC principal (confiance locale).

Elle démarre aussi un **processus d'impression en arrière-plan** qui surveille les tickets à imprimer (commandes passées depuis les téléphones).

### Résumé

| Commande | Quand l'utiliser | Effet sur les données |
|----------|-----------------|----------------------|
| `uvicorn main:app ...` | Chaque lancement | Aucun — reprend la base existante |
| `python app.py` | Chaque lancement | Aucun — interface seulement |
| `python init_db.py` | Installation initiale uniquement | **Supprime tout** et recrée depuis zéro |

---

## 3. L'application PC (central)

Au lancement, un écran d'accueil « SAN GIORGIO » s'affiche brièvement, puis le **menu principal** apparaît avec les options suivantes :

| Bouton                     | Description                                      |
|---------------------------|--------------------------------------------------|
| **Prendre commande**       | Ouvrir le point de vente (POS) pour saisir une commande |
| **Historique des commandes** | Voir toutes les commandes passées, filtrer, imprimer |
| **Gestion des stocks**     | Modifier les quantités en stock des articles et options |
| **Gestion des articles**   | Ajouter/modifier/supprimer des catégories, articles, ingrédients |
| **Gestion des accès**      | Créer et gérer les comptes utilisateurs (serveurs, admins) |

---

## 4. L'accès depuis téléphone / tablette (web)

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

## 5. Prendre une commande

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
3. Un bon de cuisine est automatiquement imprimé.

---

## 6. Historique des commandes

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

## 7. Gestion des stocks

Accessible depuis le menu principal (PC uniquement).

Pour chaque article et chaque option :

- **Quantité** : modifier le stock avec le compteur (+/-).
- **N/A** : cocher la case pour indiquer que le stock est illimité (pas de suivi de quantité).

Quand le stock d'un article tombe à 0, il apparaît comme indisponible dans le POS.

---

## 8. Gestion des articles

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

## 9. Gestion des accès (utilisateurs)

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

### Modifier un utilisateur

- Cliquer sur un utilisateur pour modifier son nom, mot de passe ou rôle.
- L'icône **oeil** sur chaque ligne permet d'afficher/masquer le mot de passe.

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

## 10. Impression des tickets

L'imprimante par défaut du PC principal est utilisée pour tous les tickets. Aucune configuration n'est nécessaire dans l'application.

### Bon de cuisine

Imprimé automatiquement quand :
- Une commande est envoyée en cuisine
- Des articles sont ajoutés à une commande existante

Contenu : date, table, couverts, serveur, articles groupés par catégorie (plats en premier, boissons/desserts en bas).

### Ticket client (reçu)

Imprimé via le bouton **Imprimer reçu** dans le détail d'une commande.

Contenu : « San Giorgio — Saint Georges de Mons », date, articles avec prix, total, total par personne, message de remerciement.

### Bon d'annulation

Imprimé automatiquement quand une commande est annulée (pour prévenir la cuisine).

### Depuis un téléphone

Toutes les actions d'impression déclenchées depuis un téléphone sont **mises en file d'attente** et imprimées automatiquement par le PC principal (délai de quelques secondes).
