from fastapi import APIRouter
from db import get_db

router = APIRouter()

# =========================
# 建筑模板列表（建造面板用）
# =========================
@router.get("/list")
def list_buildings():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            b.code,
            b.name,
            b.description,
            b.sprite_url,

            buc.cost_wood,
            buc.cost_ore,
            buc.cost_herb,
            buc.cost_berry,
            buc.cost_gold
        FROM building b
        JOIN building_upgrade_cost buc
          ON b.code = buc.building_code
        WHERE buc.level = 0
        ORDER BY b.id
        """
    )

    rows = cursor.fetchall()
    conn.close()

    buildings = []
    for r in rows:
        buildings.append({
            "code": r["code"],
            "name": r["name"],
            "description": r["description"],
            "sprite_url": r["sprite_url"],
            "cost": {
                "wood": r["cost_wood"],
                "ore": r["cost_ore"],
                "herb": r["cost_herb"],
                "berry": r["cost_berry"],
                "gold": r["cost_gold"]
            }
        })

    return buildings
