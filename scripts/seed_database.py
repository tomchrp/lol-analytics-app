"""
===============================================================================
Script : seed_database.py
Description : Outil de Moissonnage ciblé (Faille de l'Invocateur).
              Exclut l'ARAM et les modes alternatifs.
              Transmet dynamiquement le queue_id au Worker ARQ.
===============================================================================
"""

import sys
import os
import traceback
import asyncio
import aiohttp
from sqlalchemy import select
from arq import create_pool
from arq.connections import RedisSettings

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings
from services.riot_client import RiotClient
from core.database import AsyncSessionLocal
from core.models import RawMatchTimeline

# Dictionnaire des files autorisées (Faille de l'Invocateur uniquement)
TARGET_QUEUES = {
    420: "Classé Solo/Duo",
    440: "Classé Flex",
    400: "Draft Normal"
}

async def get_existing_matches(match_ids: list[str]) -> set[str]:
    if not match_ids:
        return set()
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(RawMatchTimeline.match_id)
            .where(RawMatchTimeline.match_id.in_(match_ids))
        )
        return set(result.scalars().all())

async def main():
    print("=== Outil de Moissonnage Faille de l'Invocateur ===")
    riot_id = input("Entrez le Riot ID (ex: Faker#T1) : ").strip()
    
    if "#" not in riot_id:
        print("Erreur : Le format doit contenir un hashtag.")
        return

    game_name, tag_line = riot_id.split("#", 1)
    
    try:
        target_per_queue = int(input("Combien de NOUVELLES parties voulez-vous ajouter PAR FILE ? : ").strip())
        if target_per_queue <= 0:
            return
    except ValueError:
        print("Erreur : Veuillez entrer un nombre entier positif.")
        return

    print(f"\nRecherche du PUUID pour {game_name}#{tag_line}...")
    
    client = RiotClient()
    redis_pool = None
    
    async with aiohttp.ClientSession() as session:
        try:
            puuid = await client.get_puuid_by_riot_id(session, game_name, tag_line)
            redis_pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
            
            total_tasks_injected = 0

            # Itération sur chaque mode de jeu ciblé
            for queue_id, queue_name in TARGET_QUEUES.items():
                print(f"\n--- Scan de la file : {queue_name} (ID: {queue_id}) ---")
                
                new_match_ids = []
                start_index = 0
                batch_size = 100
                
                while len(new_match_ids) < target_per_queue:
                    # Ajout du paramètre &queue= au endpoint Riot
                    url = f"{client.region_url}/lol/match/v5/matches/by-puuid/{puuid}/ids?queue={queue_id}&start={start_index}&count={batch_size}"
                    
                    async with session.get(url, headers=client.headers) as response:
                        batch_ids = await client._handle_response(response)
                        
                    if not batch_ids:
                        print(f"   -> Fin de l'historique atteinte pour ce mode.")
                        break
                        
                    existing_ids = await get_existing_matches(batch_ids)
                    
                    for match_id in batch_ids:
                        if match_id not in existing_ids and match_id not in new_match_ids:
                            new_match_ids.append(match_id)
                            if len(new_match_ids) == target_per_queue:
                                break
                                
                    print(f"   -> Index {start_index} à {start_index + len(batch_ids)} : {len(new_match_ids)}/{target_per_queue} parties inédites.")
                    start_index += batch_size
                    await asyncio.sleep(0.1)
                
                if new_match_ids:
                    for match_id in new_match_ids:
                        # Injection de la tâche avec le queue_id comme second argument
                        await redis_pool.enqueue_job('download_match_timeline_task', match_id, queue_id)
                    total_tasks_injected += len(new_match_ids)
                    print(f"   -> {len(new_match_ids)} tâches envoyées au Worker.")
                else:
                    print("   -> Base déjà à jour pour cette file.")

            print(f"\nTerminé ! {total_tasks_injected} nouvelles parties au total sont en cours de traitement.")
            
        except Exception:
            print("\nUne erreur critique est survenue. Voici la trace complète :")
            traceback.print_exc()
        finally:
            if redis_pool:
                await redis_pool.aclose()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())