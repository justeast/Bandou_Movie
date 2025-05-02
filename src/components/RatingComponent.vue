<template>
    <div class="rating-container">
        <div class="rating-header">
            <span class="label">评分</span>
            <div @click="handleClick" class="rate-wrapper">
                <a-rate v-model:value="userRating" allow-half @change="handleRatingChange" class="star-rate"
                    :disabled="!isLoggedIn" />
            </div>
            <span v-if="isLoggedIn" class="rating-text">{{ ratingText }}</span>
            <span v-else class="login-tip">登录后可评分</span>
            <span class="avg-rating">平均分: {{ avgRating || '暂无' }} ({{ ratingCount }}人)</span>
        </div>
    </div>
</template>



<script setup>
import { ref, computed, onMounted, watch, onUnmounted } from 'vue';
import axios from '../utils/axios';
import { message } from 'ant-design-vue';
import { useRoute } from 'vue-router';
import { emitter } from '../utils/eventBus';
import { useUIStore } from '../stores/ui';
import { useUserStore } from '../stores/user';

const props = defineProps({
    movieId: {
        type: Number,
        required: true
    }
});

const userStore = useUserStore();
const uiStore = useUIStore();
const route = useRoute();
const userRating = ref(0);
const userRatingId = ref(null);
const avgRating = ref(null);
const ratingCount = ref(0);
const emit = defineEmits(['update:rating-stats']);
const isLoggedIn = computed(() => userStore.isLoggedIn);

// 未登录点击评分显示登录框
const handleClick = () => {
    if (!isLoggedIn.value) {
        showLogin();
    }
};

// 匹配对应的评分文本
const ratingText = computed(() => {
    const texts = ['很差', '较差', '还行', '推荐', '力荐'];
    return userRating.value ? texts[Math.ceil(userRating.value) - 1] : '点击评分';
});

// 添加对movieId的监听
watch(() => props.movieId, (newVal) => {
    if (newVal) {
        fetchAllData();
    }
});

// 获取全部数据
const fetchAllData = async () => {
    await Promise.all([
        fetchRatingStats(),
        fetchUserRating()
    ]);
};

// 获取评分统计
const fetchRatingStats = async () => {
    try {
        const res = await axios.get(`/api/movies/${props.movieId}/rating_stats/`);
        avgRating.value = res.data.avg_rating;
        ratingCount.value = res.data.rating_count;
        emit('update:rating-stats', {
            avgRating: avgRating.value,
            ratingCount: ratingCount.value
        });
    } catch (error) {
        console.error('获取评分统计失败:', error);
    }
};

// 获取用户评分
const fetchUserRating = async () => {
    if (!isLoggedIn.value) {
        userRating.value = 0;
        userRatingId.value = null;
        return;
    }

    try {
        const res = await axios.get(`/api/movies/${props.movieId}/my_rating/`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        userRating.value = res.data.rating;
        userRatingId.value = res.data.id;
    } catch (error) {
        if (error.response?.status === 404) {
            // 用户尚未评分
            userRating.value = 0;
            userRatingId.value = null;
        } else {
            console.error('获取用户评分失败:', error);
            message.error('获取评分失败');
        }
    }
};

// 处理评分变化
const handleRatingChange = async (value) => {
    if (!isLoggedIn.value) {
        showLogin();
        userRating.value = 0;
        return;
    }

    try {
        const response = await axios.post(
            `/api/movies/${props.movieId}/my_rating/`,
            { rating: value },
            {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            }
        );

        userRating.value = value;
        userRatingId.value = response.data.id;
        message.success('评分成功');
        await fetchRatingStats(); // 只更新统计信息
    } catch (error) {
        console.error('评分失败:', error);
        message.error('评分失败');
        await fetchUserRating(); // 恢复原评分状态
    }
};

// 显示登录框
const showLogin = () => {
    if (route.path !== '/') {
        uiStore.openLoginModal()
    } else {
        message.info('请先登录');
    }
};

// 登录成功后加载数据
const handleLoginSuccess = () => {
    fetchAllData();
};

// 首次加载时获取数据
onMounted(() => {
    emitter.on('login-success', handleLoginSuccess);
    fetchAllData();
});

// 页面销毁时取消监听，避免内存泄漏
onUnmounted(() => {
    emitter.off('login-success', handleLoginSuccess);
});
</script>

<style scoped>
.rating-container {
    margin: 20px 0;
    padding: 10px;
    background: #f9f9f9;
    border-radius: 8px;
}

.rating-header {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
}

.label {
    font-weight: bold;
}

.rate-wrapper {
    margin-left: 10px;
    cursor: pointer;
}



.rating-text {
    margin-left: 10px;
    color: #666;
}

.login-tip {
    margin-left: 10px;
    color: #999;
    font-size: 13px;
}

.avg-rating {
    margin-left: auto;
    color: #999;
    font-size: 14px;
}
</style>
