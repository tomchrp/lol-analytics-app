"""
===============================================================================
Script : build_schema.py
Description : Pipeline de profilage en deux étapes pour les données Riot Games.
              Étape 1 (Cartographe) : Extrait le schéma brut de la base de données.
              Étape 2 (Synthétiseur) : Filtre et formate les événements métiers.
Auteur : Généré automatiquement
===============================================================================
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import asyncio
from sqlalchemy import select
from core.database import AsyncSessionLocal
from core.models import RawMatchTimeline

# Liste stricte des événements vitaux pour l'analyse "Jungle Diff"
TARGET_EVENTS = [
    "ELITE_MONSTER_KILL",
    "BUILDING_KILL",
    "CHAMPION_KILL",
    "CHAMPION_SPECIAL_KILL"
]

async def profile_events():
    print("Début du Cartographe : Analyse exhaustive des parties locales...")
    schema_registry = {}

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(RawMatchTimeline))
        matches = result.scalars().all()

        if not matches:
            print("Erreur : Aucun match n'a été trouvé dans la base de données locale.")
            return

        # Étape 1 : Le Cartographe (Aspiration totale)
        for match in matches:
            timeline = match.raw_data.get("timeline", {})
            frames = timeline.get("info", {}).get("frames", [])

            for frame in frames:
                for event in frame.get("events", []):
                    event_type = event.get("type", "UNKNOWN")
                    
                    if event_type not in schema_registry:
                        schema_registry[event_type] = {
                            "keys": set(),
                            "enums": {}
                        }

                    for key, value in event.items():
                        schema_registry[event_type]["keys"].add(key)
                        
                        # Capture dynamique des énumérations et modalités
                        if isinstance(value, str) and ("Type" in key or "SubType" in key or key == "laneType" or key == "monsterType"):
                            if key not in schema_registry[event_type]["enums"]:
                                schema_registry[event_type]["enums"][key] = set()
                            schema_registry[event_type]["enums"][key].add(value)

    # Étape 2 : Le Synthétiseur (Filtrage métier)
    print("Début du Synthétiseur : Création du document métier épuré...")
    business_schema = {}
    
    for event_type, data in schema_registry.items():
        if event_type in TARGET_EVENTS:
            business_schema[event_type] = {
                "cles_detectees": sorted(list(data["keys"])),
                "modalites_possibles": {k: sorted(list(v)) for k, v in data["enums"].items()}
            }

    # Sauvegarde du document de synthèse en JSON formaté
    output_file = "synthese_jungle_diff.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(business_schema, f, indent=4, ensure_ascii=False)
        
    print(f"Succès ! Le fichier de synthèse a été généré : {output_file}")
    print(f"Il contient l'analyse croisée de {len(matches)} parties pour les événements cibles.")

if __name__ == "__main__":
    # Correction du bug de boucle d'événements asyncpg sur Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(profile_events())