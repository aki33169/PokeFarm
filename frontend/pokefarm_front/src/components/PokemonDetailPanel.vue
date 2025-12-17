<template>
  <div class="detail-mask" @click.stop="onMaskClick">
    <div class="detail-panel" @click.stop>

      <button class="close" @click="$emit('close')">✕</button>

      <div v-if="detail" class="content">
        <!-- 左 -->
        <div class="left">
          <img
            class="pokemon-img"
            :src="getPokemonSprite(detail.species_id)"
          />
        </div>

        <!-- 右 -->
        <div class="right">
          <div class="name">
            {{ displayName }} Lv.{{ detail.level }}
          </div>

          <div class="stats">
            <div
              class="stat"
              v-for="s in statList"
              :key="s.key"
            >
              <span class="label">{{ s.label }}</span>
              <span class="value">{{ detail.stats[s.key] }}</span>
            </div>
          </div>

          <div class="upgrade">
            <button
              class="upgrade-btn"
              :disabled="!canUpgrade"
              @click="upgrade"
            >
              升级
            </button>

            <div class="cost">
              <img :src="getIcon('berry')" />
              <span>{{ levelUpCost }}</span>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import http from '@/api/http'

export default {
  props: {
    pokemonId: { type: Number, required: true }
  },

  data() {
    return {
      detail: null
    }
  },

  computed: {
    statList() {
      return [
        { key: 'hp', label: '生命' },
        { key: 'atk', label: '攻击' },
        { key: 'def', label: '防御' },
        { key: 'sp_atk', label: '特攻' },
        { key: 'sp_def', label: '特防' },
        { key: 'speed', label: '速度' }
      ]
    },

    displayName() {
      return this.detail.name || this.detail.name_cn
    },

    levelUpCost() {
      return this.detail.level
    },

    canUpgrade() {
      return this.levelUpCost > 0
    }
  },

  mounted() {
    this.fetchDetail()
  },

  methods: {
    onMaskClick() {
    this.$emit('close')
  },
  
    async fetchDetail() {
      const res = await http.get('/pokemon/detail', {
        params: {
          player_id: localStorage.getItem('player_id'),
          pokemon_id: this.pokemonId
        }
      })
      this.detail = res.data
    },

    async upgrade() {
      await http.post('/pokemon/level_up', null, {
        params: {
          player_id: localStorage.getItem('player_id'),
          pokemon_id: this.pokemonId
        }
      })

      await this.fetchDetail()

      this.$emit('upgraded')
    },

    getPokemonSprite(id) {
      const num = String(id).padStart(4, '0')
      return new URL(`../assets/pokemons/${num}.png`, import.meta.url).href
    },

    getIcon(code) {
      return new URL(`../assets/icons/${code}.png`, import.meta.url).href
    }
  }
}
</script>


<style scoped>
.detail-mask {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 80;
}

.detail-panel {
  width: 480px;
  background: #c49a6c;
  border: 4px solid #3a220f;
  padding: 12px;
  font-family: monospace;
  position: relative;
}

.close {
  position: absolute;
  right: 6px;
  top: 6px;
  background: #b33;
  color: #fff;
  border: none;
  cursor: pointer;
}

.content {
  display: flex;
  gap: 16px;
}

.left {
  width: 160px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.pokemon-img {
  width: 128px;
  height: 128px;
  object-fit: contain;
  image-rendering: pixelated;
}

.right {
  flex: 1;
}

.name {
  font-size: 16px;
  margin-bottom: 8px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 4px 12px;
}

.stat {
  display: flex;
  justify-content: space-between;
}

.label {
  opacity: 0.8;
}

.value {
  font-weight: bold;
}

.upgrade {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.upgrade-btn {
  padding: 6px 12px;
  border: 3px solid #3a220f;
  background: #ffd966;
  cursor: pointer;
  transition: all 0.15s;
}

.upgrade-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 0 8px rgba(255,255,255,0.7);
}

.upgrade-btn:disabled {
  background: #888;
  cursor: not-allowed;
}

.cost {
  display: flex;
  align-items: center;
  gap: 4px;
}

.cost img {
  width: 20px;
  image-rendering: pixelated;
}
</style>
