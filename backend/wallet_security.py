from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class WalletSecurity:
    def __init__(self, master_password: Optional[str] = None):
        """
        Gestionnaire de sécurité pour les clés privées des wallets
        
        Args:
            master_password: Mot de passe maître pour le chiffrement
        """
        self.master_password = master_password or os.getenv("WALLET_MASTER_PASSWORD", "default-change-this")
        self.salt = b'stable_salt_for_wallets'  # En production, utilisez un salt unique par utilisateur
        
    def _get_encryption_key(self) -> bytes:
        """Génère une clé de chiffrement à partir du mot de passe maître"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_password.encode()))
        return key
    
    def encrypt_private_key(self, private_key: str) -> str:
        """
        Chiffre une clé privée
        
        Args:
            private_key: Clé privée en clair
            
        Returns:
            Clé privée chiffrée (base64)
        """
        if not private_key:
            return ""
            
        try:
            key = self._get_encryption_key()
            fernet = Fernet(key)
            
            # Chiffrer la clé privée
            encrypted_key = fernet.encrypt(private_key.encode())
            
            # Encoder en base64 pour stockage
            return base64.urlsafe_b64encode(encrypted_key).decode()
            
        except Exception as e:
            logger.error(f"Erreur lors du chiffrement de la clé privée: {str(e)}")
            raise Exception("Erreur de chiffrement")
    
    def decrypt_private_key(self, encrypted_private_key: str) -> str:
        """
        Déchiffre une clé privée
        
        Args:
            encrypted_private_key: Clé privée chiffrée (base64)
            
        Returns:
            Clé privée en clair
        """
        if not encrypted_private_key:
            return ""
            
        try:
            key = self._get_encryption_key()
            fernet = Fernet(key)
            
            # Décoder depuis base64
            encrypted_data = base64.urlsafe_b64decode(encrypted_private_key.encode())
            
            # Déchiffrer
            decrypted_key = fernet.decrypt(encrypted_data)
            
            return decrypted_key.decode()
            
        except Exception as e:
            logger.error(f"Erreur lors du déchiffrement de la clé privée: {str(e)}")
            raise Exception("Erreur de déchiffrement")
    
    def validate_wallet_address(self, address: str) -> bool:
        """Valide le format d'une adresse de wallet"""
        if not address:
            return False
        
        # Format Ethereum/Polygon (0x + 40 caractères hexadécimaux)
        if len(address) == 42 and address.startswith('0x'):
            try:
                int(address[2:], 16)  # Vérifier que c'est bien hexadécimal
                return True
            except ValueError:
                return False
        
        return False
    
    def validate_private_key(self, private_key: str) -> bool:
        """Valide le format d'une clé privée"""
        if not private_key:
            return False
        
        # Supprimer le préfixe 0x si présent
        if private_key.startswith('0x'):
            private_key = private_key[2:]
        
        # Doit faire 64 caractères hexadécimaux
        if len(private_key) == 64:
            try:
                int(private_key, 16)
                return True
            except ValueError:
                return False
        
        return False
    
    def generate_wallet_config(self, bot_config: dict) -> dict:
        """
        Génère la configuration wallet pour le bot distant
        
        Args:
            bot_config: Configuration du bot avec clé privée déchiffrée
            
        Returns:
            Configuration wallet pour le bot
        """
        return {
            "wallet_address": bot_config.get("wallet_address"),
            "wallet_private_key": bot_config.get("wallet_private_key"),  # Déjà déchiffrée
            "rpc_endpoint": bot_config.get("rpc_endpoint", "https://polygon-rpc.com"),
            "contract_address": bot_config.get("contract_address"),
            "slippage_tolerance": bot_config.get("slippage_tolerance", 1.0),
            "gas_limit": bot_config.get("gas_limit", 300000),
            "gas_price": bot_config.get("gas_price", 30)
        }

# Instance globale
wallet_security = WalletSecurity()