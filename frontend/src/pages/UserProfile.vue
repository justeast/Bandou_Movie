<template>
    <div class="profile-container">
        <!-- 个人信息模块 -->
        <a-card title="个人信息" class="profile-card">
            <a-form :model="profileForm" layout="vertical">
                <!-- 头像上传 -->
                <a-form-item label="头像">
                    <div class="avatar-upload-container">
                        <a-upload ref="uploadRef" :custom-request="handleAvatarUpload" :show-upload-list="false"
                            accept=".jpg,.jpeg,.png">
                            <a-avatar :src="avatarUrl" :size="128" class="change-button" />
                        </a-upload>

                        <!-- 独立于上传组件的控制区域 -->
                        <div class="upload-controls">
                            <a-button type="link" @click="triggerAvatarUpload" class="change-button">
                                <UploadOutlined /> 更换头像
                            </a-button>
                            <div class="upload-tips">
                                <div>支持格式：JPEG/PNG</div>
                                <div>最大尺寸：5MB</div>
                            </div>
                        </div>
                    </div>
                </a-form-item>

                <!-- 基本信息 -->
                <a-form-item label="用户名" name="username" :rules="[
                    { required: true, message: '请输入用户名' },
                    { min: 3, max: 16, message: '用户名长度3-16个字符' },
                    { pattern: /^[\u4e00-\u9fa5a-zA-Z0-9_]+$/, message: '只能包含中文、字母、数字和下划线' }
                ]">
                    <a-input v-model:value="profileForm.username" />
                </a-form-item>

                <a-form-item label="邮箱" name="email" :rules="[
                    { required: true, message: '请输入邮箱地址' },
                    { type: 'email', message: '请输入有效的邮箱格式' }
                ]">
                    <a-input v-model:value="profileForm.email" />
                </a-form-item>

                <a-form-item label="电话">
                    <a-input v-model:value="profileForm.phone" />
                </a-form-item>

                <a-form-item>
                    <a-button type="primary" @click="updateProfile" :loading="profileLoading">
                        更新信息
                    </a-button>
                </a-form-item>
            </a-form>
        </a-card>

        <!-- 修改密码模块 -->
        <a-card title="修改密码" class="password-card">
            <a-form :model="passwordForm" layout="vertical" @finish="changePassword">
                <a-form-item label="原密码" name="old_password" :rules="[{ required: true, message: '请输入原密码' }]">
                    <a-input-password v-model:value="passwordForm.old_password" />
                </a-form-item>

                <a-form-item label="新密码" name="new_password" :rules="[{ required: true, message: '请输入新密码' }]">
                    <a-input-password v-model:value="passwordForm.new_password" />
                </a-form-item>

                <a-form-item label="确认新密码" name="confirm_password" :rules="[{ required: true, message: '请确认新密码' }]">
                    <a-input-password v-model:value="passwordForm.confirm_password" />
                </a-form-item>

                <a-form-item>
                    <a-button type="primary" html-type="submit" :loading="passwordLoading">
                        修改密码
                    </a-button>
                </a-form-item>
            </a-form>
        </a-card>
    </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import axios from '../utils/axios';
import { UploadOutlined } from '@ant-design/icons-vue';
import { getErrorMessage } from '../utils/errorHandler';
import { useUserStore } from '../stores/user';

const userStore = useUserStore();

const profileForm = reactive({
    username: '',
    email: '',
    phone: ''
});

const passwordForm = reactive({
    old_password: '',
    new_password: '',
    confirm_password: ''
});

const avatarUrl = ref('');
const profileLoading = ref(false);
const passwordLoading = ref(false);

const uploadRef = ref(null);
const triggerAvatarUpload = () => {
    // 通过组件引用触发上传
    const uploadElement = uploadRef.value?.$el?.querySelector('input[type="file"]');
    if (uploadElement) {
        uploadElement.click();
    } else {
        console.error('找不到上传输入框');
    }
};

// 获取用户信息
const fetchProfile = async () => {
    try {
        const response = await axios.get('/api/user/profile/');
        Object.assign(profileForm, response.data);
        avatarUrl.value = response.data.avatar_url;
    } catch (error) {
        message.error(getErrorMessage(error));
    }
};

// 更新个人信息
const updateProfile = async () => {
    try {
        profileLoading.value = true;
        await axios.patch('/api/user/profile/', profileForm);
        message.success('信息更新成功');
    } catch (error) {
        message.error(error.response?.data?.error || '更新失败');
    } finally {
        profileLoading.value = false;
    }
};

// 上传头像
const handleAvatarUpload = async ({ file }) => {
    const formData = new FormData();
    formData.append('avatar', file);

    try {
        await axios.patch('/api/user/avatar/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        await fetchProfile(); // 刷新头像
        message.success('头像更新成功');
        userStore.updateAvatar(avatarUrl.value);
    } catch (error) {
        message.error(getErrorMessage(error));
    }
};

// 修改密码
const changePassword = async () => {
    if (passwordForm.new_password !== passwordForm.confirm_password) {
        message.error('两次输入的新密码不一致');
        return;
    }

    try {
        passwordLoading.value = true;
        await axios.post('/api/user/change_password/', {
            old_password: passwordForm.old_password,
            new_password: passwordForm.new_password,
            confirm_password: passwordForm.confirm_password
        });
        message.success('密码修改成功，请重新登录');
        // 自动注销
        localStorage.clear();
        window.location.replace('/user/login')
    } catch (error) {
        message.error(error.response?.data?.detail || '密码修改失败');
    } finally {
        passwordLoading.value = false;
    }
};

onMounted(fetchProfile);
</script>

<style scoped>
.profile-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 24px;
}

.profile-card,
.password-card {
    margin-bottom: 24px;
}

:deep(.ant-card-head-title) {
    font-size: 18px;
    font-weight: 500;
}

/* 头像容器布局 */
.avatar-upload-container {
    display: inline-block;
    position: relative;
    text-align: center;
}

/* 隐藏原生上传控件 */
.avatar-upload-container :deep(.ant-upload) {
    display: block !important;
    margin: 0 auto;
}

.avatar-upload-container :deep(.ant-upload-list) {
    display: none;
}

/* 控制区域样式 */
.upload-controls {
    margin-top: 16px;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.change-button {
    padding: 0;
    height: auto;
    color: #1890ff;
}

.upload-tips {
    margin-top: 8px;
    font-size: 12px;
    line-height: 1.5;
    color: rgba(0, 0, 0, 0.45);
    text-align: center;
}

/* 交互优化 */
.change-button:hover {
    opacity: 0.8;
}
</style>