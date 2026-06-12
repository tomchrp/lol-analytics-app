import logging

# Configuration basique du logger pour le terminal Docker
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("LoLAnalyticsWorker")

class AlertManager:
    @staticmethod
    async def trigger_api_key_expiration():
        """
        Declenche une alerte critique indiquant que la cle API Riot a expire.
        Dans un environnement de production standalone, cela pourrait etre
        connecte a un service de monitoring externe (Sentry, Datadog).
        Pour l'instant, cela ecrit une erreur critique dans les logs du serveur.
        """
        msg = "ALERTE CRITIQUE : La cle API Riot Games est invalide ou a expire (Erreur 401/403). Le Worker est compromis."
        logger.critical(msg)