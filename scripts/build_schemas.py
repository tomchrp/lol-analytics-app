import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import asyncio
from sqlalchemy import select
from core.database import AsyncSessionLocal
from core.models import RawMatchTimeline

async def profile_events():
    schema_registry = {}

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(RawMatchTimeline))
        matches = result.scalars().all()

        if not matches:
            print("Erreur : Aucun match dans la base de donnees locale.")
            return

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
                        
                        if isinstance(value, str) and ("Type" in key or "SubType" in key or key == "laneType"):
                            if key not in schema_registry[event_type]["enums"]:
                                schema_registry[event_type]["enums"][key] = set()
                            schema_registry[event_type]["enums"][key].add(value)

    # Nettoyage pour la conversion JSON (les sets ne sont pas serialisables)
    final_schema = {}
    for event_type, data in schema_registry.items():
        final_schema[event_type] = {
            "all_detected_keys": list(data["keys"]),
            "enumerations": {k: list(v) for k, v in data["enums"].items()}
        }

    with open("riot_events_schema.json", "w", encoding="utf-8") as f:
        json.dump(final_schema, f, indent=4, ensure_ascii=False)
        
    print("Profilage termine. Fichier riot_events_schema.json genere avec succes.")

if __name__ == "__main__":
    asyncio.run(profile_events())