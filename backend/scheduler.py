from apscheduler.schedulers.background import BackgroundScheduler
from db import get_db
from routers.farm import run_produce_for_player


def run_all_players_produce():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM player")
    players = cursor.fetchall()

    conn.close()

    for p in players:
        run_produce_for_player(p["id"])


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_all_players_produce,
        trigger="interval",
        seconds=5   # ⭐ 每 5 秒自动结算一次
    )
    scheduler.start()
