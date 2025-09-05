# 🔗 Guide d'Intégration Bot Distant

## 📋 **Ce qu'il faut faire**

### **Sur le PC du Dashboard** (celui-ci)
✅ Rien à faire - tout est déjà configuré
- Dashboard web sur http://localhost:5173
- API backend sur http://localhost:8000

### **Sur le PC de votre Bot**

#### **1. Télécharger le client**
```bash
# Téléchargez seulement ce fichier depuis le Dashboard
wget http://IP_DASHBOARD:8000/download/remote_bot_client.py
# OU copiez le contenu du fichier remote_bot_client.py
```

#### **2. Modifier votre script existant**
```python
# Au début de votre script WPOL/KNO existant
from remote_bot_client import DashboardClient

class MonBotWPOL:
    def __init__(self):
        # AJOUTEZ cette connexion Dashboard
        self.dashboard = DashboardClient(
            api_url="http://192.168.1.100:8000",  # IP du PC Dashboard
            bot_token="votre_token_ici",          # Token depuis Dashboard
            bot_id="bot-1"                        # ID de votre bot
        )
        
        # Vos variables existantes
        self.balance = 10000.0
        self.total_profit = 0.0
        # ... reste de votre code
    
    def start(self):
        # AJOUTEZ la connexion
        if not self.dashboard.connect():
            print("❌ Impossible de se connecter au Dashboard")
            return
        
        # Votre logique existante
        self.run_trading_loop()
    
    def run_trading_loop(self):
        while True:
            # Votre logique existante pour récupérer le prix
            current_price = self.get_wpol_price()
            
            # Vos conditions d'achat existantes
            if self.should_buy(current_price):
                amount = 1000
                success = self.execute_buy_wpol(current_price, amount)
                
                if success:
                    # AJOUTEZ seulement cette ligne
                    self.dashboard.send_transaction("buy", amount, current_price)
            
            # Vos conditions de vente existantes  
            elif self.should_sell(current_price):
                amount = 500
                success = self.execute_sell_wpol(current_price, amount)
                
                if success:
                    profit = self.calculate_profit(amount, current_price)
                    # AJOUTEZ seulement cette ligne
                    self.dashboard.send_transaction("sell", amount, current_price, profit)
            
            time.sleep(60)  # Votre délai existant
```

#### **3. Configuration réseau**
```python
# Dans votre script, remplacez par l'IP réelle du PC Dashboard
api_url="http://192.168.1.100:8000"  # IP du PC avec le Dashboard
```

## 🌐 **Configuration Réseau**

### **Trouver l'IP du PC Dashboard**
```bash
# Sur le PC Dashboard (Windows)
ipconfig

# Sur le PC Dashboard (Linux/Mac)  
ifconfig
```

### **Tester la connexion**
```bash
# Depuis le PC du bot, testez :
curl http://IP_DASHBOARD:8000/
# Doit retourner : {"message": "Trading Bot API is running"}
```

## 🔑 **Récupérer le Token**

1. **Ouvrez le Dashboard** : http://localhost:5173
2. **Allez dans Configuration** 
3. **Copiez le token** affiché
4. **Collez-le** dans votre script bot

## ✅ **Avantages de cette approche**

- ✅ **Votre bot reste** sur son PC habituel
- ✅ **Aucun transfert** de fichiers volumineux
- ✅ **Performance** : Pas de latence réseau pour le trading
- ✅ **Sécurité** : Vos clés privées restent sur le PC bot
- ✅ **Flexibilité** : Plusieurs bots sur différents PCs

## 🔄 **Résultat**

- **Votre bot** continue à tourner normalement sur son PC
- **Le Dashboard** reçoit toutes les transactions en temps réel
- **Vous contrôlez** les paramètres depuis l'interface web
- **Synchronisation** automatique des configurations

## 📞 **Test de Connexion**

Une fois configuré, vous devriez voir dans le Dashboard :
- 🟢 **Bot en ligne** 
- 📊 **Transactions en temps réel**
- ⚙️ **Modifications de config** appliquées au bot