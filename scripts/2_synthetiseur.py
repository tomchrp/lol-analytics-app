"""
===============================================================================
Script : 2_synthetiseur.py
Description : Phase 2 du Data Pipeline.
              Lit l'encyclopédie statistique générée par le cartographe
              et extrait les événements cibles pour modélisation.
===============================================================================
"""

import os
import json

TARGET_EVENTS = [
    "ELITE_MONSTER_KILL",
    "BUILDING_KILL",
    "CHAMPION_KILL",
    "CHAMPION_SPECIAL_KILL"
]

def run_synthetiseur():
    print("Début du Synthétiseur : Lecture du schéma statistique...")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_file_path = os.path.join(base_dir, "schemas", "raw_riot_schema.json")
    output_file_path = os.path.join(base_dir, "schemas", "synthese_jungle_diff.json")
    
    if not os.path.exists(raw_file_path):
        print("Erreur : Le fichier brut est introuvable.")
        return

    with open(raw_file_path, "r", encoding="utf-8") as f:
        raw_schema = json.load(f)

    business_schema = {}
    
    for event_type in TARGET_EVENTS:
        if event_type in raw_schema:
            business_schema[event_type] = raw_schema[event_type]
        else:
            print(f"Avertissement : L'événement '{event_type}' n'a pas été trouvé.")

    with open(output_file_path, "w", encoding="utf-8") as f:
        json.dump(business_schema, f, indent=4, ensure_ascii=False)
        
    print(f"Succès ! Le fichier de synthèse a été mis à jour : {output_file_path}")

if __name__ == "__main__":
    run_synthetiseur()