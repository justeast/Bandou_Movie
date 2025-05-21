<template>
    <a-page-header title="为您推荐" class="recommend-header">
        <!-- 登录提示 -->
        <a-alert v-if="isAnonymous" type="info" show-icon class="recommend-alert" :message="alertMessage" banner>
            <template #action>
                <a-button type="primary" size="small" @click="handleLogin">立即登录</a-button>
            </template>
        </a-alert>

        <!-- 推荐内容 - 左右布局 -->
        <a-card class="recommend-card">
            <a-list item-layout="horizontal" :data-source="recommendations" :loading="loading">
                <template #renderItem="{ item }">
                    <a-list-item class="movie-item" @click="goToMovieDetail(item.id)">
                        <div class="movie-container">
                            <!-- 左侧图片 -->
                            <div class="movie-poster">
                                <img :src="cachedImage(item.cover_url)" alt="movie cover" class="movie-cover"
                                    @error="handleImageError" />
                            </div>

                            <!-- 右侧内容 -->
                            <div class="movie-content">
                                <h3 class="movie-title">{{ item.title }}</h3>

                                <!-- 基本信息行 -->
                                <div class="movie-basic-info">
                                    <span class="release-date" v-if="item.release_time">
                                        <calendar-outlined /> {{ formatDate(item.release_time) }}
                                    </span>
                                    <span class="type" v-if="item.type">
                                        <tag-outlined /> {{ item.type }}
                                    </span>
                                </div>

                                <!-- 评分 -->
                                <div class="movie-meta">
                                    <template v-if="item.score">
                                        <a-rate :value="item.score" allow-half disabled />
                                        <span class="score">{{ item.score.toFixed(1) }}</span>
                                    </template>
                                    <template v-else>
                                        <span class="no-rating">
                                            <question-circle-outlined /> 暂无评分
                                        </span>
                                    </template>
                                </div>

                                <!-- 导演和主演 -->
                                <div class="movie-crew">
                                    <div class="crew-item" v-if="item.director">
                                        <span class="crew-label">导演：</span>
                                        <span class="crew-value">{{ item.director }}</span>
                                    </div>
                                    <div class="crew-item" v-if="item.starring">
                                        <span class="crew-label">主演：</span>
                                        <span class="crew-value">
                                            {{ formatActors(item.starring) }}
                                            <span v-if="showMoreActors(item.starring)" class="more-actors">
                                                等{{ countActors(item.starring) - 5 }}人
                                            </span>
                                        </span>
                                    </div>
                                </div>

                                <!-- 简介 -->
                                <p class="movie-desc" v-if="item.brief_introduction">
                                    {{ item.brief_introduction }}
                                </p>
                            </div>
                        </div>
                    </a-list-item>
                </template>
            </a-list>
        </a-card>
    </a-page-header>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useUserStore } from '../stores/user';
import { useRouter, useRoute } from 'vue-router';
import { CalendarOutlined, TagOutlined, QuestionCircleOutlined } from '@ant-design/icons-vue';
import axios from '../utils/axios';
import { message } from 'ant-design-vue';
import DefaultMovieCover from '../assets/default-movie-cover.jpg'

const router = useRouter();
const route = useRoute()
const recommendations = ref([]);
const isAnonymous = ref(false); // 是否为匿名用户(即未登录)
const alertMessage = ref('');
const loading = ref(false);
const imageCache = ref({});

const userStore = useUserStore();

// 默认图片路径
const DEFAULT_IMAGE = DefaultMovieCover

// 初始化图片缓存
try {
    const cache = localStorage.getItem('imageCache');
    if (cache) imageCache.value = JSON.parse(cache);
} catch (e) {
    console.warn('无法加载图片缓存:', e);
}

// 图片缓存处理
const cachedImage = (url) => {
    if (!url) return DEFAULT_IMAGE; // 无 URL 时返回默认图片

    // 检查是否是本地上传的图片（以/media/开头）
    if (url.startsWith('/media/')) {
        // 本地图片直接返回完整URL
        return `http://127.0.0.1:8000${url}`;
    }

    // 外部图片使用缓存和代理
    if (imageCache.value[url]) return imageCache.value[url]; // 返回缓存的 URL

    // 缓存代理 URL
    const proxyUrl = `http://127.0.0.1:8000/proxy_image/?url=${encodeURIComponent(url)}`;
    imageCache.value[url] = proxyUrl;

    // 保存缓存到 localStorage
    try {
        localStorage.setItem('imageCache', JSON.stringify(imageCache.value));
    } catch (e) {
        console.warn('localStorage 空间不足，清空缓存');
        localStorage.removeItem('imageCache');
        console.log(e);
    }

    return proxyUrl;
};

// 处理图片加载失败
const handleImageError = (e) => {
    const img = e.target;
    const originalUrl = decodeURIComponent(
        img.src.split('url=')[1] || img.src
    );

    // 设置默认图片并更新缓存
    imageCache.value[originalUrl] = DEFAULT_IMAGE;
    img.src = DEFAULT_IMAGE;
    img.onerror = null; // 清除错误事件，防止重复触发

    // 更新 localStorage
    try {
        localStorage.setItem('imageCache', JSON.stringify(imageCache.value));
    } catch (e) {
        console.warn('localStorage 空间不足，清空缓存');
        localStorage.removeItem('imageCache');
        console.log(e);
    }
};

// 日期格式化
const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' });
};

// 主演处理逻辑
const formatActors = (actorsStr) => {
    if (!actorsStr) return '';
    const actors = actorsStr.split('/').filter(a => a.trim());
    return actors.slice(0, 5).join(' / ');
};

const showMoreActors = (actorsStr) => {
    if (!actorsStr) return false;
    return countActors(actorsStr) > 5;
};

const countActors = (actorsStr) => {
    if (!actorsStr) return 0;
    return actorsStr.split('/').filter(a => a.trim()).length;
};

// 添加监听器
watch(() => route.query.fromLogin, (newVal) => {
    if (newVal === 'true') {
        fetchRecommendations()
        // 清除参数避免重复刷新
        router.replace({ query: {} })
    }
})

// 监听登录状态变化
watch(() => userStore.isLoggedIn, (newVal) => {
    if (newVal) {
        fetchRecommendations()
        isAnonymous.value = false
    }
})

// 登录跳转
const handleLogin = () => {
    router.push({
        path: '/user/login',
        query: {
            redirect: `${router.currentRoute.value.path}?fromLogin=true`
        }
    })
};

// 获取推荐电影
const fetchRecommendations = async () => {
    try {
        loading.value = true;
        const response = await axios.get('/api/movies/recommend/');

        if (response.data.is_anonymous) {
            isAnonymous.value = true;
            alertMessage.value = response.data.message;
            recommendations.value = response.data.movies.map(movie => ({
                ...movie,
                tags: movie.type ? movie.type.split('/') : []
            }));
        } else {
            isAnonymous.value = false;
            recommendations.value = response.data.map(movie => ({
                ...movie,
                tags: movie.type ? movie.type.split('/') : []
            }));
        }
    } catch (error) {
        message.error('推荐加载失败');
        console.error('推荐加载失败:', error);
    } finally {
        loading.value = false;
    }
};

const goToMovieDetail = (movieId) => {
    router.push({
        name: 'MovieDetail',
        params: { id: movieId },
        query: { from: 'recommend' } // 添加来源标识，方便面包屑处理
    });
};

onMounted(fetchRecommendations);
</script>

<style scoped>
.movie-item {
    padding: 16px 0;
    border-bottom: 1px solid #f0f0f0;
    cursor: pointer;
    transition: background-color 0.3s;
}

.movie-item:hover {
    background-color: #f5f5f5;
}

.movie-container {
    display: flex;
    gap: 20px;
    width: 100%;
}

.movie-poster {
    flex: 0 0 180px;
}

.movie-cover {
    width: 100%;
    height: 240px;
    object-fit: cover;
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s ease;
}

.movie-cover:hover {
    transform: scale(1.03);
}

.movie-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    gap: 10px;
}

/* 基本信息行 */
.movie-basic-info {
    display: flex;
    align-items: center;
    gap: 16px;
    font-size: 13px;
    color: rgba(0, 0, 0, 0.65);
    margin-bottom: 4px;
}

.movie-basic-info span {
    display: flex;
    align-items: center;
    gap: 4px;
}

/* 评分 */
.movie-meta {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
}

.score {
    font-size: 16px;
    color: #faad14;
    margin-left: 8px;
}

.no-rating {
    color: rgba(0, 0, 0, 0.45);
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 4px;
}

/* 导演和主演 */
.movie-crew {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 13px;
    color: rgba(0, 0, 0, 0.85);
}

.crew-item {
    display: flex;
    line-height: 1.4;
}

.crew-label {
    color: rgba(0, 0, 0, 0.45);
    flex: 0 0 40px;
}

.crew-value {
    flex: 1;
}

.more-actors {
    color: rgba(0, 0, 0, 0.45);
    font-size: 0.9em;
    margin-left: 4px;
}

/* 标题 */
.movie-title {
    font-size: 20px;
    margin-bottom: 4px;
    font-weight: 500;
}

/* 标签 */
.tags {
    margin: 8px 0;
}

/* 简介 */
.movie-desc {
    color: rgba(0, 0, 0, 0.65);
    line-height: 1.6;
    overflow: hidden;
    text-overflow: ellipsis;

    /* 标准属性 (现代浏览器) */
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 3;

    /* 兼容性写法 */
    display: -moz-box;
    -moz-box-orient: vertical;
    -moz-line-clamp: 3;

    /* 最新的标准属性 */
    display: box;
    box-orient: vertical;
    line-clamp: 3;
}

/* 响应式调整 */
@media (max-width: 768px) {
    .movie-container {
        flex-direction: column;
        gap: 12px;
    }

    .movie-poster {
        flex: 0 0 auto;
        width: 100%;
    }

    .movie-cover {
        height: auto;
        max-height: 300px;
    }

    .movie-basic-info {
        flex-wrap: wrap;
        gap: 8px 16px;
    }

    .movie-title {
        font-size: 18px;
    }
}


.recommend-alert {
    margin-bottom: 24px;
}

.recommend-card {
    margin-bottom: 24px;
}
</style>