import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import traceback
import asyncio
import aiohttp
from sqlalchemy import select
from arq import create_pool
from arq.connections import RedisSettings

from core.config import settings
from services.riot_client import RiotClient
from core.database import AsyncSessionLocal
from core.models import RawMatchTimeline

async def get_existing_matches(match_ids: list[str]) -> set[str]:
    """Interroge PostgreSQL pour savoir quels matchs sont deja stockes."""
    if not match_ids:
        return set()
        
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(RawMatchTimeline.match_id)
            .where(RawMatchTimeline.match_id.in_(match_ids))
        )
        return set(result.scalars().all())

async def main():
    print("=== Outil de Moissonnage Riot Games (Deep Fetch) ===")
    riot_id = input("Entrez le Riot ID (ex: Faker#T1) : ").strip()
    
    if "#" not in riot_id:
        print("Erreur : Le format doit contenir un hashtag.")
        return

    game_name, tag_line = riot_id.split("#", 1)
    
    try:
        target_new_matches = int(input("Combien de NOUVELLES parties voulez-vous ajouter a la base ? : ").strip())
        if target_new_matches <= 0:
            return
    except ValueError:
        print("Erreur : Veuillez entrer un nombre entier positif.")
        return

    print(f"\nRecherche du PUUID pour {game_name}#{tag_line}...")
    
    client = RiotClient()
    async with aiohttp.ClientSession() as session:
        try:
            puuid = await client.get_puuid_by_riot_id(session, game_name, tag_line)
            
            new_match_ids = []
            start_index = 0
            batch_size = 100  # On tire le maximum par requete pour limiter les appels API
            
            print(f"Extraction dans l'historique jusqu'a trouver {target_new_matches} parties inedites...")
            
            # Boucle de Deep Fetching
            while len(new_match_ids) < target_new_matches:
                url = f"{client.region_url}/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start_index}&count={batch_size}"
                async with session.get(url, headers=client.headers) as response:
                    batch_ids = await client._handle_response(response)
                    
                if not batch_ids:
                    print(f"Fin de l'historique atteinte. Seulement {len(new_match_ids)} nouvelles parties trouvees au total.")
                    break
                    
                # On passe le lot au filtre PostgreSQL
                existing_ids = await get_existing_matches(batch_ids)
                
                # On ajoute strictement ce qui n'est pas en base, jusqu'a atteindre la cible
                for match_id in batch_ids:
                    if match_id not in existing_ids and match_id not in new_match_ids:
                        new_match_ids.append(match_id)
                        if len(new_match_ids) == target_new_matches:
                            break  # Objectif atteint
                            
                print(f"   -> Scan des index {start_index} a {start_index + len(batch_ids)} : {len(new_match_ids)}/{target_new_matches} parties inedites trouvees.")
                start_index += batch_size
                await asyncio.sleep(0.1) # Respect du Rate Limit de l'endpoint IDS
                
            if not new_match_ids:
                print("Aucune nouvelle partie a telecharger. Votre base est a jour.")
                return
            
            print("\nConnexion a la file d'attente Redis...")
            redis_pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
            
            print("Injection des taches dans le Worker ARQ...")
            for match_id in new_match_ids:
                await redis_pool.enqueue_job('download_match_timeline_task', match_id)
                
            print("\nTermine ! Le Worker traite les donnees en arriere-plan.")
            
        except Exception:
            print("\nUne erreur critique est survenue. Voici la trace complete :")
            traceback.print_exc()
        finally:
            if 'redis_pool' in locals():
                await redis_pool.aclose()

if __name__ == "__main__":
    # Correction du bug asyncpg sur Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(main())