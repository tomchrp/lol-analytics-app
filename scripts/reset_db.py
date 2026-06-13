"""
===============================================================================
Script : reset_db.py
Description : Script d'administration destructif.
              Supprime intégralement les tables existantes dans PostgreSQL
              et les recrée selon le modèle SQLAlchemy à jour.
              À utiliser uniquement en environnement de développement.
===============================================================================
"""

import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import engine
from core.models import Base

async def reset_database():
    print("Attention : Début de la procédure de purge de la base de données...")
    
    async with engine.begin() as conn:
        print("1. Destruction des tables existantes (DROP)...")
        await conn.run_sync(Base.metadata.drop_all)
        
        print("2. Création des nouvelles tables à partir des modèles (CREATE)...")
        await conn.run_sync(Base.metadata.create_all)
        
    print("Succès : La base de données a été réinitialisée avec la nouvelle structure.")
    print("La table raw_match_timelines possède désormais la colonne queue_id.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(reset_database())