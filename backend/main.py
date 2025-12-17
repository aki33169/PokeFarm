from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import player, pokemon, encounter, farm, building
from scheduler import start_scheduler

app = FastAPI(
    title="PokeFarm Backend",
    version="0.1.0",
    description="写啊写啊写"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(player.router, prefix="/player", tags=["Player"])
app.include_router(farm.router, prefix="/farm", tags=["Farm"])
app.include_router(pokemon.router, prefix="/pokemon", tags=["Pokemon"])
app.include_router(encounter.router, prefix="/encounter", tags=["Encounter"])
app.include_router(building.router, prefix="/building", tags=["Building"])

@app.get("/")
def root():
    return {"message": "PokeFarm backend running!"}

start_scheduler()
