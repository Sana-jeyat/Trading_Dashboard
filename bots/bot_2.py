from remote_bot_client import DashboardClient
import logging, time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleBot:
    def __init__(self):
        self.dashboard = DashboardClient(
            api_url="http://127.0.0.1:8000",   # ton backend FastAPI
            bot_token="bot_a7d74a1a6515bfd59a9a9c9e9ca26de5",           # ⚠️ ton token exact depuis phpMyAdmin
            bot_id="2"                         # ⚠️ l'id du bot dans ta table bots
        )

    def start(self):
        logger.info("🚀 Connexion au dashboard...")
        if not self.dashboard.connect():
            logger.error("❌ Échec de connexion (401 probable)")
            return
        
        logger.info("✅ Connecté au dashboard !")
        
        for i in range(5):
            price = 0.0015 + i * 0.0001
            logger.info(f"💰 Envoi d’un faux prix : {price}")
            self.dashboard.update_bot_metrics(balance=1000 + i * 10, last_buy_price=price)
            time.sleep(2)
        
        self.dashboard.disconnect()
        logger.info("🛑 Bot terminé proprement.")

if __name__ == "__main__":
    SimpleBot().start()
