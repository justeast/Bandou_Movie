<template>
    <div class="login-page">
        <div class="login-container">
            <h2>欢迎登录</h2>
            <login-form @success="handleLoginSuccess" />
            <div class="footer">
                <a-button type="link" @click="showPasswordResetRequestModal">
                    忘记密码？
                </a-button>
                <a-button type="link" @click="router.push('/')">
                    返回首页
                </a-button>
                <a-button type="link" @click="goToAdmin">
                    管理员登录
                </a-button>
            </div>
        </div>
        <!-- 密码重置请求模态框 -->
        <a-modal v-model:open="uiStore.showPasswordResetRequestModal" :destroyOnClose="true" title="密码重置请求"
            :footer="null" :width="400">
            <password-reset-request-form @success="handlePasswordResetRequestSuccess" />
        </a-modal>

        <!-- 密码重置确认模态框 -->
        <a-modal v-model:open="uiStore.showPasswordResetConfirmModal" :destroyOnClose="true" title="密码重置确认"
            :footer="null" :width="400">
            <password-reset-confirm-form :email="uiStore.resetEmail" @success="handlePasswordResetConfirmSuccess" />
        </a-modal>
    </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useUIStore } from '../stores/ui'
import { message } from 'ant-design-vue'
import LoginForm from '../components/LoginForm.vue'
import PasswordResetRequestForm from '../components/PasswordResetRequestForm.vue'
import PasswordResetConfirmForm from '../components/PasswordResetConfirmForm.vue'

const router = useRouter()
const userStore = useUserStore()
const uiStore = useUIStore();

// 跳转到Django Admin进行后台用户管理
const goToAdmin = () => {
    window.location.href = 'http://localhost:8000/admin'
}

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

// 显示密码重置请求模态框
const showPasswordResetRequestModal = () => {
    uiStore.showPasswordResetRequestModal = true;
};

// 密码重置请求成功处理
const handlePasswordResetRequestSuccess = (email) => {
    uiStore.setResetEmail(email); // 存储邮箱
    uiStore.showPasswordResetRequestModal = false;
    // 延迟打开确认模态框，确保旧定时器清理
    setTimeout(() => {
        uiStore.showPasswordResetConfirmModal = true;
    }, 300);
    message.success('验证码已发送至您的邮箱', 3);
};

// 密码重置确认成功处理
const handlePasswordResetConfirmSuccess = () => {
    uiStore.showPasswordResetConfirmModal = false;
    uiStore.clearResetEmail();
    uiStore.clearCodeExpiry();
    message.success('密码重置成功，请重新登录', 3);
};
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
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 16px;
}

.footer .ant-btn {
    margin: 0;
}
</style>