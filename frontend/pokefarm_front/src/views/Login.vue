<template>
  <div class="login-page">
    <div class="login-panel">
      <!-- 标题 -->
      <img
        class="title-img"
        src="@/assets/Texts/Title.png"
        alt="PokeFarm"
      />

      <!-- 随机宝可梦 -->
      <img
        class="pokemon-img"
        :src="pokemonSprite"
        alt="pokemon"
      />

      <!-- 输入框 -->
      <input
        v-model="username"
        class="input-box"
        placeholder="用户名"
      />
      <input
        v-model="password"
        type="password"
        class="input-box"
        placeholder="密码"
        autocomplete="current-password"
      />

      <!-- 登录按钮（主） -->
      <img
        class="action-btn main-btn"
        src="@/assets/Texts/Login.png"
        alt="login"
        @click="login"
      />

      <!-- 注册按钮（次） -->
      <img
        class="action-btn sub-btn"
        src="@/assets/Texts/Register.png"
        alt="register"
        @click="goRegister"
      />
    </div>
  </div>
</template>

<script>
import http from '@/api/http'

export default {
  name: 'Login',
  data() {
    return {
      username: '',
      password: '',
      pokemonSprite: ''
    }
  },
  mounted() {
    this.pickRandomPokemon()
  },
  methods: {
    pickRandomPokemon() {
      const id = Math.floor(Math.random() * 151) + 1
      const num = String(id).padStart(4, '0')
      this.pokemonSprite = new URL(
        `../assets/pokemons/${num}.png`,
        import.meta.url
      ).href
    },

    async login() {
    if (!this.username || !this.password) {
      alert('请输入用户名和密码')
      return
    }

    try {
      const res = await http.post(
        '/player/login',
        null,
        {
          params: {
            username: this.username,
            password: this.password
          }
        }
      )

      const playerId = res.data.player_id
      localStorage.setItem('player_id', playerId)
      this.$router.push('/farm')

    } catch (err) {
      // 读取后端返回的错误信息
      if (err.response && err.response.data) {
        alert(err.response.data.detail || '登录失败')
      } else {
        alert('无法连接服务器')
      }
    }
  },
    goRegister() {
      this.$router.push('/register')
    }
  }
}
</script>



<style scoped>
.login-page {
  width: 100vw;
  height: 100vh;
  background: #f2f2f2;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-panel {
  width: 360px;
  padding: 24px;
  border: 4px solid #222;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.title-img {
  width: 260px;
  margin-bottom: 16px;
}

.pokemon-img {
  width: 96px;
  image-rendering: pixelated;
  margin-bottom: 20px;
}

.input-box {
  width: 220px;
  padding: 8px;
  margin-bottom: 12px;
  border: 3px solid #222;
  font-size: 14px;
  outline: none;
}

.action-btn {
  cursor: pointer;
  image-rendering: pixelated;
  transition: transform 0.1s;
}

.main-btn {
  width: 150px;
  margin-top: 12px;
}

.sub-btn {
  width: 100px;
  margin-top: 8px;
  opacity: 0.85;
}

.action-btn:hover {
  transform: translateY(2px);
}
</style>
