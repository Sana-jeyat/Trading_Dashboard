# Backend API pour Bots de Trading

## Installation

1. **Créer un environnement virtuel** :

```bash
python -m venv venv
source .venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
.venv312\Scripts\activate
```

**Démarrer FASTAPI**

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Pour lancer l'environnement**:

```bash
.venv312\Scripts\python.exe main.py
.venv312\Scripts\python.exe trading_bot.py
```

2. **Installer les dépendances** :

```bash
pip install -r requirements.txt
```

3. **Configuration** :

```bash
cp .env.example .env
# Éditez le fichier .env avec vos paramètres
```

4. **Initialiser la base de données** :

```bash
python -c "from database import engine; from models import Base; Base.metadata.create_all(bind=engine)"
```

## Lancement

```bash
python main.py
```

L'API sera disponible sur http://localhost:8000

Documentation interactive : http://localhost:8000/docs

## Structure de l'API

### Authentification

- `POST /auth/register` - Créer un compte
- `POST /auth/login` - Se connecter

### Gestion des bots

- `GET /bots` - Liste des bots
- `POST /bots` - Créer un bot
- `GET /bots/{id}` - Détails d'un bot
- `PUT /bots/{id}` - Modifier un bot
- `DELETE /bots/{id}` - Supprimer un bot
- `POST /bots/{id}/start` - Démarrer un bot
- `POST /bots/{id}/stop` - Arrêter un bot

### Transactions

- `GET /bots/{id}/transactions` - Transactions d'un bot
- `GET /transactions` - Toutes les transactions

### Statistiques

- `GET /stats` - Statistiques globales

## Intégration avec vos scripts

1. **Adaptez `trading_bot_example.py`** avec votre logique de trading
2. **Configurez les chemins** dans `bot_manager.py`
3. **Testez** avec un bot simple

## Sécurité

- Changez `SECRET_KEY` en production
- Utilisez HTTPS en production
- Stockez les clés privées de manière sécurisée
- Activez les logs pour le monitoring

## Base de données

Par défaut SQLite, facilement changeable vers PostgreSQL en modifiant `DATABASE_URL` dans `.env`.

## Déploiement

```bash
# Avec Docker (optionnel)
docker build -t trading-bot-api .
docker run -p 8000:8000 trading-bot-api

# Ou directement
uvicorn main:app --host 0.0.0.0 --port 8000
```
