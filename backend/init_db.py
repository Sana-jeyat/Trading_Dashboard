from database import Base, engine
from models import User, Bot, Transaction  # importe tous tes modèles ici

# Crée toutes les tables définies dans Base
Base.metadata.create_all(bind=engine)

print("✅ Toutes les tables ont été créées dans la base de données !")
