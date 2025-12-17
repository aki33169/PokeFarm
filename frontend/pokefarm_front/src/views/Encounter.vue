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

    <!-- ================= 遭遇区域 ================= -->
    <div class="encounter-area">
      <div class="encounter-field">
        <div
          v-for="p in pokemons"
          :key="p.uid"
          class="wild-pokemon"
          :class="{ catching: catchingUid === p.uid }"
          :style="{ left: p.x + 'px', top: p.y + 'px' }"
          @click="catchPokemon(p)"
        >
          <div class="pokemon-bob">
            <img :src="getPokemonSprite(p.species_id)" />
          </div>
        </div>

        <!-- 返回按钮 -->
        <div class="return-float-btn" @click="$router.push('/farm')">
          <img src="@/assets/Texts/Back.png" />
        </div>
      </div>
    </div>

    <!-- ================= 底部球栏 ================= -->
    <div class="ball-bar">
      <div class="ball-container">
        <div
          v-for="b in ballButtons"
          :key="b.type"
          class="ball-btn"
          :class="{ active: selectedBall === b.type }"
          @click="selectedBall = b.type"
        >
          <img :src="getIcon(b.icon)" />
          <span class="ball-count">{{ b.count }}</span>

          <!-- 购买行 -->
          <div class="ball-buy-row">
            <div class="ball-plus" @click.stop="buyBall(b.type)">+</div>
            <div class="ball-price">
              <img :src="getIcon('gold')" />
              <span>{{ b.price }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 宝可梦详情 -->
    <PokemonDetailPanel
      v-if="showDetail"
      :pokemon-id="detailPokemonId"
      @close="showDetail = false"
    />
  </div>
</template>

<script>
import http from '@/api/http'
import PokemonDetailPanel from '@/components/PokemonDetailPanel.vue'

export default {
  components: { PokemonDetailPanel },

  data() {
    return {
      playerId: null,
      playerName: '',
      resources: {},
      ballsData: {},
      encounterId: null,
      pokemons: [],
      selectedBall: 'normal',
      catchingUid: null,
      lastFrame: 0,
      rafId: null,
      spawnTimer: null,
      showDetail: false,
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
    },

    ballButtons() {
      return [
        { type: 'normal', icon: 'pokeball_normal', count: this.ballsData.normal, price: 100 },
        { type: 'super', icon: 'pokeball_super', count: this.ballsData.super, price: 300 },
        { type: 'ultra', icon: 'pokeball_ultra', count: this.ballsData.ultra, price: 800 }
      ]
    }
  },

  async mounted() {
    this.playerId = localStorage.getItem('player_id')
    await this.fetchPlayerInfo()
    await this.enterMap()
    await this.fetchBalls()

    this.rafId = requestAnimationFrame(this.animate)
    this.spawnTimer = setInterval(this.spawnPokemon, 10000)
  },

  beforeUnmount() {
    cancelAnimationFrame(this.rafId)
    clearInterval(this.spawnTimer)
  },

  methods: {
    async fetchPlayerInfo() {
      const res = await http.get('/farm/state', {
        params: { player_id: this.playerId }
      })
      this.playerName = res.data.player_name
      this.resources = res.data.resources
    },

    async enterMap() {
      const res = await http.get('/encounter/map', {
        params: { player_id: this.playerId }
      })
      this.encounterId = res.data.encounter_id

      const W = 520 - 128
      const H = 280 - 128

      this.pokemons = res.data.pokemons.map(p => ({
        ...p,
        x: Math.random() * W,
        y: Math.random() * H,
        tx: Math.random() * W,
        ty: Math.random() * H,
        rest: Math.random() * 1.5
      }))
    },

    async spawnPokemon() {
      if (this.pokemons.length >= 10) return

      const res = await http.get('/encounter/spawn', {
        params: { player_id: this.playerId }
      })

      const W = 520 - 128
      const H = 280 - 128

      this.pokemons.push({
        ...res.data,
        x: Math.random() * W,
        y: Math.random() * H,
        tx: Math.random() * W,
        ty: Math.random() * H,
        rest: Math.random() * 1.5
      })
    },

    animate(time) {
      if (!this.lastFrame) this.lastFrame = time
      const dt = (time - this.lastFrame) / 1000
      this.lastFrame = time

      const SPEED = 40

      this.pokemons.forEach(p => {
        if (p.rest > 0) {
          p.rest -= dt
          return
        }

        const dx = p.tx - p.x
        const dy = p.ty - p.y
        const dist = Math.hypot(dx, dy)

        if (dist < 2) {
          p.tx = Math.random() * (520 - 128)
          p.ty = Math.random() * (280 - 128)
          p.rest = 1 + Math.random()
          return
        }

        p.x += (dx / dist) * SPEED * dt
        p.y += (dy / dist) * SPEED * dt
      })

      this.rafId = requestAnimationFrame(this.animate)
    },

    async fetchBalls() {
      const res = await http.get('/encounter/balls', {
        params: { player_id: this.playerId }
      })
      this.ballsData = res.data.balls
    },

    async buyBall(type) {
      await http.post('/encounter/buy_ball', null, {
        params: { player_id: this.playerId, ball_type: type }
      })
      await this.fetchPlayerInfo()
      await this.fetchBalls()
    },

    async catchPokemon(p) {
      if (this.ballsData[this.selectedBall] <= 0) return
      if (this.catchingUid) return

      this.catchingUid = p.uid

      setTimeout(async () => {
        try {
          const res = await http.post('/encounter/catch', null, {
            params: {
              player_id: this.playerId,
              encounter_id: this.encounterId,
              uid: p.uid,
              ball_type: this.selectedBall
            }
          })

          await this.fetchBalls()

          this.pokemons = this.pokemons.filter(x => x.uid !== p.uid)

          if (res.data.success) {
            this.detailPokemonId = res.data.pokemon_instance_id
            this.showDetail = true
          }
        } finally {
          this.catchingUid = null
        }
      }, 600)
    },

    getIcon(code) {
      return new URL(`../assets/icons/${code}.png`, import.meta.url).href
    },

    getPokemonSprite(id) {
      const num = String(id).padStart(4, '0')
      return new URL(`../assets/pokemons/${num}.png`, import.meta.url).href
    }
  }
}
</script>




<style scoped>

.farm-page {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #9ed39a;
}

/* 顶部资源栏 */
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

/* ===== 遭遇区域 ===== */
.encounter-area {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background-image: url('@/assets/background/background.png');
  background-repeat: repeat;
  background-size: 128px 128px;
}

.encounter-field {
  position: relative;
  width: 520px;
  height: 280px;
}

.wild-pokemon {
  position: absolute;
  width: 64px;
  cursor: pointer;
  transition: transform 0.3s, filter 0.3s, opacity 0.3s;
}

.wild-pokemon:hover {
  transform: scale(1.1);
}

.wild-pokemon.catching {
  filter: brightness(1.8);
  transform: scale(0.1);
  opacity: 0;
}

.wild-pokemon img {
  width: 100%;
  image-rendering: pixelated;
}

/* ===== 底部球栏 ===== */
.ball-bar {
  height: 96px;
  background: #8b5a2b;
  border-top: 4px solid #3a220f;
  display: flex;
  justify-content: center;
  align-items: center;
}

.ball-container {
  display: flex;
  gap: 32px;
}

.ball-btn {
  width: 72px;
  height: 72px;
  background: #c49a6c;
  border: 3px solid #3a220f;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.ball-btn.active {
  outline: 4px solid #ffd966;
}

.ball-btn img {
  width: 36px;
  image-rendering: pixelated;
}

.wild-pokemon img {
  width: 100%;
  image-rendering: pixelated;
}

/* 捕捉成功 */
.wild-pokemon.catching {
  filter: brightness(1.8);
  transform: scale(0.1);
  opacity: 0;
  transition: all 0.4s;
}

/* 抖动 */
@keyframes shake {
  0% { transform: translateX(0); }
  25% { transform: translateX(-8px); }
  50% { transform: translateX(8px); }
  75% { transform: translateX(-6px); }
  100% { transform: translateX(0); }
}

.wild-pokemon.shake {
  animation: shake 0.4s;
}

.return-float-btn {
  position: absolute;
  left: 900px;
  bottom: -160px;
  width: 100px;
  height: 40px;
  background: #c49a6c;
  border: 3px solid #3a220f;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}

.return-float-btn:hover {
  transform: translateY(-4px);
  box-shadow: 0 0 12px rgba(255,255,255,0.8);
}

.return-float-btn:active {
  transform: translateY(0);
  box-shadow: none;
}

.return-float-btn img {
  width: 100%;
  image-rendering: pixelated;
}

.wild-pokemon {
  position: absolute;
  width: 128px;
}

.pokemon-bob {
  animation: walk-bob 0.8s infinite alternate;
}

@keyframes walk-bob {
  from { transform: translateY(0); }
  to { transform: translateY(-6px); }
}

.ball-count {
  margin-top: 2px;
  font-size: 13px;
}

/* 下方购买行 */
.ball-buy-row {
  margin-top: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

/* + 按钮（和 return 同款手感） */
.ball-plus {
  width: 20px;
  height: 20px;
  background: #c49a6c;
  border: 2px solid #3a220f;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.15s, box-shadow 0.15s;
}

.ball-plus:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 8px rgba(255,255,255,0.8);
}

.ball-plus:active {
  transform: translateY(0);
  box-shadow: none;
}

/* 价格 */
.ball-price {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.ball-price img {
  width: 14px;
  image-rendering: pixelated;
}


</style>
