<template>
  <div class="panel-mask">
    <div class="panel">

      <!-- ===== 头部 ===== -->
      <div class="panel-header">
        <div class="title">
          {{ localBuilding.name }} Lv.{{ localBuilding.level }}
        </div>

        <button
          class="game-btn icon-btn"
          :class="{ enabled: true }"
          @click="demolish"
        >
          <img :src="getIcon('build')" />
        </button>

        <button class="close" @click="$emit('close')">✕</button>
      </div>

      <!-- ===== 建筑简介 ===== -->
      <div class="desc" v-if="localBuilding.description">
        {{ localBuilding.description }}
      </div>

      <!-- ===== 产能（仅产出型建筑显示）===== -->
      <div class="output" v-if="isProducer">
        <span>产出：</span>
        <img :src="getIcon(localBuilding.output_resource)" />
        <span class="val">{{ outputPerHour }} / h</span>
      </div>

      <!-- ===== 派遣槽位 ===== -->
      <div class="slots">
        <div
          v-for="i in totalSlots"
          :key="i"
          class="slot-wrapper"
        >
          <!-- 已派遣 -->
          <template v-if="workers[i - 1]">
            <div
              class="slot"
              @click="openPokemonDetail(workers[i - 1].pokemon_id)"
            >
              <img
                class="pokemon"
                :src="getPokemonSprite(workers[i - 1].species_id)"
              />
            </div>

            <button
              class="game-btn enabled"
              @click="remove(workers[i - 1].pokemon_id)"
            >
              撤出
            </button>
          </template>

          <!-- 空位 -->
          <template v-else>
            <button
              class="slot empty game-btn enabled slot-add"
              @click="dispatch"
            >
              +
            </button>
          </template>
        </div>
      </div>

      <!-- ===== 升级消耗 ===== -->
      <div v-if="localBuilding.upgrade_cost" class="costs">
        <div
          class="cost"
          v-for="(v, k) in localBuilding.upgrade_cost"
          :key="k"
          :class="{ lack: resources[k] < v }"
        >
          <img :src="getIcon(k)" />
          <span>{{ v }}</span>
        </div>
      </div>

      <!-- ===== 升级按钮 / 满级提示 ===== -->
      <button
        v-if="localBuilding.upgrade_cost"
        class="game-btn"
        :class="{ enabled: canUpgrade }"
        :disabled="!canUpgrade"
        @click="upgrade"
      >
        升级
      </button>

      <button
        v-else
        class="game-btn"
        disabled
      >
        已达到最大等级
      </button>

    </div>

    <!-- 宝可梦详情 -->
    <PokemonDetailPanel
      v-if="showPokemonDetail"
      :pokemon-id="detailPokemonId"
      @close="closePokemonDetail"
    />
  </div>
</template>

<script>
import http from '@/api/http'
import PokemonDetailPanel from '@/components/PokemonDetailPanel.vue'

export default {
  components: { PokemonDetailPanel },

  props: {
    building: { type: Object, required: true },
    resources: { type: Object, required: true }
  },

  data() {
    return {
      localBuilding: {},
      showPokemonDetail: false,
      detailPokemonId: null
    }
  },

  computed: {
    workers() {
      return this.localBuilding.workers || []
    },

    // ⭐ 核心改动：真实可派遣槽位数
    totalSlots() {
      return (
        (this.localBuilding.base_slots ?? 0) +
        (this.localBuilding.slot_bonus ?? 0)
      )
    },

    canUpgrade() {
      if (!this.localBuilding.upgrade_cost) return false
      return Object.entries(this.localBuilding.upgrade_cost).every(
        ([k, v]) => (this.resources?.[k] ?? 0) >= v
      )
    },

    isProducer() {
      return !!this.localBuilding.output_resource
    },

    outputPerHour() {
      const v = this.localBuilding.output_per_hour
      if (v === null || v === undefined) return this.localBuilding.output_base ?? 0
      return v
    }
  },

  watch: {
    building: {
      immediate: true,
      deep: true,
      handler(val) {
        this.localBuilding = JSON.parse(JSON.stringify(val || {}))
      }
    }
  },

  mounted() {
    this.fetchBuildingLatest()
  },

  methods: {
    dispatch() {
      this.$emit('dispatch', this.localBuilding.id)
    },

    openPokemonDetail(pokemonId) {
      this.detailPokemonId = pokemonId
      this.showPokemonDetail = true
    },

    closePokemonDetail() {
      this.showPokemonDetail = false
      this.detailPokemonId = null
    },

    async fetchBuildingLatest() {
      try {
        const res = await http.get('/farm/state', {
          params: { player_id: localStorage.getItem('player_id') }
        })
        const latest = (res.data.buildings || []).find(
          b => b.id === this.localBuilding.id
        )
        if (latest) this.localBuilding = latest
      } catch {}
    },

    async remove(pokemonId) {
      if (this.localBuilding.workers) {
        this.localBuilding.workers = this.localBuilding.workers.filter(
          w => w.pokemon_id !== pokemonId
        )
      }

      await http.post('/farm/remove', null, {
        params: {
          player_id: localStorage.getItem('player_id'),
          pokemon_id: pokemonId
        }
      })

      this.$emit('refresh')
      await this.fetchBuildingLatest()
    },

    async upgrade() {
      if (!this.canUpgrade) return
      await http.post('/farm/upgrade', null, {
        params: {
          player_id: localStorage.getItem('player_id'),
          building_instance_id: this.localBuilding.id
        }
      })
      this.$emit('refresh')
      await this.fetchBuildingLatest()
    },

    async demolish() {
      if (!confirm('确定要拆除该建筑吗？')) return
      await http.post('/farm/demolish', null, {
        params: {
          player_id: localStorage.getItem('player_id'),
          building_instance_id: this.localBuilding.id
        }
      })
      this.$emit('refresh')
      this.$emit('close')
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
.panel-mask {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 60;
}

.panel {
  width: 420px;
  max-height: 520px;          /* ⭐ 防止整体被撑爆 */
  background: #c49a6c;
  border: 4px solid #3a220f;
  padding: 12px;
  font-family: monospace;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title {
  font-size: 16px;
  flex: 1;
}

.desc {
  margin: 6px 0 8px;
  font-size: 13px;
  opacity: 0.85;
}

.close {
  background: #b33;
  color: #fff;
  border: none;
  width: 24px;
  height: 24px;
  cursor: pointer;
}

.output {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 10px 0;
}

.output img {
  width: 20px;
  image-rendering: pixelated;
}

.slots {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  max-height: 200px;          /* ⭐ 槽位区滚动 */
  overflow-y: auto;
  margin-bottom: 8px;
}

.slot-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.slot {
  width: 72px;
  height: 72px;
  background: #e3c08d;
  border: 2px solid #3a220f;
  display: flex;
  align-items: center;
  justify-content: center;
}

.slot.empty {
  font-size: 32px;
  color: #6b4a2b;
  opacity: 0.6;
}

.pokemon {
  width: 48px;
  image-rendering: pixelated;
}

.costs {
  display: flex;
  gap: 8px;
  margin: 12px 0;
}

.cost {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  background: #e3c08d;
  border: 2px solid #3a220f;
}

.cost.lack {
  background: #c97b7b;
}

.cost img {
  width: 20px;
  image-rendering: pixelated;
}

.game-btn {
  width: 100%;
  padding: 6px;
  border: 3px solid #3a220f;
  background: #888;
  cursor: not-allowed;
  transition: all 0.15s;
  font-family: monospace;
}

.game-btn.enabled {
  background: #ffd966;
  cursor: pointer;
}

.game-btn.enabled:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 8px rgba(255,255,255,0.7);
}

.icon-btn {
  width: auto;
  padding: 4px;
}

.icon-btn img {
  width: 22px;
  image-rendering: pixelated;
}

.slot-add {
  cursor: pointer;
  transition: all 0.15s;
  width: 72px;
  height: 72px;
  font-size: 32px;
  padding: 0;
}

.slot-add:hover {
  background: #ffd966;
  transform: translateY(-2px);
  box-shadow: 0 0 8px rgba(255,255,255,0.7);
}
</style>
