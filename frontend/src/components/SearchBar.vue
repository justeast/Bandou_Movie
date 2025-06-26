<template>
    <div class="search-bar-container">
        <div class="search-input-wrapper">
            <a-input-search v-model:value="searchKeyword" placeholder="搜索电影、导演、演员等" enter-button="搜索" :loading="loading"
                :maxlength="50" @search="handleSearch" @change="handleInputChange" />
            <button v-if="searchKeyword" class="clear-button" @click="clearSearch" @mousedown.stop>×</button>
        </div>
        <ul v-if="showHistory" class="search-history">
            <li v-for="(item, index) in searchHistory" :key="index" @click="selectHistory(item)">{{ item }}</li>
            <li class="clear-history" @click="clearHistory">清空历史记录</li>
        </ul>
    </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from '../utils/axios';
import { message } from 'ant-design-vue';
import { debounce } from 'lodash';

// 定义 props
const props = defineProps({
    getMoviesByCategory: {
        type: Function,
        required: true
    },
    category: {
        type: String,
        default: 'all'
    }
});

// 定义 emit来更新电影
const emit = defineEmits(['update:movies']);

// 搜索关键词
const searchKeyword = ref('');
// 搜索加载状态
const loading = ref(false);
// 搜索历史
const searchHistory = ref(JSON.parse(localStorage.getItem('searchHistory') || '[]'));
// 是否显示历史记录
const showHistory = ref(false);

// 防抖搜索函数
const debouncedSearch = debounce(async (keyword) => {
    try {
        loading.value = true;
        const response = await axios.get(`/movies/search/?keyword=${encodeURIComponent(keyword)}`);
        emit('update:movies', response.data);
        if (response.data.length === 0) {
            message.info('未找到匹配的电影', 3);
        }
    } catch (error) {
        console.error('搜索电影失败：', error);
        message.error('搜索失败，请重试', 3);
        emit('update:movies', []);
    } finally {
        loading.value = false;
    }
}, 300);

// 处理搜索
const handleSearch = (value) => {
    const keyword = value.trim();
    if (!keyword) {
        // 清空搜索时恢复分类电影
        props.getMoviesByCategory(props.category);
        showHistory.value = false;
        return;
    }
    // 添加到搜索历史
    if (!searchHistory.value.includes(keyword)) {
        searchHistory.value.unshift(keyword);
        if (searchHistory.value.length > 10) searchHistory.value.pop();
        localStorage.setItem('searchHistory', JSON.stringify(searchHistory.value));
    }
    showHistory.value = false;
    debouncedSearch(keyword);
};

// 处理输入变化
const handleInputChange = (e) => {
    const keyword = e.target.value.trim();
    if (!keyword) {
        props.getMoviesByCategory(props.category);
        showHistory.value = false;
    } else {
        showHistory.value = true;
    }
};

// 选择历史记录
const selectHistory = (item) => {
    searchKeyword.value = item;
    handleSearch(item);
};

// 清空历史记录
const clearHistory = () => {
    searchHistory.value = [];
    localStorage.removeItem('searchHistory');
    showHistory.value = false;
};

// 清空搜索内容
const clearSearch = (event) => {
    event.stopPropagation();
    searchKeyword.value = '';
    props.getMoviesByCategory(props.category);
    showHistory.value = false;
};
</script>

<style scoped>
.search-bar-container {
    margin-bottom: 24px;
    margin-left: 260px;
    max-width: 600px;
    position: relative;
}

.search-input-wrapper {
    position: relative;
}

.clear-button {
    position: absolute;
    right: 80px;
    top: 0;
    height: 100%;
    border: none;
    background: transparent;
    font-size: 20px;
    color: #aaa;
    cursor: pointer;
    outline: none;
    padding: 0 10px;
    z-index: 10;
}

.search-history {
    list-style: none;
    margin: 0;
    padding: 10px 15px;
    background-color: #fff;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
    border-radius: 4px;
    position: absolute;
    top: 45px;
    width: 100%;
    z-index: 999;
}

.search-history li {
    padding: 5px 0;
    cursor: pointer;
}

.search-history li:hover {
    background-color: #f5f5f5;
}

.clear-history {
    color: #f5222d;
    font-weight: bold;
    cursor: pointer;
    text-align: center;
    margin-top: 10px;
    border-top: 1px solid #f0f0f0;
    padding-top: 5px;
}

.clear-history:hover {
    background-color: #ffe7e7;
}
</style>
