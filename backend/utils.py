# backend/utils.py
import requests
import logging

logger = logging.getLogger(__name__)

def get_current_price(token_pair: str) -> float:
    """
    Retourne le prix actuel de la paire token_pair en euros.
    token_pair doit être au format "KNO/WMATIC".
    """
    base, quote = token_pair.split("/")
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={base.lower()}&vs_currencies={quote.lower()}"
    try:
        response = requests.get(url)
        data = response.json()
        price = data[base.lower()][quote.lower()]
        return float(price)
    except Exception as e:
        logger.error(f"Erreur récupération prix pour {token_pair}: {e}")
        return 0.0
