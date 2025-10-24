"""Bot de trading automatique pour le token KNO sur le réseau Polygon.
Connecté au dashboard FastAPI en local.
"""

from web3 import Web3
import json, time, os, sys, random
from dotenv import load_dotenv
from datetime import datetime, timezone
import requests

# --- CONFIGURATION DE BASE ---
load_dotenv()
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
BOT_ID = int(os.getenv("BOT_ID", "1"))  # ID du bot dans le dashboard
API_URL = os.getenv("API_URL", "http://localhost:8000")  # FastAPI local

if not PRIVATE_KEY or not WALLET_ADDRESS:
    print(">>> Missing PRIVATE_KEY or WALLET_ADDRESS")
    sys.exit(1)

w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
if not w3.is_connected():
    print(">>> Erreur de connexion à Polygon")
    sys.exit(1)

wallet = w3.to_checksum_address(WALLET_ADDRESS)

# --- ADRESSES DES CONTRATS ---
WPOL = w3.to_checksum_address("0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270")
KNO  = w3.to_checksum_address("0x236fbfAa3Ec9E0B9BA013Df370c098bAd85aD631")
ROUTER = w3.to_checksum_address("0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff")

# --- ABIs ---
erc20_abi = json.loads("""[
    {"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},
    {"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"success","type":"bool"}],"type":"function"},
    {"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
    {"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"remaining","type":"uint256"}],"type":"function"},
    {"constant":false,"inputs":[],"name":"deposit","outputs":[],"stateMutability":"payable","type":"function"},
    {"constant":false,"inputs":[{"name":"wad","type":"uint256"}],"name":"withdraw","outputs":[],"stateMutability":"nonpayable","type":"function"}
]""")
router_abi = json.loads("""[
    {
        "name": "swapExactTokensForTokens",
        "type": "function",
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "amountOutMin", "type": "uint256"},
            {"name": "path", "type": "address[]"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"}
        ],
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "stateMutability": "nonpayable"
    },
    {
        "name": "getAmountsOut",
        "type": "function",
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "path", "type": "address[]"}
        ],
        "outputs": [
            {"name": "amounts", "type": "uint256[]"}
        ],
        "stateMutability": "view"
    }
]""")

# --- CONTRATS ---
token_wpol = w3.eth.contract(address=WPOL, abi=erc20_abi)
token_kno = w3.eth.contract(address=KNO, abi=erc20_abi)
router = w3.eth.contract(address=ROUTER, abi=router_abi)

# --- CONSTANTES ---
GECKO_TERMINAL_POOL_URL = "https://api.geckoterminal.com/api/v2/networks/polygon_pos/pools/0xdce471c5fc17879175966bea3c9fe0432f9b189e"
PRICE_FILE = "last_price.txt"
SELL_PRICE_FILE = "last_sell_price.txt"

# --- OUTILS WEB3 ---
def to_wei(amount, decimals):
    return int(float(amount) * 10**decimals)

def from_wei(amount, decimals):
    return float(amount) / 10**decimals

def get_nonce():
    return w3.eth.get_transaction_count(wallet)

def approve_token(token_contract, spender, amount, token_name="Token"):
    current_allowance = token_contract.functions.allowance(wallet, spender).call()
    if current_allowance >= amount:
        return True
    tx = token_contract.functions.approve(spender, amount).build_transaction({
        "from": wallet,
        "nonce": get_nonce(),
        "gas": 200000,
        "gasPrice": w3.eth.gas_price
    })
    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    return True

def cancel_pending_transactions():
    """Annule les transactions en attente en envoyant une transaction à soi-même"""
    try:
        current_nonce = w3.eth.get_transaction_count(wallet, 'pending')
        latest_nonce = w3.eth.get_transaction_count(wallet, 'latest')
        
        if current_nonce > latest_nonce:
            pending_txs = current_nonce - latest_nonce
            print(f">>> {pending_txs} transaction(s) en attente détectée(s)")
            
            # Transaction d'annulation à soi-même avec gas price élevé
            cancel_tx = {
                'to': wallet,
                'value': 0,
                'gas': 21000,
                'gasPrice': w3.to_wei(200, 'gwei'),  # Gas price très élevé
                'nonce': latest_nonce,
                'chainId': 137  # Polygon Mainnet
            }
            
            signed = w3.eth.account.sign_transaction(cancel_tx, PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            print(f">>> Transaction d'annulation envoyée: {w3.to_hex(tx_hash)}")
            
            # Attendre la confirmation
            print(">>> Attente confirmation de l'annulation...")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            if receipt.status == 1:
                print(">>> Transactions en attente annulées avec succès!")
                return True
            else:
                print(">>> Échec de l'annulation")
                return False
        else:
            print(">>> Aucune transaction en attente")
            return True
            
    except Exception as e:
        print(f">>> Erreur lors de l'annulation: {e}")
        return False
    
def read_price(file):
    try:
        with open(file, "r") as f:
            return float(f.read())
    except:
        return None

def write_price(file, price):
    with open(file, "w") as f:
        f.write(str(float(price)))

# --- DASHBOARD LOCAL ---
def report_trade(action, amount, price, profit=None):
    try:
        data = {
            "bot_id": BOT_ID,
            "type": action,
            "amount": amount,
            "price": price,
            "profit": profit,
            "timestamp": datetime.utcnow().isoformat()
        }

        print(f">>> Envoi transaction: {action} {amount} KNO à {price}€")
        print(f">>> Données: {data}")

        # r = requests.post(f"{API_URL}/bots/{BOT_ID}/transactions", json=data)
        r = requests.post(f"{API_URL}/transactions", json=data)
        
        if r.status_code in [200, 201]:
            response_data = r.json()
            print(">>> Transaction enregistrée dans le dashboard")
            return True
        else:
            print(f">>> Erreur API: {r.status_code} - {r.text}")
            return False
    except Exception as e:
        print(f">>> Impossible d'envoyer la transaction: {e}")
        return False

def update_status(status):
    try:
        requests.put(f"{API_URL}/bots/{BOT_ID}/status", json={"status": status})
    except:
        pass

# --- CONFIG BOT ---
def load_bot_config():
    """Récupère les paramètres configurables depuis le dashboard"""
    default = {
        "buy_price_threshold": 0.001,
        "sell_price_threshold": 0.0016,
        "buy_amount": 0.05,
        "sell_amount": 0.05,
        "slippage": 1,        # %
        # "gas_limit": 350000,
        "gas_limit": 500000,
        "gas_price": 40       # gwei
    }
    try:
        r = requests.get(f"{API_URL}/bots/{BOT_ID}", timeout=5)
        if r.status_code == 200:
            data = r.json()
            return {
                "buy_price_threshold": data.get("buy_price_threshold", default["buy_price_threshold"]),
                "sell_price_threshold": data.get("sell_price_threshold", default["sell_price_threshold"]),
                "buy_amount": data.get("buy_amount", default["buy_amount"]),
                "sell_amount": data.get("sell_amount", default["sell_amount"]),
                "slippage": data.get("slippage", default["slippage"]),
                # "gas_limit_buy": data.get("gas_limit_buy", default["gas_limit_buy"]),
                "gas_limit": data.get("gas_limit", default["gas_limit"]),
                "gas_price": data.get("gas_price", default["gas_price"])
            }
    except Exception as e:
        print(f">>> Impossible de charger config bot: {e}")
    return default

# --- FETCH PRICE ---
def get_price_kno_eur():
    try:
        response = requests.get(GECKO_TERMINAL_POOL_URL)
        response.raise_for_status()
        data = response.json()
        price_usd = float(data["data"]["attributes"]["base_token_price_usd"])
        return price_usd * 0.87
    except:
        return None

def wrap_pol(amount_pol):
    tx = token_wpol.functions.deposit().build_transaction({
        "from": wallet,
        "value": w3.to_wei(amount_pol, "ether"),
        "nonce": get_nonce(),
        "gas": 150000,
        "gasPrice": w3.eth.gas_price
    })
    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt.status == 1

def unwrap_wpol(amount_wei):
    tx = token_wpol.functions.withdraw(amount_wei).build_transaction({
        "from": wallet,
        "nonce": get_nonce(),
        "gas": 100000,
        "gasPrice": w3.eth.gas_price
    })
    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt.status == 1

# --- ACHAT / VENTE ---
def buy_kno(current_price, config):
    try:
        print(">>> Préparation de l'achat KNO...")

        # Balance WPOL
        balance_wpol = from_wei(token_wpol.functions.balanceOf(wallet).call(), 18)
        if balance_wpol < 0.01:
            print(">>> Pas assez de WPOL, wrapping 0.5 POL...")
            if not wrap_pol(0.5):
                return False
            balance_wpol = from_wei(token_wpol.functions.balanceOf(wallet).call(), 18)

        amt_decimal = min(config["buy_amount"], balance_wpol)
        amt_wei = to_wei(amt_decimal, 18)
        print(f">>> Montant WPOL à swap: {amt_decimal:.6f}")

        if not approve_token(token_wpol, ROUTER, amt_wei, "WPOL"):
            return False

        amounts = router.functions.getAmountsOut(amt_wei, [WPOL, KNO]).call()
        min_out = int(amounts[-1] * (1 - config["slippage"]/100))
        deadline = int(time.time()) + 600

        tx = router.functions.swapExactTokensForTokens(
            amt_wei,
            min_out,
            [WPOL, KNO],
            wallet,
            deadline
        ).build_transaction({
            "from": wallet,
            "nonce": get_nonce(),
            "gas": config["gas_limit"],
            "gasPrice": w3.to_wei(config["gas_price"], "gwei")
        })

        signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f">>> Swap envoyé: {w3.to_hex(tx_hash)}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        success = receipt.status == 1
        if success:
            print(">>> Achat réussi !")
            report_trade("buy", amt_decimal, current_price)
        else:
            print(">>> Achat échoué - receipt.status=0")
        return success
    except Exception as e:
        print(f">>> Erreur achat: {e}")
        return False

def sell_kno(current_price, config):
    try:
        print(">>> Début de la vente KNO...")

        old_balance_wpol = token_wpol.functions.balanceOf(wallet).call()
        balance_kno = token_kno.functions.balanceOf(wallet).call()
        balance_kno_decimal = from_wei(balance_kno, 18)

        print(f">>> Balance KNO: {balance_kno_decimal:.6f}")
        if balance_kno_decimal < 0.001:
            print(">>> Balance KNO insuffisante pour vendre")
            return False

        amt_decimal = min(config["sell_amount"], balance_kno_decimal)
        amt_wei = to_wei(amt_decimal, 18)

        if not approve_token(token_kno, ROUTER, amt_wei, "KNO"):
            return False

        amounts = router.functions.getAmountsOut(amt_wei, [KNO, WPOL]).call()
        min_out = int(amounts[-1] * (1 - config["slippage"]/100))
        deadline = int(time.time()) + 600

        tx = router.functions.swapExactTokensForTokens(
            amt_wei,
            min_out,
            [KNO, WPOL],
            wallet,
            deadline
        ).build_transaction({
            "from": wallet,
            "nonce": get_nonce(),
            "gas": config["gas_limit"],
            "gasPrice": w3.to_wei(config["gas_price"], "gwei")
        })

        signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f">>> Swap KNO → WPOL envoyé: {w3.to_hex(tx_hash)}")

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
        success = receipt.status == 1

        if success:
            print(">>> Swap KNO → WPOL réussi")
            new_balance_wpol = token_wpol.functions.balanceOf(wallet).call()
            gained_wpol = new_balance_wpol - old_balance_wpol
            print(f">>> WPOL reçus: {from_wei(gained_wpol,18):.6f}")
            unwrap_wpol(gained_wpol)
            write_price(SELL_PRICE_FILE, current_price)
            report_trade("sell", amt_decimal, current_price)
        return success
    except Exception as e:
        print(f">>> Erreur lors de la vente KNO: {e}")
        return False

# def sell_kno(current_price, config):
#     try:
#         print("🔄 Début de la vente KNO...")
        
#         # ⚠️ VÉRIFIER D'ABORD LES TRANSACTIONS EN ATTENTE
#         pending_count = w3.eth.get_transaction_count(wallet, 'pending')
#         latest_count = w3.eth.get_transaction_count(wallet, 'latest')
        
#         if pending_count > latest_count:
#             print(f"⚠️ {pending_count - latest_count} transaction(s) en attente")
#             print("💡 Attendez ou annulez les transactions avant de continuer")
#             return False

#         # Vérifier la balance
#         balance_kno = token_kno.functions.balanceOf(wallet).call()
#         balance_kno_decimal = from_wei(balance_kno, 18)
#         print(f"💰 Balance KNO: {balance_kno_decimal:.6f}")

#         if balance_kno_decimal < 0.001:
#             print("❌ Balance KNO insuffisante pour vendre")
#             return False

#         # Montant réduit pour test
#         amt_decimal = min(1.0, balance_kno_decimal)
#         amt_wei = to_wei(amt_decimal, 18)
#         print(f"💸 Montant à vendre: {amt_decimal:.2f} KNO")

#         # Approval
#         if not approve_token(token_kno, ROUTER, amt_wei, "KNO"):
#             return False

#         # Estimation du prix de sortie
#         amounts = router.functions.getAmountsOut(amt_wei, [KNO, WPOL]).call()
#         min_out = int(amounts[-1] * (1 - config["slippage"]/100))
#         print(f"📊 Min WPOL attendu: {from_wei(min_out, 18):.6f}")

#         # Gas price DYNAMIQUE et ÉLEVÉ
#         current_gas_price = w3.eth.gas_price
#         gas_price_to_use = int(current_gas_price * 1.5)  # +50% pour priorité
#         print(f"⛽ Gas price: {w3.from_wei(gas_price_to_use, 'gwei'):.0f} gwei")

#         # ⚠️ NONCE CORRECT
#         nonce = w3.eth.get_transaction_count(wallet, 'pending')
#         print(f"🔢 Nonce utilisé: {nonce}")

#         deadline = int(time.time()) + 600

#         # Construction de la transaction
#         tx = router.functions.swapExactTokensForTokens(
#             amt_wei,
#             min_out,
#             [KNO, WPOL],
#             wallet,
#             deadline
#         ).build_transaction({
#             "from": wallet,
#             "nonce": nonce,
#             "gas": config["gas_limit"],
#             "gasPrice": gas_price_to_use
#         })

#         # Signature et envoi
#         signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
#         tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
#         tx_hash_hex = w3.to_hex(tx_hash)
#         print(f"🔄 Transaction envoyée: {tx_hash_hex}")
#         print(f"🔗 PolygonScan: https://polygonscan.com/tx/{tx_hash_hex}")

#         # Attente avec timeout
#         print("⏳ Attente confirmation...")
#         receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
#         if receipt.status == 1:
#             print("✅ Vente réussie !")
#             # ... reste du code de succès ...
#             return True
#         else:
#             print("❌ Transaction échouée sur la blockchain")
#             return False

#     except Exception as e:
#         print(f"❌ Erreur vente KNO: {e}")
#         return False

# --- MAIN LOOP ---
if __name__ == "__main__":
    update_status("online")
    print(">>> Bot trading local démarré")

    # ⭐ ANNULATION DES TRANSACTIONS EN ATTENTE AU DÉMARRAGE
    print(">>> Vérification des transactions en attente...")
    cancel_pending_transactions()

    trade_count = 0
    try:
        while True:
            config = load_bot_config()
            price = get_price_kno_eur()
            if not price:
                time.sleep(60)
                continue
            last_price = read_price(PRICE_FILE)
            last_sell  = read_price(SELL_PRICE_FILE)

            buy_condition = price <= config["buy_price_threshold"] or (last_price and price <= last_price * 0.9)
            if buy_condition:
                if buy_kno(price, config):
                    trade_count += 1

            sell_condition = price >= config["sell_price_threshold"] or (last_sell and price >= last_sell * 1.1)
            if sell_condition:
                if sell_kno(price, config):
                    trade_count += 1

            write_price(PRICE_FILE, price)
            delay = random.randint(2,5)
            print(f">>> Prochain cycle dans {delay} minutes...")
            time.sleep(delay * 60)
    except KeyboardInterrupt:
        update_status("offline")
        print(">>> Bot arrêté par l'utilisateur")
