<template>
    <a-form :model="form" :rules="rules" @finish="handleSubmit">
        <a-form-item name="email">
            <a-input v-model:value="form.email" placeholder="请输入注册邮箱" />
        </a-form-item>
        <a-form-item>
            <a-button type="primary" html-type="submit" :loading="loading" block>
                发送验证码
            </a-button>
        </a-form-item>
    </a-form>
</template>

<script setup>
import { ref } from 'vue';
import { message } from 'ant-design-vue';
import axios from '../utils/axios';
import { useUIStore } from '../stores/ui';

const uiStore = useUIStore();

const emit = defineEmits(['success']);

const form = ref({
    email: '',
});

const rules = {
    email: [
        { required: true, message: '请输入邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
    ],
};

const loading = ref(false);

const handleSubmit = async () => {
    loading.value = true;
    try {
        const response = await axios.post('/api/user/reset_password/request/', {
            email: form.value.email,
        });
        if (response.status === 200) {
            // 解析 code_expiry（格式 "00:05:00"）为秒数
            const expiryStr = response.data.code_expiry;
            const [hours, minutes, seconds] = expiryStr.split(':').map(Number);
            const expirySeconds = hours * 3600 + minutes * 60 + seconds;
            uiStore.setCodeExpiry(expirySeconds);
            emit('success', form.value.email);
        }
    } catch (error) {
        if (error.response?.status === 429) {
            message.error('请等待60秒后再试', 3);
        } else {
            message.error(error.response?.data?.error || '发送验证码失败', 3);
        }
    } finally {
        loading.value = false;
    }
};
</script>