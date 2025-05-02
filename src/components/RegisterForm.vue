<template>
    <a-form :model="formState" name="registerForm" layout="vertical" @finish="handleSubmit" autocomplete="off">
        <!-- 用户名 -->
        <a-form-item label="用户名" name="username" :rules="[
            { required: true, message: '请输入用户名' },
            { min: 4, max: 16, message: '用户名长度4-16个字符' },
            { pattern: /^[\u4e00-\u9fa5a-zA-Z0-9_]+$/, message: '只能包含中文、字母、数字和下划线' }
        ]">
            <a-input v-model:value="formState.username" placeholder="请输入用户名" allow-clear>
                <template #prefix>
                    <user-outlined type="user" />
                </template>
            </a-input>
        </a-form-item>

        <!-- 邮箱 -->
        <a-form-item label="邮箱" name="email" :rules="[
            { required: true, message: '请输入邮箱' },
            { type: 'email', message: '邮箱格式不正确' }
        ]">
            <a-input v-model:value="formState.email" placeholder="请输入邮箱" allow-clear>
                <template #prefix>
                    <mail-outlined type="mail" />
                </template>
            </a-input>
        </a-form-item>

        <!-- 密码 -->
        <a-form-item label="密码" name="password" :rules="[
            { required: true, message: '请输入密码' },
            { min: 8, message: '至少需要8个字符' },
            {
                validator: validatePassword,
                trigger: 'change'
            }
        ]">
            <a-input-password v-model:value="formState.password" placeholder="请输入密码" allow-clear>
                <template #prefix>
                    <lock-outlined type="lock" />
                </template>
            </a-input-password>
        </a-form-item>

        <!-- 确认密码 -->
        <a-form-item label="确认密码" name="confirmPassword" :rules="[
            { required: true, message: '请再次输入密码' },
            {
                validator: validateConfirmPassword,
                trigger: 'change'
            }
        ]">
            <a-input-password v-model:value="formState.confirmPassword" placeholder="请确认密码" allow-clear>
                <template #prefix>
                    <safety-certificate-outlined type="safety-certificate" />
                </template>
            </a-input-password>
        </a-form-item>

        <!-- 手机号 -->
        <a-form-item label="手机号（可选）" name="phone" :rules="[
            {
                pattern: /^1[3-9]\d{9}$/,
                message: '请输入有效的手机号码'
            }
        ]">
            <a-input v-model:value="formState.phone" placeholder="请输入手机号" allow-clear>
                <template #prefix>
                    <mobile-outlined type="mobile" />
                </template>
            </a-input>
        </a-form-item>

        <!-- 注册按钮 -->
        <a-form-item>
            <a-button type="primary" html-type="submit" block :loading="loading" size="large">
                {{ loading ? '注册中...' : '立即注册' }}
            </a-button>
        </a-form-item>
    </a-form>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import {
    UserOutlined,
    MailOutlined,
    LockOutlined,
    SafetyCertificateOutlined,
    MobileOutlined
} from '@ant-design/icons-vue'
import axios from '../utils/axios'

const emit = defineEmits(['success'])

const formState = reactive({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    phone: ''
})

const loading = ref(false)

// 密码复杂度验证
const validatePassword = async (_rule, value) => {
    if (!value) return Promise.reject()
    if (value.length < 8) return Promise.reject('密码至少8个字符')
    if (!/[A-Z]/.test(value)) return Promise.reject('需包含至少一个大写字母')
    if (!/[a-z]/.test(value)) return Promise.reject('需包含至少一个小写字母')
    if (!/[0-9]/.test(value)) return Promise.reject('需包含至少一个数字')
    return Promise.resolve()
}

// 确认密码验证
const validateConfirmPassword = async (_rule, value) => {
    if (value !== formState.password) {
        return Promise.reject('两次输入的密码不一致')
    }
    return Promise.resolve()
}

// 提交处理
const handleSubmit = async () => {
    try {
        loading.value = true
        const response = await axios.post('/api/user/register/', {
            username: formState.username,
            email: formState.email,
            password: formState.password,
            confirm_password: formState.confirmPassword,
            phone: formState.phone
        })

        message.success('注册成功')
        emit('success', response.data)
    } catch (error) {
        const errorData = error.response?.data || {}
        const errorMessage = parseErrorMessage(errorData)
        message.error(errorMessage)
    } finally {
        loading.value = false
    }
}

// 错误信息解析
const parseErrorMessage = (errorData) => {
    const errorMap = {
        username: {
            'unique': '用户名已被注册',
            'invalid': '用户名格式不正确'
        },
        email: {
            'unique': '邮箱已被注册',
            'invalid': '邮箱格式不正确'
        },
        password: {
            'too_common': '密码安全性不足',
            'numeric': '密码不能全为数字'
        },
        phone: {
            'invalid': '手机号格式不正确'
        }
    }

    for (const [field, errors] of Object.entries(errorData)) {
        if (errorMap[field]) {
            for (const [errorType, message] of Object.entries(errorMap[field])) {
                if (errors.includes(errorType)) return message
            }
        }
    }

    return '注册失败，请检查输入信息'
}
</script>

<style scoped>
/* 自定义表单项间距 */
:deep(.ant-form-item) {
    margin-bottom: 20px;
}

/* 调整输入框前缀图标颜色 */
:deep(.ant-input-prefix) {
    color: rgba(0, 0, 0, 0.25);
}

/* 适配移动端 */
@media (max-width: 576px) {
    :deep(.ant-form-item-label) {
        padding-bottom: 4px !important;
    }

    :deep(.ant-btn-lg) {
        height: 40px;
        font-size: 14px;
    }
}
</style>