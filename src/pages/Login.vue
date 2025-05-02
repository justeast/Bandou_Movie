<template>
    <div class="login-page">
        <div class="login-container">
            <h2>欢迎登录</h2>
            <login-form @success="handleLoginSuccess" />
            <div class="footer">
                <a-button type="link" @click="router.push('/')">
                    返回首页
                </a-button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { message } from 'ant-design-vue'
import LoginForm from '../components/LoginForm.vue'

const router = useRouter()
const userStore = useUserStore()

const handleLoginSuccess = async () => {
    try {
        await userStore.fetchUserProfile()
        // 检查是否有重定向参数，如果有则跳转，否则返回上一页
        const redirect = router.currentRoute.value.query.redirect
        if (redirect) {
            router.push(redirect)
        } else {
            router.go(-1) // 返回上一页
        }
    } catch (error) {
        message.error('获取用户信息失败')
        console.log(error)
    }
}
</script>

<style scoped>
.login-page {
    display: flex;
    min-height: 100vh;
    align-items: center;
    justify-content: center;
    background: #f0f2f5;
}

.login-container {
    width: 400px;
    padding: 40px;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.footer {
    margin-top: 24px;
    text-align: center;
}
</style>