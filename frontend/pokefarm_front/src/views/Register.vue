<template>
  <div class="register-page">
    <div class="register-panel">
      <!-- 标题 -->
      <img
        class="title-img"
        src="@/assets/Texts/Title.png"
        alt="PokeFarm"
      />

      <!-- 输入框 -->
      <input
        v-model="username"
        class="input-box"
        placeholder="用户名"
      />

      <input
        v-model="nickname"
        class="input-box"
        placeholder="昵称（可选）"
      />

      <input
        v-model="password"
        type="password"
        class="input-box"
        placeholder="密码"
        autocomplete="current-password"
      />

      <input
        v-model="confirmPassword"
        type="password"
        class="input-box"
        placeholder="确认密码"
        autocomplete="new-password"
      />

      <!-- 注册按钮 -->
      <img
        class="action-btn main-btn"
        src="@/assets/Texts/Register.png"
        alt="register"
        @click="register"
      />

      <!-- 返回登录 -->
      <img
        class="action-btn back-btn"
        src="@/assets/Texts/Back.png"
        alt="back"
        @click="goLogin"
      />
    </div>
  </div>
</template>

<script>
import http from '@/api/http'

export default {
  name: 'Register',
  data() {
    return {
      username: '',
      nickname: '',
      password: '',
      confirmPassword: ''
    }
  },
  methods: {
    async register() {
      if (!this.username || !this.password) {
        alert('用户名和密码不能为空')
        return
      }

      if (this.password !== this.confirmPassword) {
        alert('两次密码不一致')
        return
      }

      try {
        await http.post(
          '/player/register',
          null,
          {
            params: {
              username: this.username,
              password: this.password,
              nickname: this.nickname || null
            }
          }
        )

        alert('注册成功，请登录')
        this.$router.push('/login')
      } catch (err) {
        if (err.response && err.response.data) {
          alert(err.response.data.detail || '注册失败')
        } else {
          alert('无法连接服务器')
        }
      }
    },

    goLogin() {
      this.$router.push('/login')
    }
  }
}
</script>

<style scoped>
.register-page {
  width: 100vw;
  height: 100vh;
  background: #f2f2f2;
  display: flex;
  align-items: center;
  justify-content: center;
}

.register-panel {
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
  margin-top: 14px;
}

.action-btn:hover {
  transform: translateY(2px);
}

.back-login {
  margin-top: 14px;
  font-size: 14px;
  cursor: pointer;
  color: #333;
}

.back-btn {
  width: 90px;
  margin-top: 14px;
  opacity: 0.85;
}

.back-btn:hover {
  opacity: 1;
}

</style>
