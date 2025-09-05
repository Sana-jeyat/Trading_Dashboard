# 🌐 Guide Configuration Réseau Dashboard ↔ Bot

## 📍 **Étape 1 : Identifier les PCs**

### **PC Dashboard** (celui-ci)
```bash
# Windows - Ouvrir CMD et taper :
ipconfig

# Cherchez "Adresse IPv4" dans la section WiFi ou Ethernet
# Exemple : 192.168.1.100
```

### **PC Bot** (votre bot Python)
```bash
# Windows - Ouvrir CMD et taper :
ipconfig

# Exemple : 192.168.1.101
```

## 🔧 **Étape 2 : Tester la connexion**

### **Depuis le PC Bot, testez l'accès au Dashboard** :
```bash
# Remplacez 192.168.1.100 par l'IP réelle du PC Dashboard
ping 192.168.1.100

# Si ça marche, testez l'API :
curl http://192.168.1.100:8000/
# Doit retourner : {"message": "Trading Bot API is running"}
```

## 🔥 **Étape 3 : Configuration Firewall**

### **Sur le PC Dashboard** :
```bash
# Windows Firewall - Autoriser les ports
# Méthode 1 : Interface graphique
1. Panneau de configuration → Système et sécurité → Pare-feu Windows
2. Paramètres avancés → Règles de trafic entrant → Nouvelle règle
3. Port → TCP → Ports spécifiques : 8000,5173
4. Autoriser la connexion → Tous les profils → Nom : "Dashboard Trading Bot"

# Méthode 2 : Ligne de commande (Admin)
netsh advfirewall firewall add rule name="Dashboard API" dir=in action=allow protocol=TCP localport=8000
netsh advfirewall firewall add rule name="Dashboard Web" dir=in action=allow protocol=TCP localport=5173
```

## 📁 **Étape 4 : Télécharger le client sur PC Bot**

### **Option A : Téléchargement direct**
```bash
# Depuis le PC Bot, dans votre dossier de bot :
curl -O http://192.168.1.100:8000/download/remote_bot_client.py
```

### **Option B : Copie manuelle**
1. **Ouvrez** http://192.168.1.100:8000/download/remote_bot_client.py dans un navigateur
2. **Copiez** tout le contenu
3. **Créez** un fichier `remote_bot_client.py` sur le PC Bot
4. **Collez** le contenu

## 🔑 **Étape 5 : Récupérer le token**

### **Sur le PC Dashboard** :
1. **Ouvrez** http://localhost:5173
2. **Allez** dans "Configuration"  
3. **Copiez** le token affiché
4. **Notez** l'IP du Dashboard

## 🐍 **Étape 6 : Modifier votre script Python**

### **Sur le PC Bot, dans votre script WPOL/KNO** :
```python
# Ajoutez au début de votre script
from remote_bot_client import DashboardClient

class MonBotWPOL:
    def __init__(self):
        # CONFIGURATION DASHBOARD
        self.dashboard = DashboardClient(
            api_url="http://192.168.1.100:8000",  # IP du PC Dashboard
            bot_token="votre_token_ici",          # Token depuis Dashboard
            bot_id="bot-1"                        # ID de votre bot
        )
        
        # Vos variables existantes
        self.balance = 10000.0
        # ... reste de votre code
    
    def start(self):
        # Connexion au Dashboard
        if not self.dashboard.connect():
            print("❌ Impossible de se connecter au Dashboard")
            return
        
        print("✅ Bot connecté au Dashboard")
        
        # Votre logique de trading existante
        self.run_trading_loop()
    
    def run_trading_loop(self):
        while True:
            # Récupérer la config mise à jour depuis le Dashboard
            config = self.dashboard.get_bot_config()
            if config:
                self.buy_threshold = config.get('buy_price_threshold', 0.007)
                self.sell_threshold = config.get('sell_price_threshold', 0.009)
                # ... autres paramètres
            
            # Votre logique de prix WPOL/KNO existante
            current_price = self.get_wpol_price()  # Votre fonction
            
            # Vos conditions d'achat existantes
            if self.should_buy(current_price):
                amount = 1000
                success = self.execute_buy_wpol(current_price, amount)  # Votre fonction
                
                if success:
                    # AJOUTEZ seulement cette ligne
                    self.dashboard.send_transaction("buy", amount, current_price)
                    self.dashboard.update_bot_metrics(balance=self.balance)
            
            # Vos conditions de vente existantes
            elif self.should_sell(current_price):
                amount = 500
                success = self.execute_sell_wpol(current_price, amount)  # Votre fonction
                
                if success:
                    profit = self.calculate_profit(amount, current_price)  # Votre fonction
                    # AJOUTEZ seulement ces lignes
                    self.dashboard.send_transaction("sell", amount, current_price, profit)
                    self.dashboard.update_bot_metrics(
                        balance=self.balance, 
                        total_profit=self.total_profit
                    )
            
            time.sleep(60)  # Votre délai existant

# Lancement
if __name__ == "__main__":
    bot = MonBotWPOL()
    bot.start()
```

## ✅ **Étape 7 : Test final**

### **Démarrer le Dashboard** (PC Dashboard) :
```bash
# Terminal 1 : Backend
cd backend
python main.py

# Terminal 2 : Frontend  
npm run dev
```

### **Démarrer votre bot** (PC Bot) :
```bash
python votre_script_wpol.py
```

### **Vérifications** :
1. **Dashboard** : http://localhost:5173 → Bot doit apparaître "🟢 En ligne"
2. **Transactions** : Doivent apparaître en temps réel
3. **Configuration** : Changements appliqués au bot

## 🚨 **Dépannage**

### **Bot ne se connecte pas** :
```bash
# Testez la connectivité
ping 192.168.1.100
telnet 192.168.1.100 8000

# Vérifiez les logs
python votre_script_wpol.py
# Regardez les messages d'erreur
```

### **Firewall bloque** :
- **Désactivez temporairement** le firewall pour tester
- **Ajoutez les règles** spécifiques pour les ports 8000 et 5173

### **IP change** :
- **Configurez une IP fixe** sur le PC Dashboard
- **Ou utilisez le nom d'ordinateur** : `http://NOM-PC-DASHBOARD:8000`

## 📱 **Résultat Final**

- **Votre bot WPOL/KNO** continue sur son PC
- **Dashboard** affiche tout en temps réel  
- **Modifications** de config appliquées automatiquement
- **Historique** complet des transactions
- **Contrôle à distance** total ! 🎮