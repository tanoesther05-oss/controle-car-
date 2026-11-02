# Déployer le site EMSP sur Vercel

Le projet contient maintenant le point d'entrée `api/index.py` et `vercel.json` nécessaires à Vercel. Cette configuration impose PostgreSQL en production : SQLite est réservé au développement local. Vercel sert les fichiers statiques collectés pendant le build.

## 1. Sauvegarder les inscriptions locales

Dans PowerShell, depuis le dossier du projet, exportez les etudiants et l'historique des imports avant de changer de base :

    python manage.py dumpdata students.Student students.SyncLog --indent 2 -o emsp_students_backup.json

Ce fichier contient des donnees personnelles. Il est ignore par Git et Vercel : ne le partagez pas et ne le committez pas.

## 2. Creer les comptes de deploiement

1. Creez un depot GitHub prive et envoyez-y le code du projet. Le fichier .gitignore exclut la base SQLite, les fichiers .env et les sauvegardes.
2. Dans Vercel, importez ce depot comme un nouveau projet, mais ne lancez pas encore le deploiement si l'assistant permet de le differer.
3. Dans Vercel Storage / Marketplace, creez une base PostgreSQL et copiez son URL de connexion. Choisissez si possible une region proche de la fonction Vercel.

Ne mettez jamais de fichier .env, de base de donnees SQLite, de sauvegarde d'etudiants ou de cle Google dans GitHub.

Si le dossier n'a pas encore ete initialise avec Git, apres avoir cree un depot GitHub vide, envoyez le projet avec ces commandes (remplacez l'URL par celle de votre depot) :

    git init
    git add .
    git commit -m "Initial EMSP transport app"
    git branch -M main
    git remote add origin https://github.com/VOTRE-COMPTE/VOTRE-DEPOT.git
    git push -u origin main

## 3. Definir les variables Vercel

Dans Project Settings > Environment Variables, definissez-les pour Production (et Preview seulement si une base separee y est configuree). Marquez les variables de connexion et les cles comme sensibles :

| Variable | Valeur |
| --- | --- |
| DJANGO_SECRET_KEY | Une nouvelle cle aleatoire, differente de la cle de developpement |
| DJANGO_DEBUG | False |
| DJANGO_ALLOWED_HOSTS | Le domaine Vercel de production, puis tout domaine personnalise |
| CSRF_TRUSTED_ORIGINS | URL(s) HTTPS de production, par exemple https://mon-site.vercel.app |
| DATABASE_URL | URL de connexion PostgreSQL fournie par le fournisseur |
| GOOGLE_SHEET_ID | Identifiant de la feuille, si la synchronisation Google est activee |
| GOOGLE_WORKSHEET_NAME | Nom de l'onglet, par exemple Form Responses 1 |
| GOOGLE_SERVICE_ACCOUNT_JSON | Contenu JSON complet de la cle du compte de service, si Google Sheets est utilise |

Pour fabriquer une cle Django sous Windows :

    python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

Dans Google Sheets, partagez la feuille en lecture seule avec l'adresse e-mail du compte de service. Collez le JSON de sa cle dans la variable privee Vercel GOOGLE_SERVICE_ACCOUNT_JSON; ne l'enregistrez jamais dans le depot. La variable GOOGLE_SERVICE_ACCOUNT_FILE reste disponible pour le developpement local.

Les parametres Django ajoutent automatiquement les domaines VERCEL_URL et VERCEL_PROJECT_PRODUCTION_URL fournis par Vercel. Ajoutez toutefois le domaine public a DJANGO_ALLOWED_HOSTS et CSRF_TRUSTED_ORIGINS apres l'avoir choisi. Le deploiement doit avoir DATABASE_URL et DJANGO_SECRET_KEY, sinon Django l'arrete volontairement sans demarrer avec une base temporaire. Si l'import GitHub lance automatiquement un premier build avant la configuration des variables, ce premier build echouera; ajoutez les variables puis relancez le deploiement.

## 4. Creer la base et migrer les donnees

Installez la CLI Vercel si necessaire, connectez le depot, puis recuperez les variables de production sur votre ordinateur :

    npm install --global vercel
    vercel login
    vercel link
    vercel env pull .env.local

.env.local est ignore par Git. Verifiez qu'il contient la DATABASE_URL PostgreSQL de production, puis executez :

    python manage.py migrate
    python manage.py loaddata emsp_students_backup.json
    python manage.py createsuperuser

La migration cree les licences et filieres par defaut. Le fichier de sauvegarde ne contient pas les comptes utilisateurs : creez un nouveau superutilisateur avec un mot de passe fort. Le mot de passe de demonstration local n'est pas exporte.

Verifiez la connexion sur le site et le nombre de fiches avant de supprimer la sauvegarde. Gardez-la dans un emplacement prive et supprimez-la du dossier du projet apres validation.

## 5. Deployer

Envoyez les changements sur la branche connectee a Vercel, ou utilisez :

    vercel deploy --prod

Vercel detecte Django depuis manage.py, execute collectstatic pour les fichiers statiques et les sert depuis son CDN. Chaque changement des variables d'environnement necessite un nouveau deploiement.

## Points a verifier apres deploiement

- La page de connexion et l'administration fonctionnent en HTTPS.
- Les styles CSS, Bootstrap et les icones s'affichent.
- Le tableau de bord affiche les fiches migrees.
- L'export CSV fonctionne.
- La synchronisation Google Sheets fonctionne si elle est activee.
- Le compte superutilisateur utilise un mot de passe fort et unique.

Ne branchez pas les apercus Vercel publics sur la base de production. Une variable DATABASE_URL separee est necessaire pour Preview si ces apercus sont actives.
