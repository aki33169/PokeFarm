<template>
  <div class="panel-mask">
    <div class="panel">

      <!-- ===== 头部 ===== -->
      <div class="panel-header">
        <span>派遣宝可梦</span>
        <button class="close" @click="$emit('close')">✕</button>
      </div>

      <!-- ===== 宝可梦列表 ===== -->
      <div class="pokemon-grid">
        <div
          v-for="p in pagedPokemons"
          :key="p.pokemon_id"
          class="pokemon-cell"
          :class="{ selected: selected && selected.pokemon_id === p.pokemon_id }"
          @click="onClickPokemon(p)"
        >
          <img :src="getPokemonSprite(p.species_id)" />
          <div class="lv">Lv.{{ p.level }}</div>
        </div>
      </div>

      <!-- ===== 分页 ===== -->
      <div class="pager" v-if="pageCount > 1">
        <button @click="page--" :disabled="page === 1">◀</button>
        <span>{{ page }} / {{ pageCount }}</span>
        <button @click="page++" :disabled="page === pageCount">▶</button>
      </div>

      <!-- ===== 派遣按钮 ===== -->
      <button
        class="dispatch-btn"
        :class="{ enabled: !!selected }"
        :disabled="!selected"
        @click="dispatch"
      >
        派遣
      </button>

    </div>
  </div>
</template>

<script>
import http from '@/api/http'

export default {
  props: {
    buildingId: { type: Number, required: true }
  },

  data() {
    return {
      pokemons: [],
      selected: null,
      page: 1,
      pageSize: 12
    }
  },

  computed: {
    pageCount() {
      return Math.ceil(this.pokemons.length / this.pageSize)
    },
    pagedPokemons() {
      const start = (this.page - 1) * this.pageSize
      return this.pokemons.slice(start, start + this.pageSize)
    }
  },

  mounted() {
    this.fetchPokemons()
  },

  methods: {
    async fetchPokemons() {
      const res = await http.get('/pokemon/idle', {
        params: { player_id: localStorage.getItem('player_id') }
      })
      this.pokemons = res.data
    },

    onClickPokemon(p) {
      // ⭐ 第二次点同一只 → 交给父组件打开详情
      if (this.selected && this.selected.pokemon_id === p.pokemon_id) {
        this.$emit('open-pokemon-detail', p.pokemon_id)
      } else {
        this.selected = p
      }
    },

    async dispatch() {
      await http.post('/farm/assign', null, {
        params: {
          player_id: localStorage.getItem('player_id'),
          pokemon_id: this.selected.pokemon_id,
          building_instance_id: this.buildingId
        }
      })
      this.$emit('dispatched')
      this.$emit('close')
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
  z-index: 70;
}

.panel {
  width: 520px;
  background: #c49a6c;
  border: 4px solid #3a220f;
  padding: 12px;
  font-family: monospace;
}

/* 头部 */
.panel-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.close {
  background: #b33;
  color: #fff;
  border: none;
  width: 24px;
  cursor: pointer;
}

/* 网格 */
.pokemon-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  padding: 8px;
}

.pokemon-cell {
  background: rgba(255,255,255,0.2);
  border: 2px solid #3a220f;
  text-align: center;
  cursor: pointer;
  padding: 6px;
}

.pokemon-cell.selected {
  outline: 3px solid #ffd966;
}

.pokemon-cell img {
  width: 48px;
  image-rendering: pixelated;
}

.lv {
  font-size: 12px;
}

/* 分页 */
.pager {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin: 8px 0;
}

/* 派遣按钮 */
.dispatch-btn {
  width: 100%;
  padding: 6px;
  border: 3px solid #3a220f;
  background: #888;
  cursor: not-allowed;
  transition: all 0.15s;
}

.dispatch-btn.enabled {
  background: #ffd966;
  cursor: pointer;
}

.dispatch-btn.enabled:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 8px rgba(255,255,255,0.7);
}
</style>
