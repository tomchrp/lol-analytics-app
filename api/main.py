from fastapi import FastAPI, HTTPException
from arq import create_pool
from arq.connections import RedisSettings
import aiohttp

from core.config import settings
from sqlalchemy import select
from core.database import engine, Base, AsyncSessionLocal
from core.models import RawMatchTimeline  # L'import indispensable
from services.riot_client import RiotClient, RiotAPIException

app = FastAPI(
    title="LoL Analytics API", 
    description="Backend standalone pour l'analyse de données League of Legends",
    version="0.1.0"
)

redis_pool = None

# Cache statique récupéré de ton ancien projet
cache = {"version": None, "champions": {}}

@app.on_event("startup")
async def startup_event():
    """Initialisation de la base, de Redis et du cache Data Dragon."""
    global redis_pool
    
    # 1. Initialisation DB & Redis
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    redis_pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    
    # 2. Mise en cache de Data Dragon (Inspiré de ton ancien main.py)
    try:
        async with aiohttp.ClientSession() as client:
            async with client.get("https://ddragon.leagueoflegends.com/api/versions.json") as v_resp:
                versions = await v_resp.json()
                latest = versions[0]
                
            champ_url = f"https://ddragon.leagueoflegends.com/cdn/{latest}/data/fr_FR/champion.json"
            async with client.get(champ_url) as c_resp:
                c_data = await c_resp.json()
                
            cache["version"] = latest
            cache["champions"] = c_data["data"]
            print(f"✅ Données LoL à jour (Version {latest})")
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de Data Dragon : {e}")

@app.on_event("shutdown")
async def shutdown_event():
    if redis_pool:
        await redis_pool.close()

# --- ROUTES ADAPTÉES DE TON ANCIEN PROJET (Pour React) ---

@app.get("/api/v1/search")
async def universal_search(q: str):
    """
    Redirige intelligemment vers un champion ou un joueur.
    Au lieu d'un RedirectResponse HTML, on renvoie une instruction de routage pour React.
    """
    query = q.strip()

    if "#" in query:
        name, tag = query.split("#", 1)
        # React utilisera cette URL pour changer de page
        return {"type": "player", "action": f"/stats/{name}/{tag.replace('#','')}"}

    for champ_id in cache["champions"]:
        if query.lower() == champ_id.lower():
            return {"type": "champion", "action": f"/champion/{champ_id}"}

    raise HTTPException(status_code=404, detail="Aucun joueur ou champion correspondant.")


@app.get("/api/v1/stats/{game_name}/{tag_line}")
async def display_player_stats(game_name: str, tag_line: str):
    """
    Récupère le PUUID et la liste des derniers matchs.
    Optimisation : On ne fait plus de asyncio.gather sur 20 matchs pour éviter le ban API.
    """
    client = RiotClient()
    async with aiohttp.ClientSession() as session:
        try:
            puuid = await client.get_puuid_by_riot_id(session, game_name, tag_line)
            # On récupère les IDs. React fera ensuite appel à la route d'analyse pour chaque match.
            match_ids = await client.get_match_ids_by_puuid(session, puuid, count=5)
            
            return {
                "player": f"{game_name}#{tag_line}",
                "puuid": puuid,
                "matches": match_ids,
                "version": cache["version"]
            }
        except RiotAPIException as e:
            raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/champion/{champion_name}")
async def champion_detail(champion_name: str):
    """Renvoie les données statiques d'un champion depuis le cache."""
    champ = cache["champions"].get(champion_name)
    if not champ:
        raise HTTPException(status_code=404, detail="Champion non trouvé")
    
    return {
        "name": champion_name,
        "data": champ,
        "version": cache["version"]
    }


# --- ROUTE DU WORKER (Big Data / Timeline) ---

@app.post("/api/v1/matches/{match_id}/analyze")
async def analyze_match(match_id: str):
    """Délègue le téléchargement lourd de la timeline au Worker ARQ."""
    if not redis_pool:
        raise HTTPException(status_code=500, detail="Service de file d'attente indisponible")
        
    job = await redis_pool.enqueue_job('download_match_timeline_task', match_id)
    if not job:
        raise HTTPException(status_code=500, detail="Impossible de créer la tâche")
    
    return {
        "status": "pending",
        "match_id": match_id,
        "job_id": job.job_id
    }

@app.get("/api/v1/matches/{match_id}/debug/explore")
async def explore_match_data(match_id: str):
    """
    Explore les données brutes stockées dans PostgreSQL.
    Extrait la table de traduction des joueurs et les types d'événements de la timeline.
    """
    async with AsyncSessionLocal() as session:
        # Requête SQL asynchrone pour récupérer le match dans PostgreSQL
        result = await session.execute(
            select(RawMatchTimeline).where(RawMatchTimeline.match_id == match_id)
        )
        record = result.scalar_one_or_none()
        
        if not record:
            raise HTTPException(status_code=404, detail="Match non trouvé en base. Lancez l'analyse POST d'abord.")
            
        raw_data = record.raw_data
        details = raw_data.get("details", {})
        timeline = raw_data.get("timeline", {})
        
        # 1. Construction de la table de traduction (Participant ID -> Joueur/Champion)
        participants_map = {}
        for p in details.get("info", {}).get("participants", []):
            participants_map[p["participantId"]] = {
                "riot_id": f"{p.get('riotIdGameName', 'Inconnu')}#{p.get('riotIdTagline', '')}",
                "champion": p["championName"],
                "role": p["teamPosition"]
            }
            
        # 2. Exploration de la timeline
        event_types = set()
        jungle_events_sample = []
        
        for frame in timeline.get("info", {}).get("frames", []):
            for event in frame.get("events", []):
                event_types.add(event["type"])
                
                # Capture d'un échantillon d'événements liés à la jungle
                if event["type"] in ["ELITE_MONSTER_KILL", "BUILDING_KILL"]:
                    jungle_events_sample.append(event)
                    
        return {
            "match_id": match_id,
            "participants": participants_map,
            "unique_event_types": list(event_types),
            "jungle_and_objectives_sample": jungle_events_sample
        }