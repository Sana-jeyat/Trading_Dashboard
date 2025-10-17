import secrets

bot_token = f"bot_{secrets.token_hex(16)}"
print("Voici ton bot token :", bot_token)
