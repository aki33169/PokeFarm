from fastapi import APIRouter, HTTPException
from db import get_db
from utils.security import generate_salt, hash_password

router = APIRouter()

@router.post("/register")
def register(username: str, password: str, nickname: str = None):
    conn = get_db()
    cursor = conn.cursor()

    try:
        # ---------- 用户是否存在 ----------
        cursor.execute(
            "SELECT id FROM player WHERE username=%s",
            (username,)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="用户名已存在")

        # ---------- 创建 player ----------
        salt = generate_salt()
        password_hash = hash_password(password, salt)

        cursor.execute(
            """
            INSERT INTO player (username, password_hash, password_salt, nickname)
            VALUES (%s, %s, %s, %s)
            """,
            (username, password_hash, salt, nickname)
        )
        player_id = cursor.lastrowid

        # ---------- 初始化资源 ----------
        cursor.execute(
            """
            INSERT INTO player_resource
            (player_id,
             wood, ore, herb, berry, gold, food,
             capacity_resource, capacity_pokemon,
             pokeball_normal, pokeball_super, pokeball_ultra)
            VALUES
            (%s,
             120, 60, 40, 40, 500, 50,
             1500, 10,
             10, 2, 0)
            """,
            (player_id,)
        )

        # ---------- 初始化建筑 ----------
        # 用 building.code 查真实 id
        init_buildings = [
            # code, x, y
            ("home",        1, 1),
            ("lumber_mill",  2, 1),
            ("pokecenter",  3, 2),
            ("shop",        4, 2),
        ]

        for code, x, y in init_buildings:
            cursor.execute(
                "SELECT id FROM building WHERE code=%s",
                (code,)
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(
                    status_code=500,
                    detail=f"building 表缺少 code={code}"
                )

            building_id = row["id"]

            cursor.execute(
                """
                INSERT INTO player_building
                (player_id, building_id, level, pos_x, pos_y)
                VALUES (%s, %s, 1, %s, %s)
                """,
                (player_id, building_id, x, y)
            )

        conn.commit()

        return {
            "success": True,
            "msg": "注册成功",
            "player_id": player_id
        }

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ===============================
# 登录
# ===============================
@router.post("/login")
def login(username: str, password: str):
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, password_hash, password_salt
            FROM player
            WHERE username=%s
            """,
            (username,)
        )
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=400, detail="用户不存在")

        input_hash = hash_password(password, user["password_salt"])
        if input_hash != user["password_hash"]:
            raise HTTPException(status_code=400, detail="密码错误")

        cursor.execute(
            "UPDATE player SET last_login_at = NOW() WHERE id=%s",
            (user["id"],)
        )
        conn.commit()

        return {
            "success": True,
            "msg": "登录成功",
            "player_id": user["id"]
        }

    finally:
        conn.close()
