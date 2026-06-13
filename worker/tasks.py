"""
===============================================================================
Script : tasks.py
Description : Contient la logique métier des tâches asynchrones exécutées par 
              le Worker ARQ. Gère les appels à l'API Riot et l'insertion en base.
===============================================================================
"""

import asyncio
import aiohttp
import logging
from core.database import AsyncSessionLocal
from core.models import RawMatchTimeline
from services.riot_client import RiotClient, RiotApiKeyExpiredException

logger = logging.getLogger("LoLAnalyticsWorker")

async def download_match_timeline_task(ctx, match_id: str, queue_id: int):
    riot_client: RiotClient = ctx["riot_client"]
    session: aiohttp.ClientSession = ctx["http_session"]
    
    try:
        logger.info(f"Début du téléchargement pour le match {match_id} (File : {queue_id})")
        
        details_task = riot_client.fetch_match_details(session, match_id)
        timeline_task = riot_client.fetch_match_timeline(session, match_id)
        
        results = await asyncio.gather(details_task, timeline_task, return_exceptions=True)
        
        for res in results:
            if isinstance(res, RiotApiKeyExpiredException):
                logger.error(f"Échec de la tâche {match_id} : Clé API expirée.")
                return {"status": "failed", "reason": "API_KEY_EXPIRED"}
            elif isinstance(res, Exception):
                raise res

        combined_raw_data = {
            "details": results[0],
            "timeline": results[1]
        }
        
        async with AsyncSessionLocal() as db_session:
            timeline_record = RawMatchTimeline(
                match_id=match_id, 
                queue_id=queue_id,
                raw_data=combined_raw_data
            )
            await db_session.merge(timeline_record)
            await db_session.commit()
            
        logger.info(f"Données du match {match_id} sauvegardées avec succès.")
        
        # BRIDAGE ANTI-BAN : Pause de 2.5 secondes
        await asyncio.sleep(2.5)
        return {"status": "success", "match_id": match_id}
        
    except Exception as e:
        logger.error(f"Échec inattendu pour le match {match_id} : {str(e)}")
        await asyncio.sleep(2.5)
        return {"status": "failed", "reason": str(e)}