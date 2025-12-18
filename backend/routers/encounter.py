import uuid
import random
from fastapi import APIRouter, HTTPException
from db import get_db

router = APIRouter()

# encounter_id -> { player_id, pokemons: {uid: data} }
ENCOUNTER_POOL = {}

# ===============================
# 进入地图
# ===============================
@router.get("/map")
def enter_encounter_map(player_id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name_cn, rarity
        FROM pokemon_species
        ORDER BY RAND()
        LIMIT 50
    """)
    candidates = cursor.fetchall()
    conn.close()

    if not candidates:
        raise HTTPException(500, "宝可梦数据为空")

    weights = [1 / max(1, c["rarity"]) for c in candidates]
    chosen = random.sample(candidates, k=min(3, len(candidates)))

    encounter_id = str(uuid.uuid4())
    pokemons = {}

    for r in chosen:
        uid = str(uuid.uuid4())
        pokemons[uid] = {
            "uid": uid,
            "species_id": r["id"],
            "name": r["name_cn"],
            "rarity": r["rarity"],
            "level": random.randint(1, 3 + r["rarity"])
        }

    ENCOUNTER_POOL[encounter_id] = {
        "player_id": player_id,
        "pokemons": pokemons
    }

    return {
        "encounter_id": encounter_id,
        "pokemons": list(pokemons.values())
    }

# ===============================
# 刷新单只宝可梦
# ===============================
@router.get("/spawn")
def spawn_pokemon(player_id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name_cn, rarity
        FROM pokemon_species
        ORDER BY RAND()
        LIMIT 1
    """)
    r = cursor.fetchone()
    conn.close()

    if not r:
        raise HTTPException(500, "无宝可梦")

    return {
        "uid": str(uuid.uuid4()),
        "species_id": r["id"],
        "name": r["name_cn"],
        "rarity": r["rarity"],
        "level": random.randint(1, 3 + r["rarity"])
    }

# ===============================
# 球信息
# ===============================
@router.get("/balls")
def get_player_balls(player_id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT pokeball_normal, pokeball_super, pokeball_ultra
        FROM player_resource
        WHERE player_id=%s
    """, (player_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(400, "玩家不存在")

    return {
        "balls": {
            "normal": row["pokeball_normal"],
            "super": row["pokeball_super"],
            "ultra": row["pokeball_ultra"]
        }
    }

# ===============================
# 捕捉
# ===============================
@router.post("/catch")
def catch_pokemon(
    player_id: int,
    encounter_id: str,
    uid: str,
    ball_type: str
):
    if encounter_id not in ENCOUNTER_POOL:
        raise HTTPException(400, "遭遇不存在")

    encounter = ENCOUNTER_POOL[encounter_id]

    if encounter["player_id"] != player_id:
        raise HTTPException(403, "非法操作")

    # 防重复点击
    if uid not in encounter["pokemons"]:
        return {
            "success": False,
            "pokemon_instance_id": None,
            "final_rate": 0
        }

    wild = encounter["pokemons"][uid]

    conn = get_db()
    cursor = conn.cursor()

    ball_col = {
        "normal": "pokeball_normal",
        "super": "pokeball_super",
        "ultra": "pokeball_ultra"
    }.get(ball_type)

    if not ball_col:
        conn.close()
        raise HTTPException(400, "非法球")

    cursor.execute(
        f"SELECT {ball_col} FROM player_resource WHERE player_id=%s",
        (player_id,)
    )
    if cursor.fetchone()[ball_col] <= 0:
        conn.close()
        raise HTTPException(400, "球不足")

    cursor.execute(
        f"""
        UPDATE player_resource
        SET {ball_col}={ball_col}-1
        WHERE player_id=%s
        """,
        (player_id,)
    )

    base = 0.5
    rarity_factor = max(0.05, 1 - wild["rarity"] * 0.08)
    ball_factor = {"normal":1, "super":1.5, "ultra":2}[ball_type]
    final_rate = base * rarity_factor * ball_factor
    success = random.random() < final_rate

    pokemon_instance_id = None
    if success:
        cursor.execute("""
            INSERT INTO pokemon_instance
            (player_id, species_id, level, exp, gender,
             cur_hp, fatigue, rarity, status)
            VALUES (%s,%s,%s,0,'N',1,0,%s,'idle')
        """, (
            player_id,
            wild["species_id"],
            wild["level"],
            wild["rarity"]
        ))
        pokemon_instance_id = cursor.lastrowid

    conn.commit()
    conn.close()

    encounter["pokemons"].pop(uid, None)

    return {
        "success": success,
        "pokemon_instance_id": pokemon_instance_id,
        "final_rate": round(final_rate, 3)
    }

# ===============================
# 买球
# ===============================
@router.post("/buy_ball")
def buy_ball(player_id: int, ball_type: str):
    PRICE = {"normal":100, "super":300, "ultra":800}
    BALL = {
        "normal":"pokeball_normal",
        "super":"pokeball_super",
        "ultra":"pokeball_ultra"
    }

    if ball_type not in PRICE:
        raise HTTPException(400, "非法球")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT gold FROM player_resource WHERE player_id=%s",
        (player_id,)
    )
    gold = cursor.fetchone()["gold"]

    if gold < PRICE[ball_type]:
        conn.close()
        raise HTTPException(400, "金币不足")

    cursor.execute(
        f"""
        UPDATE player_resource
        SET gold=gold-%s,
            {BALL[ball_type]}={BALL[ball_type]}+1
        WHERE player_id=%s
        """,
        (PRICE[ball_type], player_id)
    )

    conn.commit()
    conn.close()
    return {"success": True}
