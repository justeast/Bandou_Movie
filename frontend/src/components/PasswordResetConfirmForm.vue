<template>
    <div style="margin-bottom: 16px;">
        已发送验证码至：{{ props.email }}
        <span v-if="remainingTime > 0">
            （剩余时间：{{ formatTime }}）
        </span>
        <span v-else style="color: red;">验证码已过期，请重新请求</span>
    </div>
    <a-form :model="form" :rules="rules" @finish="handleSubmit">
        <a-form-item name="code">
            <a-input v-model:value="form.code" placeholder="请输入6位验证码" :maxlength="6" />
        </a-form-item>
        <a-form-item name="new_password">
            <a-input-password v-model:value="form.new_password" placeholder="请输入新密码（至少8位）" />
        </a-form-item>
        <a-form-item name="confirm_password">
            <a-input-password v-model:value="form.confirm_password" placeholder="请再次输入新密码" />
        </a-form-item>
        <a-form-item>
            <a-button type="primary" html-type="submit" :loading="loading" block>
                确认重置密码
            </a-button>
        </a-form-item>
        <div style="text-align: center; margin-top: 16px;">
            <a-button type="link" @click="returnToRequest">重新输入邮箱</a-button>
        </div>
    </a-form>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { message } from 'ant-design-vue';
import axios from '../utils/axios';
import { useUIStore } from '../stores/ui';

const uiStore = useUIStore();

const props = defineProps({
    email: {
        type: String,
        required: true,
    },
});

const emit = defineEmits(['success']);

const form = ref({
    code: '',
    new_password: '',
    confirm_password: '',
});

const validatePassword = async (_rule, value) => {
    if (!value) return Promise.reject('请输入新密码');
    if (value.length < 8) return Promise.reject('密码至少8个字符');
    if (!/[A-Z]/.test(value)) return Promise.reject('需包含至少一个大写字母');
    if (!/[a-z]/.test(value)) return Promise.reject('需包含至少一个小写字母');
    if (!/[0-9]/.test(value)) return Promise.reject('需包含至少一个数字');
    return Promise.resolve();
};

const rules = {
    code: [
        { required: true, message: '请输入验证码', trigger: 'blur' },
        { len: 6, message: '验证码必须为6位', trigger: 'blur' },
    ],
    new_password: [
        { validator: validatePassword, trigger: 'blur' },
    ],
    confirm_password: [
        { required: true, message: '请再次输入新密码', trigger: 'blur' },
        {
            validator: (_rule, value) => {
                if (value !== form.value.new_password) {
                    return Promise.reject('两次输入的密码不一致');
                }
                return Promise.resolve();
            },
            trigger: 'blur',
        },
    ],
};

const loading = ref(false);
const remainingTime = ref(0);
let timer = null;

const formatTime = computed(() => {
    const minutes = Math.floor(remainingTime.value / 60);
    const seconds = remainingTime.value % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
});

const handleSubmit = async () => {
    loading.value = true;
    try {
        const response = await axios.post('/api/user/reset_password/confirm/', {
            email: props.email,
            code: form.value.code,
            new_password: form.value.new_password,
        });
        if (response.status === 200) {
            uiStore.clearCodeExpiry();
            emit('success');
        }
    } catch (error) {
        message.error(error.response?.data?.error || '密码重置失败', 3);
    } finally {
        loading.value = false;
    }
};

const returnToRequest = () => {
    if (timer) {
        clearInterval(timer);
        timer = null;
    }
    uiStore.showPasswordResetConfirmModal = false;
    uiStore.showPasswordResetRequestModal = true;
    uiStore.clearCodeExpiry();
};

const startTimer = () => {
    if (timer) {
        clearInterval(timer);
        timer = null;
    }
    timer = setInterval(() => {
        if (remainingTime.value > 0) {
            remainingTime.value--;
            uiStore.setCodeExpiry(remainingTime.value);
        } else {
            clearInterval(timer);
            timer = null;
        }
    }, 1000);
};

onMounted(() => {
    // 校验时间戳，确保状态有效
    if (uiStore.codeExpiryTimestamp && (Date.now() - uiStore.codeExpiryTimestamp) > 310000) {
        uiStore.clearCodeExpiry();
        remainingTime.value = 0;
        message.warning('验证码已过期，请重新请求', 3);
    } else {
        remainingTime.value = Math.max(0, uiStore.codeExpirySeconds);
    }
    if (!props.email) {
        message.error('请重新开始密码重置流程', 3);
        uiStore.showPasswordResetConfirmModal = false;
        uiStore.showPasswordResetRequestModal = true;
        uiStore.clearCodeExpiry();
        return;
    }
    if (remainingTime.value === 0) {
        message.warning('验证码可能已过期，请重新请求', 3);
    } else {
        startTimer();
    }
});

onUnmounted(() => {
    if (timer) {
        clearInterval(timer);
        timer = null;
    }
});

// 监听 codeExpirySeconds，确保实时更新
watch(() => uiStore.codeExpirySeconds, (newVal) => {
    if (uiStore.codeExpiryTimestamp && (Date.now() - uiStore.codeExpiryTimestamp) <= 310000) {
        remainingTime.value = Math.max(0, newVal);
        if (newVal > 0 && !timer) {
            startTimer();
        }
    } else {
        remainingTime.value = 0;
    }
}, { immediate: true });
</script>