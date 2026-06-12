import aiohttp
from core.config import settings
from core.alerts import AlertManager

class RiotAPIException(Exception):
    pass

class RiotApiKeyExpiredException(RiotAPIException):
    pass

class RiotClient:
    def __init__(self):
        self.headers = {"X-Riot-Token": settings.riot_api_key}
        # Les endpoints pour les comptes et les historiques de matchs sont regionaux
        self.region_url = "https://europe.api.riotgames.com"

    async def _handle_response(self, response: aiohttp.ClientResponse):
        """Methode interne pour gerer les erreurs HTTP de maniere unifiee."""
        if response.status in (401, 403):
            await AlertManager.trigger_api_key_expiration()
            raise RiotApiKeyExpiredException()
        if response.status != 200:
            raise RiotAPIException(f"Erreur API Riot: Code {response.status}")
        return await response.json()

    async def get_puuid_by_riot_id(self, session: aiohttp.ClientSession, game_name: str, tag_line: str) -> str:
        """Etape 1 : Convertir le Pseudo#TAG en PUUID."""
        url = f"{self.region_url}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        async with session.get(url, headers=self.headers) as response:
            data = await self._handle_response(response)
            return data["puuid"]

    async def get_match_ids_by_puuid(self, session: aiohttp.ClientSession, puuid: str, count: int = 5) -> list:
        """Etape 2 : Obtenir les derniers match_ids a partir du PUUID."""
        url = f"{self.region_url}/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}"
        async with session.get(url, headers=self.headers) as response:
            return await self._handle_response(response)

    async def fetch_match_timeline(self, session: aiohttp.ClientSession, match_id: str) -> dict:
        """Etape 3 (Lourde) : Telecharger la timeline d'une partie."""
        url = f"{self.region_url}/lol/match/v5/matches/{match_id}/timeline"
        async with session.get(url, headers=self.headers) as response:
            return await self._handle_response(response)
        
    async def fetch_match_details(self, session: aiohttp.ClientSession, match_id: str) -> dict:
        url = f"{self.region_url}/lol/match/v5/matches/{match_id}"
        async with session.get(url, headers=self.headers) as response:
            return await self._handle_response(response)