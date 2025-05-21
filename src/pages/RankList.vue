<template>
    <div class="rank-list">
        <a-page-header title="电影榜单" sub-title="根据用户评分排序" @back="() => router.go(-1)">
            <template #extra>
                <a-button type="link" @click="handleRefresh" :loading="loading">
                    <reload-outlined /> 刷新
                </a-button>
            </template>
        </a-page-header>

        <!-- 卡片式布局 -->
        <div class="movie-cards">
            <a-card v-for="(movie, index) in movies" :key="movie.id" class="movie-card" @click="goToDetail(movie.id)">
                <div class="card-content">
                    <!-- 排名徽章 -->
                    <div class="rank-badge" :class="getRankClass(index + 1)">
                        {{ index + 1 }}
                    </div>

                    <!-- 电影封面 -->
                    <div class="cover-container">
                        <img :src="getProxyImageUrl(movie.cover_url)" :alt="movie.title" @error="handleImageError">
                    </div>

                    <!-- 电影信息 -->
                    <div class="movie-info">
                        <h3 class="title">{{ movie.title }}</h3>
                        <div class="meta">
                            <span class="director">{{ movie.director }}</span>
                            <a-rate v-model:value="movie.score" allow-half disabled class="rating" />
                            <span class="score">{{ movie.score || '暂无评分' }}</span>
                        </div>
                        <p class="starring">{{ formatStarring(movie.starring) }}</p>
                    </div>
                </div>
            </a-card>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ReloadOutlined } from '@ant-design/icons-vue';
import axios from '../utils/axios';
import defaultCover from '../assets/default-movie-cover.jpg';

const router = useRouter();
const movies = ref([]);
const loading = ref(false);

const formatStarring = (starring) => {
    const actors = starring.split(" / ");
    return actors.slice(0, 3).join(" / ") + (actors.length > 3 ? "..." : "");
};

// 根据排名返回对应的 CSS 类名
const getRankClass = (rank) => {
    return {
        'rank-1': rank === 1,
        'rank-2': rank === 2,
        'rank-3': rank === 3,
        'rank-normal': rank > 3
    };
};

// 缓存配置
const CACHE_KEY = 'movies-ranking';
const CACHE_TTL = 5 * 60 * 1000; // 5分钟缓存

// 获取代理图片URL（添加本地缓存）
const getProxyImageUrl = (originalUrl) => {
    if (!originalUrl) return defaultCover;

    // 检查是否是本地图片路径（以/media/开头）
    if (originalUrl.startsWith('/media/')) {
        // 本地图片直接返回完整URL
        return `http://127.0.0.1:8000${originalUrl}`;
    }

    // 外部图片使用代理和缓存
    const cacheKey = `image:${originalUrl}`;
    const cached = sessionStorage.getItem(cacheKey);
    if (cached) return cached;

    const proxyUrl = `http://127.0.0.1:8000/proxy_image/?url=${encodeURIComponent(originalUrl)}`;
    sessionStorage.setItem(cacheKey, proxyUrl);
    return proxyUrl;
};

// 图片加载失败处理
const handleImageError = (event) => {
    event.target.src = defaultCover;
};



// 带缓存的获取榜单数据
const fetchRankingMovies = async () => {
    try {
        loading.value = true;

        // 先尝试读取缓存
        const cachedData = getValidCache();
        if (cachedData) {
            movies.value = cachedData;
            loading.value = false;

            // 后台静默更新
            setTimeout(fetchAndUpdate, 0);
            return;
        }

        // 无缓存时直接请求
        await fetchAndUpdate();
    } catch (error) {
        console.error('获取榜单失败:', error);
    } finally {
        loading.value = false;
    }
};

// 实际获取并更新缓存
const fetchAndUpdate = async () => {
    try {
        const response = await axios.get('/movies/ranking/');
        const newData = response.data.map((movie, index) => ({
            ...movie,
            rank: index + 1,
        }));

        // 更新数据并缓存
        movies.value = newData;
        setCache(newData);
    } catch (error) {
        console.error('后台更新失败:', error);
    }
};

// 缓存管理方法
const getValidCache = () => {
    try {
        const cached = localStorage.getItem(CACHE_KEY);
        if (!cached) return null;

        const { data, timestamp } = JSON.parse(cached);
        if (Date.now() - timestamp < CACHE_TTL) {
            return data;
        }
    } catch (e) {
        console.warn('缓存读取失败', e);
    }
    return null;
};

const setCache = (data) => {
    try {
        const cacheData = {
            data,
            timestamp: Date.now()
        };
        localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData));
    } catch (e) {
        console.warn('缓存写入失败', e);
    }
};

// 添加手动刷新方法（绑定到按钮）
const handleRefresh = async () => {
    localStorage.removeItem(CACHE_KEY);
    loading.value = true;
    await fetchAndUpdate();
    loading.value = false;
};

const goToDetail = (movieId) => {
    // 使用命名路由确保路径一致性
    router.push({
        name: 'MovieDetail',
        params: { id: movieId },
        query: { from: 'ranking' } // 携带来源信息
    })
}

onMounted(() => {
    fetchRankingMovies();
});
</script>

<style scoped>
/* 容器样式 */
.rank-list-container {
    padding: 20px;
    background: #fff;
}

.movie-cards {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin-top: 20px;
}

/* 卡片样式 */
.movie-card {
    cursor: pointer;
    transition: all 0.3s ease;
    border-radius: 8px;
    overflow: hidden;
    padding: 12px;
}

.movie-card:hover {
    transform: scale(1.03) translateY(-3px);
    box-shadow: 0 8px 20px rgba(46, 4, 200, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.5);

}

.card-content {
    display: flex;
    gap: 18px;
    height: 150px;
}

/* 排名徽章基础样式 */
.rank-badge {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    color: white;
    font-weight: bold;
    flex-shrink: 0;
    align-self: center;
    font-size: 14px;
}

.rank-1 {
    background: #FFEB00;
    /* 金色 */
}

.rank-2 {
    background: #D5DAEB
        /* 银色 */
}

.rank-3 {
    background: #FF9149;
    /* 铜色 */
}

.rank-normal {
    background: #f0f0f0;
    color: #666;
    border: 1px solid #ddd;
}

/* 封面样式 */
.cover-container {
    width: 110px;
    height: 150px;
    flex-shrink: 0;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.cover-container img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 4px;
}

/* 信息区域 */
.movie-info {
    flex: 1;
    overflow: hidden;
    padding-right: 20px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.title {
    font-size: 16px;
    font-weight: 600;
    margin: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.meta {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--ant-text-color-secondary);
}

.director {
    font-size: 12px;
}

.rating {
    font-size: 16px;
}

.score {
    font-weight: bold;
    color: var(--ant-primary-6);
}

.starring {
    font-size: 12px;
    color: var(--ant-text-color-secondary);
    margin: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* 响应式调整 */
@media (max-width: 768px) {
    .card-content {
        height: auto;
        flex-direction: wrap;
    }

    .cover-container {
        width: 100%;
        height: 200px;
    }

    .movie-info {
        padding: 12px 0;
        width: 100%;
    }
}
</style>