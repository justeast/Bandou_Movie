<template>
    <div class="admin-movie-manage">
        <a-card title="电影管理" :bordered="false">
            <!-- 未登录提示 -->
            <a-alert v-if="!userStore.isLoggedIn" type="warning" message="请先登录" description="您需要登录才能访问电影管理功能。"
                show-icon />
            <!-- 非管理员提示 -->
            <a-alert v-else-if="!userStore.isAdmin" type="error" message="权限不足" description="只有管理员才能访问电影管理功能。"
                show-icon />
            <!-- 管理员内容 -->
            <div v-else>
                <!-- 电影列表 -->
                <a-table :columns="columns" :data-source="movies" :row-selection="rowSelection" :pagination="pagination"
                    :loading="loading" rowKey="id" @change="handleTableChange">
                    <template #bodyCell="{ column, record }">
                        <template v-if="column.key === 'action'">
                            <a-button type="link" @click="editMovie(record)">编辑</a-button>
                            <a-popconfirm title="确定删除这部电影？" @confirm="deleteMovie(record.id)">
                                <a-button type="link" danger>删除</a-button>
                            </a-popconfirm>
                        </template>
                    </template>
                </a-table>

                <!-- 批量删除按钮 -->
                <a-button type="primary" danger :disabled="!selectedRowKeys.length" style="margin: 16px 0"
                    @click="bulkDelete">
                    批量删除
                </a-button>

                <!-- 分类统计 -->
                <a-card title="分类统计" style="margin-top: 24px">
                    <a-table :columns="categoryColumns" :data-source="categoryStats" :pagination="false" />
                </a-card>

                <!-- 评分分布 -->
                <a-card title="评分分布" style="margin-top: 24px">
                    <a-table :columns="distributionColumns" :data-source="ratingDistribution" :pagination="false" />
                </a-card>
            </div>
        </a-card>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useUserStore } from '../stores/user';
import axios from '../utils/axios';
import { message } from 'ant-design-vue';


const userStore = useUserStore();


const movies = ref([]);
const loading = ref(false);
const selectedRowKeys = ref([]);
const pagination = ref({
    current: 1,
    pageSize: 10,
    total: 0,
});

// 电影列表列配置
const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: '标题', dataIndex: 'title', key: 'title' },
    { title: '导演', dataIndex: 'director', key: 'director' },
    { title: '类型', dataIndex: 'type', key: 'type' },
    { title: '主演', dataIndex: 'starring', key: 'starring' },
    { title: '评分', dataIndex: 'score', key: 'score' },
    { title: '操作', key: 'action' },
];

// 分类统计列配置
const categoryColumns = [
    { title: '分类', dataIndex: 'category', key: 'category' },
    { title: '电影数量', dataIndex: 'count', key: 'count' },
];

// 评分分布列配置
const distributionColumns = [
    { title: '分类', dataIndex: 'category', key: 'category' },
    { title: '0-1分', dataIndex: 'range_0_1', key: 'range_0_1' },
    { title: '1-2分', dataIndex: 'range_1_2', key: 'range_1_2' },
    { title: '2-3分', dataIndex: 'range_2_3', key: 'range_2_3' },
    { title: '3-4分', dataIndex: 'range_3_4', key: 'range_3_4' },
    { title: '4-5分', dataIndex: 'range_4_5', key: 'range_4_5' },
];

// 分类统计数据
const categoryStats = ref([]);
// 评分分布数据
const ratingDistribution = ref([]);

// 行选择配置
const rowSelection = computed(() => ({
    selectedRowKeys: selectedRowKeys.value,
    onChange: (keys) => {
        selectedRowKeys.value = keys;
    },
}));

// 获取电影列表
const fetchMovies = async () => {
    loading.value = true;
    try {
        const response = await axios.get('/bandou/admin/movies/', {
            params: {
                page: pagination.value.current,
                page_size: pagination.value.pageSize,
            },
        });
        movies.value = response.data.results;
        pagination.value.total = response.data.count;
    } catch (error) {
        message.error('获取电影列表失败');
        console.error(error);
    } finally {
        loading.value = false;
    }
};

// 获取分类统计
const fetchCategoryStats = async () => {
    try {
        const response = await axios.get('/bandou/admin/movies/category_stats/');
        categoryStats.value = response.data;
    } catch (error) {
        message.error('获取分类统计失败');
        console.error(error);
    }
};

// 获取评分分布
const fetchRatingDistribution = async () => {
    try {
        const response = await axios.get('/bandou/admin/movies/rating_distribution/');
        ratingDistribution.value = response.data.map(item => ({
            category: item.category,
            range_0_1: item.distribution.find(d => d.range === '0-1')?.count || 0,
            range_1_2: item.distribution.find(d => d.range === '1-2')?.count || 0,
            range_2_3: item.distribution.find(d => d.range === '2-3')?.count || 0,
            range_3_4: item.distribution.find(d => d.range === '3-4')?.count || 0,
            range_4_5: item.distribution.find(d => d.range === '4-5')?.count || 0,
        }));
    } catch (error) {
        message.error('获取评分分布失败');
        console.error(error);
    }
};

// 删除单部电影
const deleteMovie = async (id) => {
    try {
        await axios.delete(`/bandou/admin/movies/${id}/`);
        message.success('删除成功');
        fetchMovies();
    } catch (error) {
        message.error('删除失败');
        console.error(error);
    }
};

// 批量删除
const bulkDelete = async () => {
    try {
        await axios.post('/bandou/admin/movies/bulk_delete/', {
            ids: selectedRowKeys.value,
        });
        message.success('批量删除成功');
        selectedRowKeys.value = [];
        fetchMovies();
    } catch (error) {
        message.error('批量删除失败');
        console.error(error);
    }
};

// 编辑电影（跳转到Django Admin）
const editMovie = (record) => {
    window.location.href = `http://localhost:8000/admin/movies/movie/${record.id}/change/`;
};

// 表格分页、排序、筛选变化
const handleTableChange = (pag) => {
    pagination.value.current = pag.current;
    pagination.value.pageSize = pag.pageSize;
    fetchMovies();
};

// 初始化加载数据
onMounted(() => {
    if (userStore.isAdmin) {
        fetchMovies();
        fetchCategoryStats();
        fetchRatingDistribution();
    }
});
</script>

<style scoped>
.admin-movie-manage {
    padding: 24px;
}
</style>