# create_tables.py
from models import Base
from database import engine  # ton engine doit maintenant utiliser MySQL

# Crée toutes les tables définies dans tes modèles
Base.metadata.create_all(bind=engine)

print("✅ Toutes les tables ont été créées dans MySQL !")
