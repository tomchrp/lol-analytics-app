import aiohttp
import logging
import asyncio
from arq.connections import RedisSettings
from core.config import settings
from core.database import AsyncSessionLocal
from core.models import RawMatchTimeline
from services.riot_client import RiotClient, RiotApiKeyExpiredException

logger = logging.getLogger("LoLAnalyticsWorker")

async def on_startup(ctx):
    """S'execute au demarrage du conteneur Worker."""
    logger.info("Demarrage du Worker ARQ...")
    ctx["http_session"] = aiohttp.ClientSession()
    ctx["riot_client"] = RiotClient()

async def on_shutdown(ctx):
    """S'execute a la fermeture du conteneur Worker."""
    logger.info("Arret du Worker ARQ, fermeture des sessions HTTP...")
    await ctx["http_session"].close()

async def download_match_timeline_task(ctx, match_id: str):
    riot_client: RiotClient = ctx["riot_client"]
    session: aiohttp.ClientSession = ctx["http_session"]
    
    try:
        logger.info(f"Debut du telechargement complet pour le match {match_id}")
        
        details_task = riot_client.fetch_match_details(session, match_id)
        timeline_task = riot_client.fetch_match_timeline(session, match_id)
        
        results = await asyncio.gather(details_task, timeline_task, return_exceptions=True)
        
        for res in results:
            if isinstance(res, RiotApiKeyExpiredException):
                logger.error(f"Echec de la tache {match_id} : Cle API expiree.")
                return {"status": "failed", "reason": "API_KEY_EXPIRED"}
            elif isinstance(res, Exception):
                raise res

        match_details = results[0]
        match_timeline = results[1]
        
        combined_raw_data = {
            "details": match_details,
            "timeline": match_timeline
        }
        
        async with AsyncSessionLocal() as db_session:
            timeline_record = RawMatchTimeline(match_id=match_id, raw_data=combined_raw_data)
            await db_session.merge(timeline_record)
            await db_session.commit()
            
        logger.info(f"Donnees completes du match {match_id} sauvegardees.")
        
        # BRIDAGE ANTI-BAN : Pause de 2.5 secondes pour respecter le quota Riot (100 req / 2 min)
        await asyncio.sleep(2.5)
        
        return {"status": "success", "match_id": match_id}
        
    except Exception as e:
        logger.error(f"Echec inattendu pour le match {match_id} : {str(e)}")
        # Pause meme en cas d'erreur pour eviter de spammer l'API en boucle
        await asyncio.sleep(2.5)
        return {"status": "failed", "reason": str(e)}

class WorkerSettings:
    """Configuration lue directement par la commande arq."""
    functions = [download_match_timeline_task]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    on_startup = on_startup
    on_shutdown = on_shutdown