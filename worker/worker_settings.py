"""
===============================================================================
Script : worker_settings.py
Description : Point d'entrée et configuration du Worker ARQ. Déclare les 
              tâches disponibles, les hooks de démarrage et le pont Redis.
===============================================================================
"""

import aiohttp
import logging
from arq.connections import RedisSettings
from core.config import settings
from services.riot_client import RiotClient
from worker.tasks import download_match_timeline_task

logger = logging.getLogger("LoLAnalyticsWorker")

async def on_startup(ctx):
    """S'exécute au démarrage du conteneur Worker."""
    logger.info("Démarrage du Worker ARQ...")
    ctx["http_session"] = aiohttp.ClientSession()
    ctx["riot_client"] = RiotClient()

async def on_shutdown(ctx):
    """S'exécute à la fermeture du conteneur Worker."""
    logger.info("Arrêt du Worker ARQ, fermeture des sessions HTTP...")
    await ctx["http_session"].close()

class WorkerSettings:
    """Configuration lue directement par la commande arq au lancement."""
    functions = [download_match_timeline_task]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    on_startup = on_startup
    on_shutdown = on_shutdown
    max_jobs = 1  # Vital pour le respect strict du Rate Limit Riot