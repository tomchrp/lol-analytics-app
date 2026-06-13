"""
===============================================================================
Script : 1_cartographe.py
Description : Outil modulaire d'exploration et de profilage des schémas JSON 
              de l'API Riot. Échantillonne les données en base et génère 
              une encyclopédie incrémentale sans écraser les données existantes.
===============================================================================
"""

import sys
import os
import json
import argparse
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import AsyncSessionLocal
from core.models import RawMatchTimeline

MAX_ENUM_VALUES = 40

def merge_profiles(target, source):
    """Fusionne récursivement deux profils de schéma."""
    for key, source_val in source.items():
        if key not in target:
            target[key] = source_val
            continue
            
        target_val = target[key]
        
        # Fusion des types
        if isinstance(source_val, dict) and 'types' in source_val:
            for t in source_val['types']:
                if t not in target_val['types']:
                    target_val['types'].append(t)
            
            # Mise a jour des min/max
            if 'min' in source_val and ('min' not in target_val or source_val['min'] < target_val['min']):
                target_val['min'] = source_val['min']
            if 'max' in source_val and ('max' not in target_val or source_val['max'] > target_val['max']):
                target_val['max'] = source_val['max']
                
            # Gestion intelligente des enumerations (textes)
            if 'enumerations' in source_val and 'enumerations' in target_val:
                if target_val['enumerations'] is not None:
                    merged_enums = set(target_val['enumerations']).union(set(source_val['enumerations']))
                    if len(merged_enums) > MAX_ENUM_VALUES:
                        # Si trop de valeurs uniques (ex: puuid, itemIds en string), on desactive l'enumeration
                        target_val['enumerations'] = None
                    else:
                        target_val['enumerations'] = sorted(list(merged_enums))
        
        # Cas des dictionnaires imbriques
        elif isinstance(source_val, dict):
            merge_profiles(target_val, source_val)

def profile_value(value):
    """Analyse une valeur brute et retourne son profil structurel."""
    val_type = type(value).__name__
    
    if val_type == 'dict':
        profile = {}
        for k, v in value.items():
            profile[k] = profile_value(v)
        return profile
    
    elif val_type == 'list':
        # On profile le contenu de la liste de maniere unifiee
        list_profile = {"types": ["list"]}
        if value:
            # Pour simplifier, on profile le premier element non nul si c'est un dict
            sample_item = next((item for item in value if item is not None), None)
            if isinstance(sample_item, dict):
                list_profile["item_schema"] = profile_value(sample_item)
        return list_profile
    
    else:
        profile = {"types": [val_type]}
        if val_type in ('int', 'float'):
            profile['min'] = value
            profile['max'] = value
        elif val_type == 'str':
            profile['enumerations'] = [value]
        return profile

async def extract_and_profile(api, schema_type, limit):
    """Requête la base de données, extrait le sous-arbre et génère le profil."""
    print(f"Demarrage du profilage : API={api}, Type={schema_type}, Limite={limit} parties.")
    
    schema_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "schemas", api)
    os.makedirs(schema_dir, exist_ok=True)
    schema_file = os.path.join(schema_dir, f"{schema_type}.json")
    
    # Chargement du schema existant pour fusion incrémentale
    master_schema = {}
    if os.path.exists(schema_file):
        with open(schema_file, 'r', encoding='utf-8') as f:
            try:
                master_schema = json.load(f)
                print(f"Schema existant charge depuis {schema_file}")
            except json.JSONDecodeError:
                print("Le fichier existant est corrompu, depart a zero.")

    async with AsyncSessionLocal() as session:
        # On recupere les N parties les plus recentes
        query = select(RawMatchTimeline.raw_data).order_by(RawMatchTimeline.fetched_at.desc()).limit(limit)
        result = await session.execute(query)
        raw_matches = result.scalars().all()
        
    if not raw_matches:
        print("Aucune donnee trouvee dans la base de donnees.")
        return

    print(f"Analyse de {len(raw_matches)} parties en cours...")

    for raw_data in raw_matches:
        if schema_type == "timeline_events":
            frames = raw_data.get('timeline', {}).get('info', {}).get('frames', [])
            for frame in frames:
                for event in frame.get('events', []):
                    event_type = event.get('type', 'UNKNOWN_EVENT')
                    if event_type not in master_schema:
                        master_schema[event_type] = {"keys_profile": {}}
                    event_profile = profile_value(event)
                    merge_profiles(master_schema[event_type]["keys_profile"], event_profile)

        elif schema_type == "timeline_frames":
            if "timeline_frames" not in master_schema:
                master_schema["timeline_frames"] = {"keys_profile": {}}
            frames = raw_data.get('timeline', {}).get('info', {}).get('frames', [])
            for frame in frames:
                participant_frames = frame.get('participantFrames', {})
                for p_id, p_frame in participant_frames.items():
                    frame_profile = profile_value(p_frame)
                    merge_profiles(master_schema["timeline_frames"]["keys_profile"], frame_profile)

        elif schema_type == "match_details":
            if "match_details" not in master_schema:
                master_schema["match_details"] = {"keys_profile": {}}
            participants = raw_data.get('details', {}).get('info', {}).get('participants', [])
            for participant in participants:
                participant_profile = profile_value(participant)
                merge_profiles(master_schema["match_details"]["keys_profile"], participant_profile)

    # Nettoyage des enumerations annulees (None) avant sauvegarde
    def clean_null_enums(d):
        if isinstance(d, dict):
            if 'enumerations' in d and d['enumerations'] is None:
                del d['enumerations']
            for k, v in d.items():
                clean_null_enums(v)
                
    clean_null_enums(master_schema)

    with open(schema_file, 'w', encoding='utf-8') as f:
        json.dump(master_schema, f, indent=4, ensure_ascii=False)
        
    print(f"Succes : Profil sauvegarde dans {schema_file}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    parser = argparse.ArgumentParser(description="Cartographe API Riot")
    parser.add_argument("--api", required=True, choices=["match_v5", "summoner_v4"], help="L'API a analyser")
    parser.add_argument("--type", required=True, choices=["timeline_events", "timeline_frames", "match_details"], help="Le sous-arbre de donnees cible")
    parser.add_argument("--limit", type=int, default=50, help="Nombre de matchs recents a analyser")
    
    args = parser.parse_args()
    
    asyncio.run(extract_and_profile(args.api, args.type, args.limit))