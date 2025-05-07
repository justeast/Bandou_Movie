<template>
    <a-form :model="formState" name="loginForm" layout="vertical" @finish="handleSubmit" autocomplete="off">
        <a-form-item label="用户名或邮箱" name="loginId" :rules="[
            { required: true, message: '请输入用户名或邮箱' },
            { validator: validateLoginId, trigger: 'blur' }
        ]">
            <a-input v-model:value="formState.loginId" placeholder="请输入用户名或邮箱" />
        </a-form-item>

        <a-form-item label="密码" name="password" :rules="[{ required: true, message: '请输入密码' }]">
            <a-input-password v-model:value="formState.password" placeholder="请输入密码" />
        </a-form-item>

        <a-button type="primary" html-type="submit" block :loading="loading">
            登录
        </a-button>
    </a-form>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { message } from 'ant-design-vue';
import axios from '../utils/axios';
import { emitter } from '../utils/eventBus';

const emit = defineEmits(['success']);

const formState = reactive({
    loginId: '',
    password: ''
});

const loading = ref(false);

// 验证用户名或邮箱格式
const validateLoginId = async (_rule, value) => {
    if (!value) {
        return Promise.reject('请输入用户名或邮箱');
    }
    // 如果输入包含 @，验证邮箱格式
    if (value.includes('@')) {
        const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!emailRegex.test(value)) {
            return Promise.reject('请输入有效的邮箱地址');
        }
    }
    // 如果不包含 @，视为用户名，无格式限制
    return Promise.resolve();
};

const handleSubmit = async () => {
    try {
        loading.value = true;
        // 根据输入判断是用户名还是邮箱
        const isEmail = formState.loginId.includes('@');
        const requestData = {
            [isEmail ? 'email' : 'username']: formState.loginId,
            password: formState.password
        };
        const response = await axios.post('/api/user/login/', requestData);

        localStorage.setItem('access_token', response.data.access);
        localStorage.setItem('refresh_token', response.data.refresh);
        localStorage.setItem('username', response.data.username);
        emit('success');
        emitter.emit('login-success'); // 全局广播登录成功
    } catch (error) {
        const errorMsg = error.response?.data?.error ||
            error.response?.data?.detail ||
            '登录失败';
        message.error(errorMsg);
    } finally {
        loading.value = false;
    }
};
</script>