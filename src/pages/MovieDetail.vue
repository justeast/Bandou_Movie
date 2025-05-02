<template>
    <a-layout>
        <a-layout-content :style="{ padding: '24px', maxWidth: '800px', margin: '0 auto' }">
            <a-card v-if="movie" :style="{
                background: 'linear-gradient(145deg, #98D8EF, #f3f3f3)',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
                borderRadius: '12px',
                overflow: 'hidden',
                padding: '24px',
            }">
                <a-row :gutter="16" type="flex" align="stretch" style="position: relative; margin-bottom: 0">
                    <!-- 电影封面 -->
                    <a-col :span="10" style="
                            display: flex;
                            align-items: stretch;
                            padding-right: 16px;
                            height: 100%;
                        ">
                        <div style="
                            flex: 1;
                            min-height: 300px;
                            display: flex;  
                            border-radius: 8px;
                            box-shadow: 0 4px 10px rgba(9, 18, 44, 0.3);
                            overflow: hidden;
                            transition: transform 0.3s ease;
                            cursor: pointer;
                            " @mouseover="hoverEffect(true)" @mouseleave="hoverEffect(false)">
                            <a-image :src="cachedImage(movie.cover_url)" alt="电影封面" @error="handleImageError"
                                :preview="false" :style="{
                                    width: '100%',
                                    height: '100%',
                                    'object-fit': 'cover'
                                }" />

                        </div>

                    </a-col>

                    <!-- 右侧电影详细信息 -->
                    <a-col :span="14" style=" 
                            display: flex;
                            flex-direction: column;
                            padding-left: 16px;
                            border-left: 2px solid #f0f0f0">

                        <a-descriptions :column="1" :bordered="false" style="flex: 1; margin-bottom: 0">
                            <!-- 自定义标题 -->
                            <template #title>
                                <span style="font-size: 22px; font-weight: bold">🎬电影详情</span>
                            </template>
                            <a-descriptions-item label="导演" :labelStyle="{ fontSize: '18px' }"
                                :contentStyle="{ fontSize: '18px' }">{{
                                    movie.director
                                }}</a-descriptions-item>
                            <a-descriptions-item label="主演" :labelStyle="{ fontSize: '18px' }"
                                :contentStyle="{ fontSize: '18px' }">
                                <div style="
                                        max-height: 150px;  
                                        overflow-y: auto;">
                                    {{ movie.starring }}
                                </div>
                            </a-descriptions-item>
                            <a-descriptions-item label="类型" :labelStyle="{ fontSize: '18px' }"
                                :contentStyle="{ fontSize: '18px' }">{{ movie.type
                                }}</a-descriptions-item>
                            <a-descriptions-item label="评分" :labelStyle="{ fontSize: '18px' }"
                                :contentStyle="{ fontSize: '18px' }">
                                <div style="display: flex; align-items: center; gap: 8px">
                                    <a-rate :value="avgRating" allow-half disabled style="color: #EC5228;" />
                                    <span style="font-weight: bold; color: #fa541c">{{ avgRating !== null ? avgRating :
                                        '暂无' }}</span>
                                    <span style="font-size: 14px; color: #8c8c8c;">({{ ratingCount }}人评分)</span>
                                </div>
                            </a-descriptions-item>
                            <a-descriptions-item label="上映时间" :labelStyle="{ fontSize: '18px' }"
                                :contentStyle="{ fontSize: '18px' }">{{
                                    movie.release_time
                                }}</a-descriptions-item>
                        </a-descriptions>

                    </a-col>
                </a-row>

                <!-- 电影简介 -->
                <div style="margin-top: 16px; padding-top: 16px; border-top: 2px solid #e8e8e8">
                    <h3 style="font-size: 22px; font-weight: bold;">📖简介:</h3>
                    <p style="font-size: 18px; line-height: 1.8; color: #595959;">{{ movie.brief_introduction }}</p>
                </div>

                <!--用户评分-->
                <rating-component :movieId="movieId" @update:rating-stats="updateRatingStats"></rating-component>

                <!--用户评论-->
                <comment-component :movieId="movieId"></comment-component>


                <!-- 返回按钮 -->
                <a-button type="primary" @click="goBack"
                    style="margin-top: 16px; background-color: #52c41a; border: none;" @mouseover="hoverBack = true"
                    @mouseleave="hoverBack = false">
                    {{ hoverBack ? '👈 返回' : '返回' }}
                </a-button>
            </a-card>

            <a-skeleton v-else active /> <!-- 加载状态 -->
        </a-layout-content>
    </a-layout>
</template>

<script setup>
import { useRoute, useRouter } from "vue-router";
import { onMounted, ref, computed } from "vue";
import axios from "../utils/axios";
import RatingComponent from "../components/RatingComponent.vue";
import CommentComponent from "../components/CommentComponent.vue";
import defaultCover from '../assets/default-movie-cover.jpg';


const route = useRoute();
const router = useRouter();
const movie = ref(null);
const hoverBack = ref(false);

const avgRating = ref(null);
const ratingCount = ref(0);

// 更新评分统计
const updateRatingStats = ({ avgRating: avg, ratingCount: count }) => {
    avgRating.value = avg;
    ratingCount.value = count;
};

const emit = defineEmits(["updateCategory"])

// 获取电影详情
const fetchMovieDetail = async () => {
    const movieId = route.params.id;
    try {
        const response = await axios.get(`/bandou/movies/${movieId}/`);
        movie.value = response.data;
        updateSelectedCategory(route.query.category || "all");
    } catch (error) {
        console.error("获取电影详情失败", error);
    }
};

// 本地缓存
const imageCache = ref(JSON.parse(localStorage.getItem("imageCache")) || {});

// 处理图片 URL
const cachedImage = (url) => {
    if (!imageCache.value[url]) {
        const proxyUrl = `http://127.0.0.1:8000/proxy_image/?url=${encodeURIComponent(url)}`;
        imageCache.value[url] = proxyUrl;
        localStorage.setItem("imageCache", JSON.stringify(imageCache.value));
    }
    return imageCache.value[url];
};

// 图片加载失败处理
const handleImageError = (event) => {
    event.target.src = defaultCover;
};

// 鼠标悬停封面时的缩放效果
const hoverEffect = (isHovering) => {
    const coverDiv = document.querySelector('.ant-image');
    if (coverDiv) {
        coverDiv.style.transform = isHovering ? 'scale(1.08)' : 'scale(1)';
    }
};

const goBack = () => {
    router.back();
};

// 更新选中的分类
const updateSelectedCategory = (category) => {
    emit("updateCategory", category);
};

// 获取电影ID
const movieId = computed(() => parseInt(route.params.id));

onMounted(fetchMovieDetail);
</script>

<style scoped></style>
