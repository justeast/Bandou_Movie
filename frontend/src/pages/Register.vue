<template>
    <div class="register-page">
        <a-card class="register-card">
            <h2 class="register-title">新用户注册</h2>
            <register-form @success="handleSuccess" />
            <div class="register-footer">
                <span>已有账号？</span>
                <a-button type="link" @click="router.push('/user/login')">立即登录</a-button>
            </div>
        </a-card>
    </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import RegisterForm from '../components/RegisterForm.vue'

const router = useRouter()

const handleSuccess = () => {
    router.push({
        path: '/user/login',
        query: { registered: true }
    })
}
</script>

<style scoped>
.register-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #f0f2f5;
    padding: 20px;
}

.register-card {
    width: 100%;
    max-width: 800px;
    padding: 24px 32px;
}

.register-title {
    text-align: center;
    margin-bottom: 24px;
    font-size: 22px;
    color: rgba(0, 0, 0, 0.85);
}

.register-footer {
    margin-top: 24px;
    text-align: center;
    color: rgba(0, 0, 0, 0.45);
}

:deep(.ant-form-item) {
    margin-bottom: 20px;
}
</style>