<template>
    <a-form :model="formState" name="loginForm" layout="vertical" @finish="handleSubmit" autocomplete="off">
        <a-form-item label="用户名" name="username" :rules="[{ required: true, message: '请输入用户名' }]">
            <a-input v-model:value="formState.username" />
        </a-form-item>

        <a-form-item label="密码" name="password" :rules="[{ required: true, message: '请输入密码' }]">
            <a-input-password v-model:value="formState.password" />
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
    username: '',
    password: ''
});

const loading = ref(false);

const handleSubmit = async () => {
    try {
        loading.value = true;
        const response = await axios.post('/api/user/login/', {
            username: formState.username,
            password: formState.password
        });

        localStorage.setItem('access_token', response.data.access);
        localStorage.setItem('refresh_token', response.data.refresh);
        localStorage.setItem('username', response.data.username);
        emit('success');
        emitter.emit('login-success'); // 全局广播登录成功
    } catch (error) {
        const errorMsg = error.response?.data?.detail ||
            error.response?.data?.error ||
            '登录失败';
        message.error(errorMsg);
    } finally {
        loading.value = false;
    }
};
</script>