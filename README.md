# 🤖 Dashboard Trading Bot

Dashboard web pour gérer et monitorer vos bots de trading automatique.

## 🚀 Démarrage Rapide

### Frontend (Dashboard)
```bash
npm install
npm run dev
```
Le dashboard sera accessible sur http://localhost:5173

### Backend (API)
```bash
cd backend
pip install -r requirements.txt
python main.py
```
L'API sera accessible sur http://localhost:8000

## 🔗 Connecter votre Bot Distant

### 🔄 Synchronisation Bidirectionnelle

**Dashboard → Bot** :
- Modifiez les paramètres dans l'interface
- Le bot récupère automatiquement la nouvelle config
- Application immédiate des changements

**Bot → Dashboard** :
- Transactions envoyées en temps réel
- Métriques mises à jour automatiquement
- Statut de connexion affiché

### 1. Configuration Réseau
- **Dashboard PC** : Notez l'IP (ex: 192.168.1.100)
- **Bot PC** : Doit pouvoir accéder à cette IP
- **Port** : 8000 (API) et 5173 (Dashboard)

### 2. Intégration dans votre Script Python

```python
from remote_bot_client import DashboardClient

# Dans votre script de trading
dashboard = DashboardClient(
    api_url="http://192.168.1.100:8000",  # IP du PC Dashboard
    bot_token="votre_token",              # Token depuis le Dashboard
    bot_id="bot-1"                        # ID de votre bot
)

# Connexion
dashboard.connect()

# Envoyer une transaction
dashboard.send_transaction("buy", 1000, 0.0065)

# Mettre à jour les métriques
dashboard.update_bot_metrics(balance=15000, total_profit=250)
```

### 3. Étapes d'Intégration

1. **Créer un bot** dans le Dashboard
2. **Copier le token** d'authentification
3. **Télécharger** `remote_bot_client.py`
4. **Modifier votre script** pour utiliser le client
5. **Lancer votre bot** - il apparaîtra en ligne dans le Dashboard

## 📊 Fonctionnalités

- ✅ **Multi-bots** : Gérez plusieurs bots simultanément
- ✅ **Configuration** : Paramètres d'achat/vente par bot
- ✅ **Monitoring** : Transactions et profits en temps réel
- ✅ **Connexion distante** : Bots sur différents PCs
- ✅ **Historique** : Toutes les transactions sauvegardées
- ✅ **Alertes** : Statut en ligne/hors ligne

## 🛠️ Architecture

```
Dashboard PC (192.168.1.100)
├── Frontend React (port 5173)
├── Backend FastAPI (port 8000)
└── Base de données SQLite

Bot PC (192.168.1.101)
├── Votre script Python
├── remote_bot_client.py
└── Connexion HTTP vers Dashboard
```

## 🔧 Configuration Avancée

### Variables d'environnement (.env)
```
DATABASE_URL=sqlite:///./trading_bots.db
SECRET_KEY=your-secret-key
API_HOST=0.0.0.0
API_PORT=8000
```

### Sécurité
- Tokens d'authentification uniques par bot
- Connexions HTTPS en production
- Heartbeat pour détecter les déconnexions

## 📱 Interface

- **Dashboard** : Vue d'ensemble de tous vos bots
- **Configuration** : Paramètres individuels par bot
- **Historique** : Toutes les transactions
- **Gestion** : Créer/supprimer des bots

## 🐛 Dépannage

### Bot ne se connecte pas
1. Vérifiez l'IP et le port
2. Testez avec `curl http://IP:8000/`
3. Vérifiez le token d'authentification

### Transactions non affichées
1. Vérifiez les logs du bot
2. Testez la connexion API
3. Vérifiez le format des données

## 📞 Support

Pour toute question sur l'intégration de votre bot spécifique, n'hésitez pas à demander !