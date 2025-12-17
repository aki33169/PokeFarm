<template>
  <div class="build-mask">
    <div class="panel">
      <div class="panel-header">
        <span>建造</span>
        <button class="close" @click="$emit('close')">✕</button>
      </div>

      <!-- 建筑列表（横向滚动） -->
      <div class="building-list">
        <div
          class="building-item"
          v-for="b in buildings"
          :key="b.code"
          :class="{ active: current && current.code === b.code }"
          @click="select(b)"
        >
          <img :src="getBuildingSprite(b.sprite_url)" />
          <div class="name">{{ b.name }}</div>
        </div>
      </div>

      <!-- 详情 -->
      <div v-if="current" class="detail">
        <p class="desc">{{ current.description }}</p>

        <!-- 花费 -->
        <div class="costs">
          <div
            class="cost"
            v-for="(v, k) in current.cost"
            :key="k"
            :class="{ lack: resources[k] < v }"
          >
            <img :src="getIcon(k)" />
            <span>{{ v }}</span>
          </div>
        </div>

        <!-- 建造按钮 -->
        <button
          class="build-btn"
          :class="{ enabled: canBuild }"
          :disabled="!canBuild"
          @click="build"
        >
          <img src="@/assets/icons/build.png" />
          <span>建造</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import http from '@/api/http'

export default {
  props: {
    slot: Object,
    resources: Object
  },

  data() {
    return {
      buildings: [],
      current: null,
      building: false
    }
  },

  computed: {
    // 是否资源足够
    canBuild() {
      if (!this.current) return false
      return Object.entries(this.current.cost).every(
        ([k, v]) => (this.resources[k] ?? 0) >= v
      )
    }
  },

  mounted() {
    this.fetchBuildings()
  },

  methods: {
    async fetchBuildings() {
      const res = await http.get('/building/list')
      this.buildings = res.data
      this.current = res.data[0] || null
    },

    select(b) {
      this.current = b
    },

    async build() {
      if (!this.canBuild || this.building) return
      this.building = true

      try {
        await http.post('/farm/build', null, {
          params: {
            player_id: localStorage.getItem('player_id'),
            building_code: this.current.code,
          }
        })

        this.$emit('built')
        this.$emit('close')
      } catch (e) {
        alert(e.response?.data?.detail || '建造失败')
      } finally {
        this.building = false
      }
    },

    getIcon(code) {
      return new URL(`../assets/icons/${code}.png`, import.meta.url).href
    },

    getBuildingSprite(file) {
      return new URL(`../assets/buildings/${file}`, import.meta.url).href
    }
  }
}
</script>

<style scoped>
.build-mask {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 50;
}

.panel {
  width: 420px;
  background: #c49a6c;
  border: 4px solid #3a220f;
  padding: 12px;
  font-family: monospace;
}

/* 头部 */
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.close {
  background: #b33;
  color: white;
  border: none;
  width: 24px;
  height: 24px;
  cursor: pointer;
}

/* 建筑列表 */
.building-list {
  display: flex;
  overflow-x: auto;
  gap: 8px;
  padding-bottom: 6px;
  margin-bottom: 10px;
}

.building-item {
  width: 96px;
  background: #e3c08d;
  border: 2px solid #3a220f;
  text-align: center;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}

.building-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 6px rgba(255,255,255,0.6);
}

.building-item.active {
  outline: 3px solid #ffd966;
}

.building-item img {
  width: 64px;
  image-rendering: pixelated;
}

.name {
  font-size: 12px;
}

/* 描述 */
.desc {
  font-size: 13px;
  margin-bottom: 6px;
}

/* 花费 */
.costs {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
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

/* 建造按钮 */
.build-btn {
  width: 100%;
  padding: 6px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
  border: 3px solid #3a220f;
  background: #888;
  cursor: not-allowed;
  transition: all 0.15s;
}

.build-btn.enabled {
  background: #ffd966;
  cursor: pointer;
}

.build-btn.enabled:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 8px rgba(255,255,255,0.7);
}

.build-btn.enabled:active {
  transform: translateY(0);
  box-shadow: none;
}

.building-item.active {
  outline: 3px solid #ffd966;
  box-shadow: 0 0 10px rgba(255,217,102,0.8);
}

.build-btn img {
  width: 24px;
  image-rendering: pixelated;
}
</style>
