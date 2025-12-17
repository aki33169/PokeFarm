from fastapi import APIRouter, HTTPException
from db import get_db

router = APIRouter()

# ===============================
# 仓库：列出玩家所有宝可梦
# ===============================
@router.get("/list")
def list_pokemons(player_id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            pi.id AS pokemon_id,
            pi.nickname AS name,            -- ✅ 玩家自定义名（可为空）
            ps.name_cn,
            ps.sprite_url,
            pi.level,
            pi.rarity,
            pi.gender,
            pi.status
        FROM pokemon_instance pi
        JOIN pokemon_species ps ON pi.species_id = ps.id
        WHERE pi.player_id = %s
        ORDER BY pi.rarity DESC, pi.level DESC, pi.id ASC
        """,
        (player_id,)
    )

    rows = cursor.fetchall()
    conn.close()

    return {
        "player_id": player_id,
        "pokemons": rows
    }

# ===============================
# 单只宝可梦详情（真实数值）
# 基础种族值 + 等级
# ===============================
@router.get("/detail")
def get_pokemon_detail(player_id: int, pokemon_id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            pi.id,
            pi.species_id,
            pi.nickname AS name,            -- ✅ 玩家自定义名（可为空）
            pi.level,
            pi.exp,
            pi.gender,
            pi.fatigue,
            pi.status,
            pi.rarity,

            ps.name_cn,
            ps.sprite_url,
            ps.base_hp,
            ps.base_atk,
            ps.base_def,
            ps.base_sp_atk,
            ps.base_sp_def,
            ps.base_speed
        FROM pokemon_instance pi
        JOIN pokemon_species ps ON pi.species_id = ps.id
        WHERE pi.id = %s AND pi.player_id = %s
        """,
        (pokemon_id, player_id)
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="宝可梦不存在")

    level = row["level"]

    # 实际数值 = 基础 + 等级
    stats = {
        "hp": row["base_hp"] + level,
        "atk": row["base_atk"] + level,
        "def": row["base_def"] + level,
        "sp_atk": row["base_sp_atk"] + level,
        "sp_def": row["base_sp_def"] + level,
        "speed": row["base_speed"] + level
    }

    return {
        "pokemon_id": row["id"],
        "species_id": row["species_id"],

        # ✅ 两个名字都给
        "name": row["name"],          # 可能 None/空
        "name_cn": row["name_cn"],

        "sprite_url": row["sprite_url"],
        "level": level,
        "rarity": row["rarity"],
        "gender": row["gender"],
        "status": row["status"],
        "fatigue": row["fatigue"],

        "stats": stats,

        # ⭐ 新增：升级消耗（前端按钮用）
        "level_up_cost": {
            "berry": level
        }
    }

# ===============================
# 宝可梦升级
# 规则：升一级 = level +1
# ===============================
@router.post("/level_up")
def level_up_pokemon(player_id: int, pokemon_id: int):
    conn = get_db()
    cursor = conn.cursor()

    # 1. 校验宝可梦归属 & 取当前等级
    cursor.execute(
        """
        SELECT level
        FROM pokemon_instance
        WHERE id = %s AND player_id = %s
        """,
        (pokemon_id, player_id)
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="宝可梦不存在")

    current_level = row["level"]

    # 2. 计算升级消耗（等级越高越贵）
    cost_berry = current_level

    # 3. 检查树果数量
    cursor.execute(
        """
        SELECT berry
        FROM player_resource
        WHERE player_id = %s
        """,
        (player_id,)
    )
    res = cursor.fetchone()

    if not res or res["berry"] < cost_berry:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail=f"树果不足，需要 {cost_berry} 个"
        )

    # 4. 扣树果
    cursor.execute(
        """
        UPDATE player_resource
        SET berry = berry - %s
        WHERE player_id = %s
        """,
        (cost_berry, player_id)
    )

    # 5. 宝可梦升级
    cursor.execute(
        """
        UPDATE pokemon_instance
        SET level = level + 1
        WHERE id = %s
        """,
        (pokemon_id,)
    )

    conn.commit()
    conn.close()

    return {
        "msg": "宝可梦升级成功",
        "pokemon_id": pokemon_id,
        "old_level": current_level,
        "new_level": current_level + 1,
        "cost": {
            "berry": cost_berry
        }
    }

# ===============================
# 可派遣宝可梦（idle）
# ===============================
@router.get("/idle")
def list_idle_pokemons(player_id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            pi.id AS pokemon_id,
            pi.species_id,
            pi.nickname AS name,            -- ✅ 玩家自定义名（可为空）
            pi.level,
            pi.rarity,
            pi.gender,

            ps.name_cn,
            ps.sprite_url,
            ps.base_hp,
            ps.base_atk,
            ps.base_def,
            ps.base_sp_atk,
            ps.base_sp_def,
            ps.base_speed
        FROM pokemon_instance pi
        JOIN pokemon_species ps ON pi.species_id = ps.id
        WHERE pi.player_id = %s
          AND pi.status = 'idle'
        ORDER BY pi.rarity DESC, pi.level DESC, pi.id ASC
        """,
        (player_id,)
    )

    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        level = r["level"]
        result.append({
            "pokemon_id": r["pokemon_id"],
            "species_id": r["species_id"],

            # ✅ 两个名字都给
            "name": r["name"],
            "name_cn": r["name_cn"],

            "sprite_url": r["sprite_url"],
            "level": level,
            "rarity": r["rarity"],
            "gender": r["gender"],

            "stats": {
                "hp": r["base_hp"] + level,
                "atk": r["base_atk"] + level,
                "def": r["base_def"] + level,
                "sp_atk": r["base_sp_atk"] + level,
                "sp_def": r["base_sp_def"] + level,
                "speed": r["base_speed"] + level
            },

            "level_up_cost": {
                "berry": level
            }
        })

    return result
