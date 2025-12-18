from fastapi import APIRouter, HTTPException
from db import get_db

router = APIRouter()
produce_buffer = {}

# =========================
# 农场状态
# =========================
@router.get("/state")
def get_farm_state(player_id: int):
    conn = get_db()
    cursor = conn.cursor()

    # ===== 玩家 =====
    cursor.execute(
        "SELECT username, nickname FROM player WHERE id = %s",
        (player_id,)
    )
    player = cursor.fetchone()
    player_name = player["nickname"] or player["username"]

    # ===== 资源 =====
    cursor.execute(
        """
        SELECT
            wood, ore, herb, berry, gold,
            pokeball_normal, pokeball_super, pokeball_ultra,
            capacity_resource, capacity_pokemon
        FROM player_resource
        WHERE player_id = %s
        """,
        (player_id,)
    )
    resources = cursor.fetchone()

    # ===== 建筑 =====
    cursor.execute(
        """
        SELECT
            pb.id,
            pb.level,
            pb.pos_x,
            pb.pos_y,

            pb.efficiency_bonus,
            pb.slot_bonus,

            b.id AS building_id,
            b.code,
            b.name,
            b.sprite_url,
            b.output_resource,
            b.output_base,
            b.base_slots,
            b.job_id,
            b.max_level
        FROM player_building pb
        JOIN building b ON pb.building_id = b.id
        WHERE pb.player_id = %s
        """,
        (player_id,)
    )
    rows = cursor.fetchall()
    buildings = []

    for b in rows:
        # ===== 工作者 =====
        cursor.execute(
            """
            SELECT
                ja.pokemon_id,
                pi.species_id,
                ps.name_cn
            FROM job_assignment ja
            JOIN pokemon_instance pi ON ja.pokemon_id = pi.id
            JOIN pokemon_species ps ON pi.species_id = ps.id
            WHERE ja.building_id = %s
              AND ja.status = 'working'
            """,
            (b["id"],)
        )
        workers = cursor.fetchall()

        # ===== 计算产出 =====
        output_per_hour = 0.0

        efficiency_multiplier = 1 + (b["efficiency_bonus"] or 0) / 100

        for w in workers:
            cursor.execute(
                """
                SELECT
                    j.weight_hp, j.weight_atk, j.weight_def,
                    j.weight_sp_atk, j.weight_sp_def, j.weight_speed,
                    j.base_efficiency,

                    pi.level,

                    ps.base_hp, ps.base_atk, ps.base_def,
                    ps.base_sp_atk, ps.base_sp_def, ps.base_speed
                FROM job_assignment ja
                JOIN job j ON ja.job_id = j.id
                JOIN pokemon_instance pi ON ja.pokemon_id = pi.id
                JOIN pokemon_species ps ON pi.species_id = ps.id
                WHERE ja.pokemon_id = %s
                  AND ja.building_id = %s
                  AND ja.status = 'working'
                """,
                (w["pokemon_id"], b["id"])
            )
            r = cursor.fetchone()
            if not r:
                continue

            level = r["level"]

            real_hp = r["base_hp"] + level
            real_atk = r["base_atk"] + level
            real_def = r["base_def"] + level
            real_sp_atk = r["base_sp_atk"] + level
            real_sp_def = r["base_sp_def"] + level
            real_speed = r["base_speed"] + level

            power = (
                real_hp * r["weight_hp"] +
                real_atk * r["weight_atk"] +
                real_def * r["weight_def"] +
                real_sp_atk * r["weight_sp_atk"] +
                real_sp_def * r["weight_sp_def"] +
                real_speed * r["weight_speed"]
            )

            output_per_hour += (
                b["output_base"]
                * r["base_efficiency"]
                * power
                * efficiency_multiplier
            )

        # ===== 升级消耗（下一等级）=====
        upgrade_cost = None
        if b["level"] < b["max_level"]:
            cursor.execute(
                """
                SELECT
                    cost_wood,
                    cost_ore,
                    cost_herb,
                    cost_berry,
                    cost_gold
                FROM building_upgrade_cost
                WHERE building_code = %s
                  AND level = %s
                """,
                (b["code"], b["level"])
            )
            cost = cursor.fetchone()
            if cost:
                upgrade_cost = {
                    "wood": cost["cost_wood"],
                    "ore": cost["cost_ore"],
                    "herb": cost["cost_herb"],
                    "berry": cost["cost_berry"],
                    "gold": cost["cost_gold"]
                }

        buildings.append({
            "id": b["id"],
            "building_id": b["building_id"],
            "code": b["code"],
            "name": b["name"],
            "sprite_url": b["sprite_url"],
            "level": b["level"],
            "pos_x": b["pos_x"],
            "pos_y": b["pos_y"],

            "output_resource": b["output_resource"],
            "output_base": b["output_base"],
            "output_per_hour": round(output_per_hour, 1),

            # 槽位 = 基础 + bonus
            "base_slots": b["base_slots"] + (b["slot_bonus"] or 0),

            "job_id": b["job_id"],
            "workers": workers,
            "worker_count": len(workers),

            "upgrade_cost": upgrade_cost
        })

    conn.close()

    return {
        "player_id": player_id,
        "player_name": player_name,
        "resources": resources,
        "buildings": buildings
    }

# =========================
# 建造建筑（level = 0）
# =========================
@router.post("/build")
def build_building(player_id: int, building_code: str):
    conn = get_db()
    cursor = conn.cursor()

    # ===== 建筑模板 =====
    cursor.execute(
        "SELECT id FROM building WHERE code = %s",
        (building_code,)
    )
    template = cursor.fetchone()
    if not template:
        conn.close()
        raise HTTPException(status_code=400, detail="建筑模板不存在")

    # ===== 已有建筑位置 =====
    cursor.execute(
        """
        SELECT pos_x, pos_y
        FROM player_building
        WHERE player_id = %s
        """,
        (player_id,)
    )
    occupied = {(r["pos_x"], r["pos_y"]) for r in cursor.fetchall()}

    # ===== 自动分配位置 =====
    pos_x = pos_y = None
    START_Y=1
    START_X=1
    MAX_COL=7
    y = START_Y

    while True:
        for x in range(START_X, MAX_COL + 1):
            if (x, y) not in occupied:
                pos_x, pos_y = x, y
                break
        if pos_x is not None:
            break
        y += 1

    # ===== 建造费用 =====
    cursor.execute(
        """
        SELECT cost_wood, cost_ore, cost_herb, cost_berry, cost_gold
        FROM building_upgrade_cost
        WHERE building_code = %s AND level = 0
        """,
        (building_code,)
    )
    cost = cursor.fetchone()
    if not cost:
        conn.close()
        raise HTTPException(status_code=400, detail="未配置建造费用")

    cursor.execute(
        """
        SELECT wood, ore, herb, berry, gold
        FROM player_resource
        WHERE player_id = %s
        """,
        (player_id,)
    )
    res = cursor.fetchone()

    if (res["wood"] < cost["cost_wood"] or
        res["ore"] < cost["cost_ore"] or
        res["herb"] < cost["cost_herb"] or
        res["berry"] < cost["cost_berry"] or
        res["gold"] < cost["cost_gold"]):
        conn.close()
        raise HTTPException(status_code=400, detail="资源不足")

    # ===== 扣资源 =====
    cursor.execute(
        """
        UPDATE player_resource
        SET wood = wood - %s,
            ore = ore - %s,
            herb = herb - %s,
            berry = berry - %s,
            gold = gold - %s
        WHERE player_id = %s
        """,
        (
            cost["cost_wood"],
            cost["cost_ore"],
            cost["cost_herb"],
            cost["cost_berry"],
            cost["cost_gold"],
            player_id
        )
    )

    # ===== 插入建筑 =====
    cursor.execute(
        """
        INSERT INTO player_building
        (player_id, building_id, level, pos_x, pos_y)
        VALUES (%s, %s, 1, %s, %s)
        """,
        (player_id, template["id"], pos_x, pos_y)
    )

    conn.commit()
    conn.close()

    return {
        "msg": "建筑建造成功",
        "pos_x": pos_x,
        "pos_y": pos_y
    }



@router.post("/demolish")
def demolish_building(player_id: int, building_instance_id: int):
    conn = get_db()
    cursor = conn.cursor()

    # 1. 校验建筑
    cursor.execute(
        """
        SELECT id
        FROM player_building
        WHERE id = %s AND player_id = %s
        """,
        (building_instance_id, player_id)
    )
    building = cursor.fetchone()

    if not building:
        conn.close()
        raise HTTPException(status_code=400, detail="建筑不存在或不属于该玩家")

    # 2. 找出所有派遣（不管状态）
    cursor.execute(
        """
        SELECT pokemon_id
        FROM job_assignment
        WHERE building_id = %s
        """,
        (building_instance_id,)
    )
    workers = cursor.fetchall()

    # 3. 宝可梦全部改回 idle
    for w in workers:
        cursor.execute(
            """
            UPDATE pokemon_instance
            SET status = 'idle'
            WHERE id = %s
            """,
            (w["pokemon_id"],)
        )

    # 4. 删除派遣记录
    cursor.execute(
        """
        DELETE FROM job_assignment
        WHERE building_id = %s
        """,
        (building_instance_id,)
    )

    #  5. 删除产出日志
    cursor.execute(
        """
        DELETE FROM produce_log
        WHERE building_id = %s
        """,
        (building_instance_id,)
    )

    # 6. 删除建筑本体
    cursor.execute(
        """
        DELETE FROM player_building
        WHERE id = %s
        """,
        (building_instance_id,)
    )

    conn.commit()
    conn.close()

    return {
        "msg": "建筑已拆除",
        "building_instance_id": building_instance_id
    }



# =========================
# 升级建筑（存 A → A+1）
# =========================
@router.post("/upgrade")
def upgrade_building(player_id: int, building_instance_id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            pb.level,
            b.code,
            b.max_level,
            b.output_resource,
            b.base_slots
        FROM player_building pb
        JOIN building b ON pb.building_id = b.id
        WHERE pb.id = %s AND pb.player_id = %s
        """,
        (building_instance_id, player_id)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=400, detail="建筑不存在")

    current_level = row["level"]
    max_level = row["max_level"]

    if current_level >= max_level:
        conn.close()
        raise HTTPException(status_code=400, detail="已达最大等级")

    # ===== 升级消耗 =====
    cursor.execute(
        """
        SELECT cost_wood, cost_ore, cost_herb, cost_berry, cost_gold
        FROM building_upgrade_cost
        WHERE building_code = %s AND level = %s
        """,
        (row["code"], current_level)
    )
    cost = cursor.fetchone()
    if not cost:
        conn.close()
        raise HTTPException(status_code=400, detail="未配置升级费用")

    cursor.execute(
        """
        SELECT wood, ore, herb, berry, gold
        FROM player_resource
        WHERE player_id = %s
        """,
        (player_id,)
    )
    res = cursor.fetchone()

    if (
        res["wood"] < cost["cost_wood"] or
        res["ore"] < cost["cost_ore"] or
        res["herb"] < cost["cost_herb"] or
        res["berry"] < cost["cost_berry"] or
        res["gold"] < cost["cost_gold"]
    ):
        conn.close()
        raise HTTPException(status_code=400, detail="资源不足")

    # 扣资源
    cursor.execute(
        """
        UPDATE player_resource
        SET
            wood = wood - %s,
            ore = ore - %s,
            herb = herb - %s,
            berry = berry - %s,
            gold = gold - %s
        WHERE player_id = %s
        """,
        (
            cost["cost_wood"],
            cost["cost_ore"],
            cost["cost_herb"],
            cost["cost_berry"],
            cost["cost_gold"],
            player_id
        )
    )

    # ===== 升级效果 =====
    if row["output_resource"]:
        # 产出型：效率 +10%
        cursor.execute(
            """
            UPDATE player_building
            SET
                level = level + 1,
                efficiency_bonus = efficiency_bonus + 10,
                upgraded_at = NOW()
            WHERE id = %s
            """,
            (building_instance_id,)
        )
    else:
        # 派遣型：槽位 +1
        cursor.execute(
            """
            UPDATE player_building
            SET
                level = level + 1,
                slot_bonus = slot_bonus + 1,
                upgraded_at = NOW()
            WHERE id = %s
            """,
            (building_instance_id,)
        )

    conn.commit()
    conn.close()

    return {
        "msg": "建筑升级成功",
        "new_level": current_level + 1
    }

# =========================
# 派遣宝可梦
# =========================
@router.post("/assign")
def assign_pokemon(player_id: int, pokemon_id: int, building_instance_id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT status FROM pokemon_instance WHERE id = %s AND player_id = %s",
        (pokemon_id, player_id)
    )
    mon = cursor.fetchone()
    if not mon or mon["status"] != "idle":
        conn.close()
        raise HTTPException(status_code=400, detail="宝可梦不可派遣")

    cursor.execute(
        """
        SELECT b.base_slots, b.job_id
        FROM player_building pb
        JOIN building b ON pb.building_id = b.id
        WHERE pb.id = %s AND pb.player_id = %s
        """,
        (building_instance_id, player_id)
    )
    building = cursor.fetchone()
    if not building:
        conn.close()
        raise HTTPException(status_code=400, detail="建筑不存在")

    cursor.execute(
        """
        SELECT COUNT(*) AS cnt
        FROM job_assignment
        WHERE building_id = %s AND status = 'working'
        """,
        (building_instance_id,)
    )
    if cursor.fetchone()["cnt"] >= building["base_slots"]:
        conn.close()
        raise HTTPException(status_code=400, detail="建筑已满员")

    cursor.execute(
        """
        INSERT INTO job_assignment
        (player_id, pokemon_id, building_id, job_id, start_time, last_calc_time, status)
        VALUES (%s, %s, %s, %s, NOW(), NOW(), 'working')
        """,
        (player_id, pokemon_id, building_instance_id, building["job_id"])
    )

    cursor.execute(
        "UPDATE pokemon_instance SET status = 'working' WHERE id = %s",
        (pokemon_id,)
    )

    conn.commit()
    conn.close()

    return {"msg": "派遣成功"}

@router.post("/remove")
def remove_pokemon_from_building(player_id: int, pokemon_id: int):
    conn = get_db()
    cursor = conn.cursor()

    # 1. 找到正在工作的派遣记录
    cursor.execute(
        """
        SELECT id
        FROM job_assignment
        WHERE player_id = %s
          AND pokemon_id = %s
          AND status = 'working'
        """,
        (player_id, pokemon_id)
    )
    assignment = cursor.fetchone()

    if not assignment:
        conn.close()
        raise HTTPException(status_code=400, detail="该宝可梦当前不在工作")

    assign_id = assignment["id"]

    # 2. 在撤出前，手动结算一次产出
    #    直接复用已有的产出逻辑
    from routers.farm import run_produce_for_player
    run_produce_for_player(player_id)

    # 3. 标记派遣记录为 removed
    cursor.execute(
        """
        UPDATE job_assignment
        SET status = 'removed'
        WHERE id = %s
        """,
        (assign_id,)
    )

    # 4. 宝可梦状态改回 idle
    cursor.execute(
        """
        UPDATE pokemon_instance
        SET status = 'idle'
        WHERE id = %s
        """,
        (pokemon_id,)
    )

    conn.commit()
    conn.close()

    return {
        "msg": "宝可梦已撤出建筑",
        "pokemon_id": pokemon_id
    }


# =================================================
#  自动产出核心函数
# =================================================
def run_produce_for_player(player_id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            ja.id AS assign_id,
            ja.pokemon_id,
            ja.building_id,
            ja.job_id,
            ja.last_calc_time,

            b.output_resource,
            b.output_base,

            j.weight_hp, j.weight_atk, j.weight_def,
            j.weight_sp_atk, j.weight_sp_def, j.weight_speed,
            j.base_efficiency,

            pi.level,

            ps.base_hp, ps.base_atk, ps.base_def,
            ps.base_sp_atk, ps.base_sp_def, ps.base_speed
        FROM job_assignment ja
        JOIN player_building pb ON ja.building_id = pb.id
        JOIN building b ON pb.building_id = b.id
        JOIN job j ON ja.job_id = j.id
        JOIN pokemon_instance pi ON ja.pokemon_id = pi.id
        JOIN pokemon_species ps ON pi.species_id = ps.id
        WHERE ja.player_id = %s
          AND ja.status = 'working'
        """,
        (player_id,)
    )

    assignments = cursor.fetchall()

    for a in assignments:
        assign_id = a["assign_id"]

        cursor.execute(
            "SELECT TIMESTAMPDIFF(SECOND, %s, NOW()) AS diff",
            (a["last_calc_time"],)
        )
        seconds = cursor.fetchone()["diff"]
        if seconds <= 0:
            continue

        hours = seconds / 3600
        level = a["level"]

        # 实际种族值 = 基础 + 等级
        real_hp = a["base_hp"] + level
        real_atk = a["base_atk"] + level
        real_def = a["base_def"] + level
        real_sp_atk = a["base_sp_atk"] + level
        real_sp_def = a["base_sp_def"] + level
        real_speed = a["base_speed"] + level

        # 岗位能力
        power = (
            real_hp * a["weight_hp"] +
            real_atk * a["weight_atk"] +
            real_def * a["weight_def"] +
            real_sp_atk * a["weight_sp_atk"] +
            real_sp_def * a["weight_sp_def"] +
            real_speed * a["weight_speed"]
        )

        # 本次产出
        delta = (
            a["output_base"]
            * a["base_efficiency"]
            * power
            * hours
        )

        prev = produce_buffer.get(assign_id, 0.0)
        total = prev + delta

        amount = int(total)
        remain = total - amount

        if amount > 0:
            res = a["output_resource"]

            cursor.execute(
                """
                INSERT INTO produce_log
                (player_id, pokemon_id, building_id, job_id,
                 resource_type, amount, start_time, end_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                """,
                (
                    player_id,
                    a["pokemon_id"],
                    a["building_id"],
                    a["job_id"],
                    res,
                    amount,
                    a["last_calc_time"]
                )
            )

            cursor.execute(
                f"""
                UPDATE player_resource
                SET {res} = {res} + %s
                WHERE player_id = %s
                """,
                (amount, player_id)
            )

        produce_buffer[assign_id] = remain

        cursor.execute(
            """
            UPDATE job_assignment
            SET last_calc_time = NOW()
            WHERE id = %s
            """,
            (assign_id,)
        )

    conn.commit()
    conn.close()

