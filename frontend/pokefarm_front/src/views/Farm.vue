<template>
  <div class="farm-page">
    <!-- ================= 顶部 HUD ================= -->
    <div class="resource-bar">
      <div class="bar-left">
        <div class="player-name">{{ playerName }}</div>
      </div>

      <div class="bar-center">
        <div class="res" v-for="r in displayResources" :key="r.key">
          <img class="res-icon" :src="getIcon(r.key)" />
          <span>{{ r.value }}</span>
        </div>
      </div>

      <div class="bar-right">
        <div class="res" v-for="b in balls" :key="b.key">
          <img class="res-icon" :src="getIcon(b.key)" />
          <span>{{ b.value }}</span>
        </div>
      </div>
    </div>

    <!-- ================= 农场区域 ================= -->
    <div class="farm-area">
      <div
        class="building"
        v-for="b in buildings"
        :key="b.id"
        :class="{ selected: selectedBuilding && selectedBuilding.id === b.id }"
        :style="{
          left: b.pos_x * (GRID + GAP) + 'px',
          top: b.pos_y * (GRID + GAP) + 'px'
        }"
        @click.stop="selectBuilding(b)"
      >
        <img class="building-sprite" :src="getBuildingSprite(b.sprite_url)" />

        <div class="building-level">Lv.{{ b.level }}</div>

        <div class="pokemon-area">
          <div
            v-for="p in b.workers"
            :key="p.pokemon_id"
            class="pokemon-wrapper"
            :style="getPokemonStyle(p.pokemon_id)"
          >
            <div class="pokemon-bob">
              <img
                class="pokemon-sprite"
                :src="getPokemonSprite(p.species_id)"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- ⭐ 外出按钮（左下角） -->
      <div class="encounter-float-btn" @click.stop="goEncounter">
        <img :src="getIcon('pokeball_normal')" />
      </div>

      <!-- 建造按钮（右下角，原样） -->
      <div class="build-float-btn" @click.stop="openBuildPanel">
        <img :src="getIcon('build')" />
      </div>
    </div>

    <!-- ================= 建造面板 ================= -->
    <BuildPanel
      v-if="showBuildPanel"
      :player-id="playerId"
      :resources="resources"
      @close="closeBuildPanel"
      @built="onBuildingBuilt"
    />

    <!-- ================= 建筑详情 ================= -->
    <BuildingPanel
      v-if="selectedBuilding"
      :building="selectedBuilding"
      :resources="resources"
      @close="selectedBuilding = null"
      @refresh="fetchFarmState"
      @dispatch="openDispatchPanel"
      @open-pokemon-detail="openPokemonDetail"
    />

    <!-- ================= 派遣面板 ================= -->
    <DispatchPanel
      v-if="showDispatchPanel"
      :key="dispatchBuildingId"
      :building-id="dispatchBuildingId"
      @close="closeDispatchPanel"
      @dispatched="onPokemonDispatched"
      @open-pokemon-detail="openPokemonDetail"
    />

    <!-- ================= 宝可梦详情 ================= -->
    <PokemonDetailPanel
      v-if="showPokemonDetail"
      :pokemon-id="detailPokemonId"
      @close="closePokemonDetail"
    />
  </div>
</template>

<script>
import http from '@/api/http'
import BuildPanel from '@/components/BuildPanel.vue'
import BuildingPanel from '@/components/BuildingPanel.vue'
import DispatchPanel from '@/components/DispatchPanel.vue'
import PokemonDetailPanel from '@/components/PokemonDetailPanel.vue'

export default {
  name: 'Farm',
  components: {
    BuildPanel,
    BuildingPanel,
    DispatchPanel,
    PokemonDetailPanel
  },

  data() {
    return {
      GRID: 128,
      GAP: 64,

      playerId: null,
      playerName: '',

      resources: {},
      buildings: [],

      pokemonMotion: {},
      lastFrameTime: 0,

      showBuildPanel: false,
      selectedBuilding: null,

      showDispatchPanel: false,
      dispatchBuildingId: null,

      showPokemonDetail: false,
      detailPokemonId: null
    }
  },

  computed: {
    displayResources() {
      const order = ['wood', 'ore', 'herb', 'berry', 'gold']
      return order
        .filter(k => this.resources[k] !== undefined)
        .map(k => ({ key: k, value: this.resources[k] }))
    },

    balls() {
      return [
        { key: 'pokeball_normal', value: this.resources.pokeball_normal },
        { key: 'pokeball_super', value: this.resources.pokeball_super },
        { key: 'pokeball_ultra', value: this.resources.pokeball_ultra }
      ]
    }
  },

  mounted() {
    this.playerId = localStorage.getItem('player_id')
    this.fetchFarmState()
    setInterval(this.fetchFarmState, 3000)
    setInterval(this.updatePokemonTargets, 3000)
    requestAnimationFrame(this.animate)
  },

  methods: {
    async fetchFarmState() {
      const res = await http.get('/farm/state', {
        params: { player_id: this.playerId }
      })
      this.playerName = res.data.player_name
      this.resources = res.data.resources
      this.buildings = res.data.buildings

      if (
        this.selectedBuilding &&
        !this.buildings.find(b => b.id === this.selectedBuilding.id)
      ) {
        this.selectedBuilding = null
      }
    },

    selectBuilding(b) {
      this.selectedBuilding = b
      this.showBuildPanel = false
    },

    openBuildPanel() {
      this.selectedBuilding = null
      this.showBuildPanel = true
    },

    closeBuildPanel() {
      this.showBuildPanel = false
    },

    onBuildingBuilt() {
      this.showBuildPanel = false
      this.fetchFarmState()
    },

    openDispatchPanel(buildingId) {
      this.dispatchBuildingId = buildingId
      this.selectedBuilding = null
      this.showDispatchPanel = true
    },

    closeDispatchPanel() {
      this.showDispatchPanel = false
      this.dispatchBuildingId = null
    },

    onPokemonDispatched() {
      this.closeDispatchPanel()
      this.fetchFarmState()
    },

    openPokemonDetail(pokemonId) {
      this.detailPokemonId = pokemonId
      this.showPokemonDetail = true
    },

    closePokemonDetail() {
      this.showPokemonDetail = false
      this.detailPokemonId = null
    },

    getIcon(code) {
      return new URL(`../assets/icons/${code}.png`, import.meta.url).href
    },
    getBuildingSprite(filename) {
      return new URL(`../assets/buildings/${filename}`, import.meta.url).href
    },
    getPokemonSprite(id) {
      const num = String(id).padStart(4, '0')
      return new URL(`../assets/pokemons/${num}.png`, import.meta.url).href
    },

    goEncounter() {
      this.$router.push('/Encounter')
    },

    updatePokemonTargets() {
      this.buildings.forEach(b => {
        b.workers.forEach(p => {
          if (!this.pokemonMotion[p.pokemon_id]) {
            this.pokemonMotion[p.pokemon_id] = {
              x: 0,
              y: 0,
              tx: 0,
              ty: 0,
              dir: 1
            }
          }

          const AREA_WIDTH = 100
          const AREA_HEIGHT = 40

          this.pokemonMotion[p.pokemon_id].tx =
            Math.random() * AREA_WIDTH - AREA_WIDTH / 2

          this.pokemonMotion[p.pokemon_id].ty =
            Math.random() * AREA_HEIGHT
        })
      })
    },

    animate(time) {
      if (!this.lastFrameTime) this.lastFrameTime = time
      const dt = (time - this.lastFrameTime) / 1000
      this.lastFrameTime = time

      Object.values(this.pokemonMotion).forEach(m => {
        const dx = m.tx - m.x
        const dy = m.ty - m.y

        if (Math.abs(dx) > 1) {
          const vx = dx * 2
          m.x += vx * dt
          m.dir = vx > 0 ? 1 : -1
        }

        if (Math.abs(dy) > 1) {
          const vy = dy * 2
          m.y += vy * dt
        }
      })

      requestAnimationFrame(this.animate)
    },

    getPokemonStyle(pid) {
      const m = this.pokemonMotion[pid]
      return m
        ? { transform: `translate(${m.x}px, ${m.y}px) scaleX(${m.dir})` }
        : {}
    }
  }
}
</script>

<style scoped>
  .encounter-float-btn {
  position: absolute;
  left: 20px;
  bottom: 20px;
  width: 64px;
  height: 64px;
  background: #c49a6c;
  border: 3px solid #3a220f;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}

.encounter-float-btn:hover {
  transform: translateY(-4px);
  box-shadow: 0 0 12px rgba(255,255,255,0.8);
}

.encounter-float-btn:active {
  transform: translateY(0);
  box-shadow: none;
}

.encounter-float-btn img {
  width: 100%;
  image-rendering: pixelated;
}

.farm-page {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #9ed39a;
}

/* ===== 顶部 ===== */

.resource-bar {
  display: flex;
  align-items: center;
  height: 64px;
  padding: 0 12px;
  background: #8b5a2b;
  border-bottom: 4px solid #3a220f;
}

.bar-left { margin-right: 16px; }

.player-name {
  padding: 6px 10px;
  background: #c49a6c;
  border: 2px solid #3a220f;
  font-family: monospace;
}

.bar-center {
  display: flex;
  gap: 10px;
  flex: 1;
}

.bar-right {
  display: flex;
  gap: 10px;
}

.res {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: #c49a6c;
  border: 2px solid #3a220f;
}

.res-icon {
  width: 20px;
  image-rendering: pixelated;
}

/* ===== 农场 ===== */

.farm-area {
  flex: 1;
  position: relative;
  background: #7fcf8a;
}

.building {
  position: absolute;
  width: 128px;
  height: 128px;
  cursor: pointer;
  filter: drop-shadow(2px 3px 0 #3a220f);
  transition: transform 0.15s, filter 0.15s;
}

.building:hover {
  transform: translateY(-4px);
  filter: drop-shadow(0 0 10px rgba(255,255,255,0.6))
          drop-shadow(2px 3px 0 #3a220f);
}

.building.selected {
  outline: 4px solid #ffd966;
}

.building-sprite {
  width: 128px;
  image-rendering: pixelated;
}

.building-level {
  position: absolute;
  bottom: -18px;
  width: 100%;
  text-align: center;
  font-size: 13px;
  background: #fff;
  border: 2px solid #222;
}

/* ===== 宝可梦 ===== */

.pokemon-area {
  position: absolute;
  top: 96px;
  left: 0;
  width: 128px; 
  height: 64px; 
  pointer-events: none;
}


.pokemon-wrapper {
  position: absolute;
}

.pokemon-bob {
  animation: walk-bob 0.8s infinite alternate;
}

.pokemon-sprite {
  width: 76px;
  image-rendering: pixelated;
}

@keyframes walk-bob {
  from { transform: translateY(0); }
  to   { transform: translateY(-6px); }
}

/* ===== 底部 ===== */

.bottom-bar {
  display: flex;
  justify-content: space-around;
  padding: 10px;
  background: #fff;
  border-top: 3px solid #222;
}

.build-float-btn {
  position: absolute;
  right: 20px;
  bottom: 20px;
  width: 64px;
  height: 64px;
  background: #c49a6c;
  border: 3px solid #3a220f;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}

.build-float-btn:hover {
  transform: translateY(-4px);
  box-shadow: 0 0 12px rgba(255,255,255,0.8);
}

.build-float-btn:active {
  transform: translateY(0);
  box-shadow: none;
}

.build-float-btn img {
  width: 100%;
  image-rendering: pixelated;
}

.farm-page {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 农场背景：平铺 */
.farm-area {
  flex: 1;
  position: relative;
  background-image: url('@/assets/background/background.png');
  background-repeat: repeat;
  background-size: 128px 128px;
}
</style>
