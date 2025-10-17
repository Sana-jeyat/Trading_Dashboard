#!/usr/bin/env python3

import time, json, random, requests, os, sys
from datetime import datetime
from dotenv import load_dotenv
from web3 import Web3
from remote_bot_client import DashboardClient

# --- CONFIGURATION ---
dotenv_path = os.path.join(os.path.dirname(__file__), "../backend/.env")
load_dotenv(dotenv_path)
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")

if not PRIVATE_KEY or not WALLET_ADDRESS:
    print("❌ Missing PRIVATE_KEY or WALLET_ADDRESS")
    sys.exit(1)


class BotWPOLKNO:
    def __init__(self):
        # Dashboard
        self.dashboard = DashboardClient(
            api_url="http://127.0.0.1:8000",
            bot_token="bot_bot-1760622169050_mgthajo2",
            bot_id="2"
        )

        # Web3
        self.w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
        if not self.w3.is_connected():
            print("❌ Erreur de connexion à Polygon")
            sys.exit(1)
        self.wallet = self.w3.to_checksum_address(WALLET_ADDRESS)

        # Contrats
        self.WPOL = self.w3.to_checksum_address("0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270")
        self.KNO  = self.w3.to_checksum_address("0x236fbfAa3Ec9E0B9BA013Df370c098bAd85aD631")
        self.ROUTER = self.w3.to_checksum_address("0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff")

        # ABIs
        self.erc20_abi = json.loads("""[
            {"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},
            {"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"success","type":"bool"}],"type":"function"},
            {"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
            {"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"remaining","type":"uint256"}],"type":"function"},
            {"constant":false,"inputs":[],"name":"deposit","outputs":[],"stateMutability":"payable","type":"function"},
            {"constant":false,"inputs":[{"name":"wad","type":"uint256"}],"name":"withdraw","outputs":[],"stateMutability":"nonpayable","type":"function"}
        ]""")

        self.router_abi = json.loads("""[
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

        # Contrats
        self.token_wpol = self.w3.eth.contract(address=self.WPOL, abi=self.erc20_abi)
        self.token_kno  = self.w3.eth.contract(address=self.KNO,  abi=self.erc20_abi)
        self.router     = self.w3.eth.contract(address=self.ROUTER, abi=self.router_abi)

        # Fichiers
        self.PRICE_FILE = "last_price.txt"
        self.SELL_PRICE_FILE = "last_sell_price.txt"

        # Paramètres dynamiques
        self.buy_threshold = 0.001
        self.sell_threshold = 0.0014
        self.buy_percentage_drop = 10
        self.sell_percentage_gain = 10
        self.random_trades_count = 20
        self.trading_duration_hours = 24
        self.MIN_SWAP_AMOUNT = 0.001  # KNO minimum pour swap

    # ---------- UTILS ----------
    def to_wei(self, amount, decimals=18):
        return int(amount * 10**decimals)

    def from_wei(self, amount, decimals=18):
        return float(amount) / 10**decimals

    def get_nonce(self):
        return self.w3.eth.get_transaction_count(self.wallet)

    def read_price(self, file):
        try:
            with open(file, "r") as f:
                return float(f.read())
        except:
            return None

    def write_price(self, file, price):
        with open(file, "w") as f:
            f.write(str(float(price)))

    # ---------- DASHBOARD ----------
    def update_config_from_dashboard(self):
        try:
            config = self.dashboard.get_bot_config()
            if config:
                self.buy_threshold = config.get('buy_price_threshold', self.buy_threshold)
                self.sell_threshold = config.get('sell_price_threshold', self.sell_threshold)
                self.buy_percentage_drop = config.get('buy_percentage_drop', self.buy_percentage_drop)
                self.sell_percentage_gain = config.get('sell_percentage_gain', self.sell_percentage_gain)
                self.random_trades_count = config.get('random_trades_count', self.random_trades_count)
                self.trading_duration_hours = config.get('trading_duration_hours', self.trading_duration_hours)
                print("🔄 Config Dashboard mise à jour")
        except Exception as e:
            print(f"❌ Erreur config Dashboard: {e}")

    # ---------- PRIX ----------
    def get_price_kno_eur(self):
        try:
            url = "https://api.geckoterminal.com/api/v2/networks/polygon_pos/pools/0xdce471c5fc17879175966bea3c9fe0432f9b189e"
            resp = requests.get(url)
            resp.raise_for_status()
            data = resp.json()
            price_usd = float(data["data"]["attributes"]["base_token_price_usd"])
            return price_usd * 0.87
        except Exception as e:
            print(f"❌ Erreur récupération prix: {e}")
            return None

    # ---------- ACHAT / VENTE ----------
    def approve_token(self, token_contract, spender, amount, token_name):
        try:
            if token_contract.functions.allowance(self.wallet, spender).call() >= amount:
                return True
            tx = token_contract.functions.approve(spender, amount).build_transaction({
                "from": self.wallet,
                "nonce": self.get_nonce(),
                "gas": 200000,
                "gasPrice": self.w3.eth.gas_price
            })
            signed = self.w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            return True
        except Exception as e:
            print(f"❌ Erreur approve {token_name}: {e}")
            return False

    def wrap_pol(self, amount_pol):
        try:
            tx = self.token_wpol.functions.deposit().build_transaction({
                "from": self.wallet,
                "value": self.w3.to_wei(amount_pol, "ether"),
                "nonce": self.get_nonce(),
                "gas": 150000,
                "gasPrice": self.w3.eth.gas_price
            })
            signed = self.w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            return True
        except Exception as e:
            print(f"❌ Erreur wrap POL: {e}")
            return False

    def unwrap_wpol(self, amount_wei):
        try:
            tx = self.token_wpol.functions.withdraw(amount_wei).build_transaction({
                "from": self.wallet,
                "nonce": self.get_nonce(),
                "gas": 100000,
                "gasPrice": self.w3.eth.gas_price
            })
            signed = self.w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            return True
        except Exception as e:
            print(f"❌ Erreur unwrap WPOL: {e}")
            return False

    def buy_kno(self, current_price):
        try:
            print("🔍 Préparation de l'achat KNO...")

            # Balance WPOL
            balance_wpol = self.from_wei(self.token_wpol.functions.balanceOf(self.wallet).call(), 18)
            if balance_wpol < 0.01:
                print("⚠️ Pas assez de WPOL, wrapping 0.5 POL...")
                if not self.wrap_pol(0.5):
                    return False
                balance_wpol = self.from_wei(self.token_wpol.functions.balanceOf(self.wallet).call(), 18)

            amt_decimal = min(balance_wpol * 0.05 * random.uniform(0.8, 1.2), 0.05)
            amt_wei = self.to_wei(amt_decimal, 18)
            print(f"💰 Montant WPOL à swap: {amt_decimal:.6f}")

            if not self.approve_token(self.token_wpol, self.ROUTER, amt_wei, "WPOL"):
                return False

            amounts = self.router.functions.getAmountsOut(amt_wei, [self.WPOL, self.KNO]).call()
            min_out = int(amounts[-1] * 0.9)
            deadline = int(time.time()) + 600

            print(f"📈 Estimation sortie: {self.from_wei(amounts[-1],18):.6f} KNO (min {self.from_wei(min_out,18):.6f})")

            tx = self.router.functions.swapExactTokensForTokens(
                amt_wei,
                min_out,
                [self.WPOL, self.KNO],
                self.wallet,
                deadline
            ).build_transaction({
                "from": self.wallet,
                "nonce": self.get_nonce(),
                "gas": 350000,
                "gasPrice": self.w3.eth.gas_price
            })

            signed = self.w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            print(f"🔄 Swap envoyé: {self.w3.to_hex(tx_hash)}")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt.status == 1:
                print("✅ Achat réussi !")
                return True
            else:
                print("❌ Achat échoué - receipt.status=0")
                return False

        except Exception as e:
            print(f"❌ Erreur achat: {e}")
            return False

    def sell_kno(self, current_price):
        try:
            print("🔄 Début de la vente KNO...")

            old_balance_wpol = self.token_wpol.functions.balanceOf(self.wallet).call()
            balance_kno = self.token_kno.functions.balanceOf(self.wallet).call()
            balance_kno_decimal = self.from_wei(balance_kno, 18)

            print(f"💰 Balance KNO: {balance_kno_decimal:.6f}")
            if balance_kno_decimal < self.MIN_SWAP_AMOUNT:
                print("❌ Balance KNO insuffisante pour vendre")
                return False

            max_kno = balance_kno_decimal * 0.05  # fallback
            try:
                max_kno = self.from_wei(
                    self.router.functions.getAmountsOut(
                        self.to_wei(0.05, 18), [self.WPOL, self.KNO]
                    ).call()[-1], 18
                )
            except Exception as e:
                print(f"⚠️ Erreur calcul max_kno, fallback utilisé: {e}")

            amt_decimal = random.uniform(0, min(2, balance_kno_decimal))
            amt_decimal = min(amt_decimal, max_kno, balance_kno_decimal)
            print(f"🔄 Montant à vendre: {amt_decimal:.6f} KNO")

            amt_wei = self.to_wei(amt_decimal, 18)

            if not self.approve_token(self.token_kno, self.ROUTER, amt_wei, "KNO"):
                return False

            amounts = self.router.functions.getAmountsOut(amt_wei, [self.KNO, self.WPOL]).call()
            min_out = int(amounts[-1] * 0.8)
            deadline = int(time.time()) + 600

            tx = self.router.functions.swapExactTokensForTokens(
                amt_wei,
                min_out,
                [self.KNO, self.WPOL],
                self.wallet,
                deadline
            ).build_transaction({
                "from": self.wallet,
                "nonce": self.get_nonce(),
                "gas": 500000,
                "gasPrice": self.w3.eth.gas_price
            })

            signed = self.w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            print(f"🔄 Swap KNO → WPOL envoyé: {self.w3.to_hex(tx_hash)}")

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
            if receipt.status != 1:
                print("❌ Swap KNO → WPOL échoué")
                return False

            print("✅ Swap KNO → WPOL réussi")
            new_balance_wpol = self.token_wpol.functions.balanceOf(self.wallet).call()
            gained_wpol = new_balance_wpol - old_balance_wpol
            print(f"💰 WPOL reçus: {self.from_wei(gained_wpol,18):.6f}")

            if self.unwrap_wpol(gained_wpol):
                new_balance_pol = self.w3.eth.get_balance(self.wallet)
                print(f"💰 Nouvelle balance POL: {self.w3.from_wei(new_balance_pol, 'ether'):.6f}")
            else:
                print("⚠️ Unwrap WPOL échoué, WPOL reste dans le wallet")

            self.write_price(self.SELL_PRICE_FILE, current_price)
            print("✅ Vente terminée et prix sauvegardé")
            return True

        except Exception as e:
            print(f"❌ Erreur lors de la vente KNO: {e}")
            return False

    # ---------- LOOP ----------
    def run(self):
        print(f"👛 Wallet: {self.wallet}")
        self.dashboard.connect()
        trade_count = 0
        while True:
            self.update_config_from_dashboard()
            price = self.get_price_kno_eur()
            if not price:
                time.sleep(60)
                continue

            last_price = self.read_price(self.PRICE_FILE)
            last_sell  = self.read_price(self.SELL_PRICE_FILE)

            # Conditions achat
            if price < self.buy_threshold or (last_price and price <= last_price * 0.9):
                if self.buy_kno(price):
                    trade_count += 1
                    self.dashboard.send_transaction("buy", None, price)

            # Conditions vente
            if price > self.sell_threshold or (last_sell and price >= last_sell * 1.1):
                if self.sell_kno(price):
                    trade_count += 1
                    self.dashboard.send_transaction("sell", None, price)

            self.write_price(self.PRICE_FILE, price)
            delay = random.randint(2,5)
            print(f"⏰ Prochain cycle dans {delay} minutes...")
            time.sleep(delay*60)


# ========== LANCEMENT ==========
if __name__ == "__main__":
    bot = BotWPOLKNO()
    bot.run()
