<template>
    <a-card :bordered="false" class="movie-card" @click="goToDetail">
        <!-- 封面 -->
        <div class="cover-container">
            <img :src="cachedImage(movie.cover_url)" alt="封面" class="cover-image">
        </div>

        <!-- 电影信息 -->
        <div class="movie-info">
            <h3 class="movie-title">{{ movie.title }}</h3>
            <p class="movie-director"><strong>导演：</strong>{{ movie.director }}</p>
            <p class="movie-starring"><strong>主演：</strong>{{ formatStarring(movie.starring) }}</p>
            <p class="movie-type"><strong>类别：</strong>{{ movie.type }}</p>
            <p class="movie-score"><strong>评分：</strong>{{ movie.score || "暂无评分" }}</p>
            <p class="movie-release"><strong>上映时间：</strong>{{ movie.release_time }}</p>
            <p class="movie-desc ellipsis-text"><strong>简介：</strong>{{ movie.brief_introduction }}</p>
        </div>
    </a-card>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';

const props = defineProps({
    movie: Object
})

const movieId = props.movie.id

// 处理主演人数
const formatStarring = (starring) => {
    const actors = starring.split(" / "); // 将字符串转换为数组
    return actors.length > 10 ? actors.slice(0, 10).join(" / ") + " / ..." : starring;
};

// 本地缓存
const imageCache = ref(JSON.parse(localStorage.getItem("imageCache")) || {});

// 处理图片 URL
const cachedImage = (url) => {
    if (!url) return '';

    // 检查是否是本地图片路径（以/media/开头）
    if (url.startsWith('/media/')) {
        // 本地图片直接返回完整URL
        return `http://127.0.0.1:8000${url}`;
    }

    // 外部图片使用代理
    if (!imageCache.value[url]) {
        const proxyUrl = `http://127.0.0.1:8000/proxy_image/?url=${encodeURIComponent(url)}`;
        imageCache.value[url] = proxyUrl;
        localStorage.setItem("imageCache", JSON.stringify(imageCache.value));
    }
    return imageCache.value[url];
};

const route = useRoute()
const router = useRouter()

const goToDetail = () => {
    router.push({
        name: 'MovieDetail',
        params: { id: movieId },
        query: {
            from: 'home', // 明确来源是首页
            category: route.query.category || "all" // 分类参数
        }
    });
}
</script>

<style scoped>
/* 默认卡片样式 */
.movie-card {
    display: flex;
    flex-direction: column;
    height: 100%;
    padding: 10px;
    text-align: left;
    border-radius: 10px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    background: #fff;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    /* 默认轻微阴影 */

}

/* ⭐ 悬浮时的高亮效果 */
.movie-card:hover {
    transform: scale(1.03) translateY(-3px);
    /* 轻微放大 + 上移 */
    box-shadow: 0 8px 20px rgba(46, 4, 200, 0.7);
    /* 阴影更明显 */
    border: 1px solid rgba(255, 255, 255, 0.5);
    /* 增加白色边框，增强立体感 */
}

/* 封面图片区域 */
.cover-container {
    width: 100%;
    height: 280px;
    overflow: hidden;
    border-radius: 8px;
}

.cover-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 8px;
}

/* 电影信息区域 */
.movie-info {
    padding-top: 10px;
}

.movie-title {
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 8px;
}

.movie-director,
.movie-starring,
.movie-type,
.movie-score,
.movie-release {
    font-size: 14px;
    margin: 4px 0;
    color: #555;
}

/* 让简介超出部分显示省略号 */
.ellipsis-text {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    /* 限制最多显示 2 行 */
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    word-break: break-word;

    /* 兼容性优化 */
    display: box;
    line-clamp: 2;
    box-orient: vertical;
}
</style>