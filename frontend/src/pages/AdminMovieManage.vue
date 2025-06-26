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
                <!-- 图表区域 -->
                <a-row :gutter="[16, 16]" style="margin-bottom: 24px">
                    <a-col :span="12">
                        <a-card title="分类电影数量统计">
                            <div ref="categoryChart" style="height: 300px"></div>
                        </a-card>
                    </a-col>
                    <a-col :span="12">
                        <a-card title="分类电影分数段占比">
                            <a-select v-model:value="selectedCategory" style="width: 200px; margin-bottom: 16px"
                                :options="categoryOptions" placeholder="选择分类" @change="updatePieChart" />
                            <div ref="ratingPieChart" style="height: 300px"></div>
                        </a-card>
                    </a-col>
                </a-row>

                <!-- 操作按钮区域 -->
                <div class="button-group" style="margin-bottom: 16px; display: flex; justify-content: space-between;">
                    <div>
                        <a-button type="primary" danger :disabled="!selectedRowKeys.length" @click="bulkDelete">
                            批量删除
                        </a-button>
                    </div>
                    <div class="search-container" style="flex-grow: 1; margin: 0 16px;">
                        <a-input-search v-model:value="searchQuery" placeholder="搜索电影名称、导演、类型或主演" enter-button
                            @search="handleSearch" style="width: 100%;" allow-clear />
                    </div>
                    <div>
                        <a-button type="primary" @click="openAddModal">
                            添加电影
                        </a-button>
                    </div>
                </div>

                <!-- 过滤器区域 -->
                <div class="filter-container" style="margin-bottom: 16px; display: flex; gap: 16px; flex-wrap: wrap;">
                    <!-- 评分过滤 -->
                    <div class="filter-item">
                        <span class="filter-label">评分过滤：</span>
                        <a-select v-model:value="ratingFilter" style="width: 150px" @change="handleFilterChange">
                            <a-select-option value="">全部评分</a-select-option>
                            <a-select-option value="gte_4">4分以上</a-select-option>
                            <a-select-option value="gte_3">3分以上</a-select-option>
                            <a-select-option value="lt_3">3分以下</a-select-option>
                            <a-select-option value="no_rating">暂无评分</a-select-option>
                        </a-select>
                    </div>
                    <!-- 上映日期过滤 -->
                    <div class="filter-item">
                        <span class="filter-label">上映日期：</span>
                        <a-select v-model:value="releaseDateFilter" style="width: 180px" @change="handleFilterChange">
                            <a-select-option value="">全部日期</a-select-option>
                            <a-select-option value="upcoming">即将上映(3天内)</a-select-option>
                            <a-select-option value="recent">最近上映(30天内)</a-select-option>
                            <a-select-option value="this_year">今年上映</a-select-option>
                            <a-select-option value="last_year">去年上映</a-select-option>
                        </a-select>
                    </div>
                    <!-- 自定义日期范围 -->
                    <div class="filter-item" v-if="releaseDateFilter === 'custom'">
                        <a-range-picker v-model:value="customDateRange" format="YYYY-MM-DD" @change="handleFilterChange"
                            style="width: 280px" />
                    </div>
                    <!-- 重置过滤器 -->
                    <div class="filter-item">
                        <a-button type="default" @click="resetFilters">重置过滤器</a-button>
                    </div>
                </div>

                <!-- 电影列表 -->
                <a-table :columns="columns" :data-source="movies" :row-selection="rowSelection" :pagination="pagination"
                    :loading="loading" rowKey="id" @change="handleTableChange">
                    <template #bodyCell="{ column, record }">
                        <template v-if="column.key === 'trend'">
                            <div :ref="(el) => setTrendChartRef(record.id, el)"
                                style="height: 200px; width: 300px; min-width: 300px" class="trend-chart"></div>
                        </template>
                        <template v-if="column.key === 'score'">
                            <span v-if="record.score !== null && record.score !== undefined">{{ record.score }}</span>
                            <span v-else class="no-score">暂无评分</span>
                        </template>
                        <template v-if="column.key === 'action'">
                            <a-button type="link" @click="editMovie(record)">编辑</a-button>
                            <a-popconfirm title="确定删除这部电影？" @confirm="deleteMovie(record.id)" cancelText="取消"
                                okText="确定">
                                <a-button type="link" danger>删除</a-button>
                            </a-popconfirm>
                        </template>
                    </template>
                </a-table>
            </div>

            <!-- 电影编辑表单 -->
            <movie-edit-form v-model:visible="editModalVisible" :movie-id="currentEditId"
                @success="handleEditSuccess" />
        </a-card>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue';
import { useUserStore } from '../stores/user';
import axios from '../utils/axios';
import { message } from 'ant-design-vue';
import * as echarts from 'echarts';
import MovieEditForm from '../components/MovieEditForm.vue';
import dayjs from 'dayjs';

// 用户状态
const userStore = useUserStore();

// 编辑相关
const editModalVisible = ref(false);
const currentEditId = ref(null);

// 搜索相关
const searchQuery = ref('');

// 过滤相关
const ratingFilter = ref('');
const releaseDateFilter = ref('');
const customDateRange = ref([]);

// 电影列表数据
const movies = ref([]);
const loading = ref(false);
const selectedRowKeys = ref([]);
const pagination = ref({
    current: 1,
    pageSize: 10,
    total: 0,
    showSizeChanger: true,
    pageSizeOptions: ['10', '20', '50', '100'],
    showQuickJumper: true,
    showTotal: (total) => `共 ${total} 条`,
    locale: {
        items_per_page: '/ 页',
    },
});

// 图表相关数据
const categoryStats = ref([]);
const ratingDistribution = ref([]);
const selectedCategory = ref(null);
const categoryOptions = ref([]);

// 图表引用
const categoryChart = ref(null);
const ratingPieChart = ref(null);
const trendChartRefs = ref({});
let categoryChartInstance = null;
let ratingPieChartInstance = null;

// 电影列表列配置
const columns = [
    { title: '电影名称', dataIndex: 'title', key: 'title', width: 150 },
    { title: '评分', dataIndex: 'score', key: 'score', width: 120 },
    { title: '上映日期', dataIndex: 'release_time', key: 'release_time', width: 180 },
    { title: '近一周评分趋势', key: 'trend', width: 320 },
    { title: '操作', key: 'action', width: 100 },
];

// 行选择配置
const rowSelection = computed(() => ({
    selectedRowKeys: selectedRowKeys.value,
    preserveSelectedRowKeys: true,
    onChange: (keys) => {
        selectedRowKeys.value = keys;
    },
}));

// 设置趋势图 DOM 引用
const setTrendChartRef = (movieId, el) => {
    if (el) {
        trendChartRefs.value[movieId] = el;
    } else {
        delete trendChartRefs.value[movieId];
    }
};

// 获取电影列表
const fetchMovies = async () => {
    loading.value = true;
    try {
        // 构建请求参数
        const params = {
            page: pagination.value.current,
            page_size: pagination.value.pageSize,
            search: searchQuery.value,
        };

        // 添加评分过滤
        if (ratingFilter.value) {
            switch (ratingFilter.value) {
                case 'gte_4':
                    params.min_score = 4;
                    break;
                case 'gte_3':
                    params.min_score = 3;
                    break;
                case 'lt_3':
                    params.max_score = 3;
                    break;
                case 'no_rating':
                    params.no_rating = true;
                    break;
            }
        }

        // 添加上映日期过滤
        if (releaseDateFilter.value) {
            const today = dayjs();

            switch (releaseDateFilter.value) {
                case 'upcoming':
                    // 今天和未来3天
                    params.release_date_start = today.format('YYYY-MM-DD');
                    params.release_date_end = today.add(3, 'day').format('YYYY-MM-DD');
                    break;
                case 'recent':
                    // 最近30天
                    params.release_date_start = today.subtract(30, 'day').format('YYYY-MM-DD');
                    params.release_date_end = today.format('YYYY-MM-DD');
                    params.filter_type = 'recent_release'; // 添加过滤类型标识
                    break;
                case 'this_year':
                    // 今年
                    params.release_date_start = today.startOf('year').format('YYYY-MM-DD');
                    params.release_date_end = today.endOf('year').format('YYYY-MM-DD');
                    break;
                case 'last_year':
                    // 去年
                    params.release_date_start = today.subtract(1, 'year').startOf('year').format('YYYY-MM-DD');
                    params.release_date_end = today.subtract(1, 'year').endOf('year').format('YYYY-MM-DD');
                    break;
                case 'custom':
                    // 自定义日期范围
                    if (customDateRange.value && customDateRange.value.length === 2) {
                        params.release_date_start = dayjs(customDateRange.value[0]).format('YYYY-MM-DD');
                        params.release_date_end = dayjs(customDateRange.value[1]).format('YYYY-MM-DD');
                    }
                    break;
            }
        }

        const response = await axios.get('/bandou/admin/movies/', { params });
        movies.value = response.data.results;
        pagination.value.total = response.data.count;
    } catch (error) {
        // 处理404错误
        if (error.response && error.response.status === 404) {
            // 如果当前页不存在且不是第一页，则跳转到前一页
            if (pagination.value.current > 1) {
                pagination.value.current -= 1;
                // 递归调用，重新获取数据
                return fetchMovies();
            }
        }
        message.error('获取电影列表失败');
        console.error(error);
    } finally {
        loading.value = false;
    }
};

// 处理搜索
const handleSearch = (value) => {
    searchQuery.value = value;
    pagination.value.current = 1; // 重置到第一页
    fetchMovies();
};

// 处理过滤器变化
const handleFilterChange = () => {
    pagination.value.current = 1; // 重置到第一页
    fetchMovies();
};

// 重置过滤器
const resetFilters = () => {
    ratingFilter.value = '';
    releaseDateFilter.value = '';
    customDateRange.value = [];
    pagination.value.current = 1;
    fetchMovies();
};

// 获取分类统计
const fetchCategoryStats = async () => {
    try {
        const response = await axios.get('/bandou/admin/movies/category_stats/');
        categoryStats.value = response.data;
        categoryOptions.value = response.data.map((item) => ({
            value: item.category,
            label: item.category,
        }));
        if (categoryStats.value.length > 0) {
            selectedCategory.value = categoryStats.value[0].category;
        }

        // 确保在调用initCategoryChart前，已有实例被销毁
        if (categoryChartInstance) {
            categoryChartInstance.dispose();
            categoryChartInstance = null;
        }

        initCategoryChart();
    } catch (error) {
        message.error('获取分类统计失败');
        console.error(error);
    }
};

// 获取评分分布
const fetchRatingDistribution = async () => {
    try {
        const response = await axios.get('/bandou/admin/movies/rating_distribution/');
        ratingDistribution.value = response.data;

        // 确保在调用updatePieChart前，已有实例被销毁
        if (ratingPieChartInstance) {
            ratingPieChartInstance.dispose();
            ratingPieChartInstance = null;
        }

        updatePieChart();
    } catch (error) {
        message.error('获取评分分布失败');
        console.error(error);
    }
};

// 获取单部电影评分趋势
const fetchRatingTrend = async (movieId) => {
    try {
        const response = await axios.get(`/bandou/admin/movies/${movieId}/rating_trend/`);
        const trendData = response.data;
        initTrendChart(movieId, trendData);
    } catch (error) {
        console.error(`获取电影 ${movieId} 评分趋势失败`, error);
        initTrendChart(movieId, []); // 显示空状态
    }
};

// 初始化分类电影数量柱状图
const initCategoryChart = () => {
    if (!categoryChart.value || !categoryStats.value.length) return;
    // 检查是否已存在图表实例，如果存在则销毁
    if (categoryChartInstance) {
        categoryChartInstance.dispose();
    }
    categoryChartInstance = echarts.init(categoryChart.value);

    // 按电影数量排序
    const sortedData = [...categoryStats.value].sort((a, b) => b.count - a.count);

    const option = {
        title: { text: '' },
        tooltip: {
            trigger: 'axis',
            formatter: '{b}: {c} 部电影'
        },
        grid: {
            top: '5%',
            left: '10%',
            right: '10%',
            bottom: '6%',
            containLabel: true
        },
        xAxis: {
            type: 'value',
            name: '电影数量',
            nameLocation: 'middle',
            nameGap: 25,
            axisLabel: {
                fontSize: 11
            }
        },
        yAxis: {
            type: 'category',
            data: sortedData.map(item => item.category),
            axisLabel: {
                formatter: function (value) {
                    return value.length > 8 ? value.substring(0, 7) + '...' : value;
                },
                tooltip: {
                    show: true
                },
                fontSize: 11,
                margin: 8
            }
        },
        series: [
            {
                name: '电影数量',
                type: 'bar',
                data: sortedData.map(item => item.count),
                barWidth: '60%',
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
                        { offset: 0, color: '#83bff6' },
                        { offset: 0.5, color: '#188df0' },
                        { offset: 1, color: '#188df0' }
                    ])
                },
                label: {
                    show: true,
                    position: 'right',
                    formatter: '{c}',
                    fontSize: 11
                }
            }
        ]
    };
    categoryChartInstance.setOption(option);
};

// 初始化评分分布饼状图
const updatePieChart = () => {
    if (!ratingPieChart.value || !selectedCategory.value) return;
    // 检查是否已存在图表实例，如果存在则销毁
    if (ratingPieChartInstance) {
        ratingPieChartInstance.dispose();
    }
    ratingPieChartInstance = echarts.init(ratingPieChart.value);
    const categoryData = ratingDistribution.value.find(
        (item) => item.category === selectedCategory.value
    );
    if (!categoryData) return;

    const pieData = categoryData.distribution
        .filter((item) => item.count > 0)
        .map((item) => ({
            name: item.range,
            value: item.count,
        }));

    if (!pieData.length) {
        ratingPieChartInstance.setOption({
            title: {
                text: '暂无数据',
                textStyle: { fontSize: 14, color: '#999' },
                left: 'center',
                top: 'middle',
            },
        });
        return;
    }

    const totalCount = pieData.reduce((sum, item) => sum + item.value, 0);

    const option = {
        title: { text: '' },
        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)',
        },
        legend: { orient: 'vertical', left: 'left' },
        series: [
            {
                name: '分数段占比',
                type: 'pie',
                radius: '40%',
                data: pieData,
                label: {
                    show: true,
                    position: 'outside',
                    formatter: (params) => {
                        const percent = totalCount > 0 ? ((params.value / totalCount) * 100).toFixed(2) : 0;
                        return `${params.name}: ${percent}%`;
                    },
                    fontSize: 12,
                    color: '#000',
                },
                labelLine: {
                    show: true,
                    length: 15,
                    length2: 10,
                    lineStyle: {
                        type: 'dashed',
                    },
                },
                emphasis: {
                    itemStyle: {
                        shadowBlur: 10,
                        shadowOffsetX: 0,
                        shadowColor: 'rgba(0, 0, 0, 0.5)',
                    },
                },
            },
        ],
    };
    ratingPieChartInstance.setOption(option);
};

// 初始化单部电影评分趋势折线图
const initTrendChart = (movieId, trendData) => {
    const chartDom = trendChartRefs.value[movieId];
    if (!chartDom) {
        console.warn(`Chart DOM not found for movie ${movieId}`);
        return;
    }

    // 检查是否已存在图表实例，如果存在则销毁
    if (chartDom.echartsInstance) {
        chartDom.echartsInstance.dispose();
        chartDom.echartsInstance = null;
    }

    const chart = echarts.init(chartDom);

    if (!trendData || trendData.length === 0) {
        chart.setOption({
            title: {
                text: '暂无评分数据',
                textStyle: { fontSize: 14, color: '#999' },
                left: 'center',
                top: 'middle',
            },
        });
    } else {
        const dates = trendData.map((item) => item.date);
        const ratings = trendData.map((item) => item.avg_rating);

        const option = {
            tooltip: { trigger: 'axis' },
            xAxis: {
                type: 'category',
                data: dates,
                axisLabel: {
                    rotate: 45,
                    fontSize: 12,
                    formatter: (value) => {
                        // 移除年份，仅显示月-日
                        return value.split('-').slice(1).join('-');
                    },
                },
                axisTick: { alignWithLabel: true },
            },
            yAxis: {
                type: 'value',
                min: 0,
                max: 5,
                axisLabel: { fontSize: 12 },
            },
            series: [
                {
                    name: '平均评分',
                    type: 'line',
                    data: ratings,
                    smooth: true,
                    lineStyle: { width: 2 },
                    symbol: 'circle',
                    symbolSize: 6,
                },
            ],
            grid: {
                left: '8%',
                right: '8%',
                top: '15%',
                bottom: '25%',
            },
        };
        chart.setOption(option);
    }

    // 保存实例引用
    chartDom.echartsInstance = chart;
};

// 添加电影
const openAddModal = () => {
    currentEditId.value = null; // 不传ID表示新建
    editModalVisible.value = true;
};

// 删除单部电影
const deleteMovie = async (id) => {
    try {
        // 检查当前页面是否只有一条记录
        const currentPageData = [...movies.value];
        const isLastItemOnPage = currentPageData.length === 1;
        const isNotFirstPage = pagination.value.current > 1;

        await axios.delete(`/bandou/admin/movies/${id}/`);
        message.success('删除成功');

        // 如果删除的是当前页面的最后一条记录且不是第一页，则跳转到前一页
        if (isLastItemOnPage && isNotFirstPage) {
            pagination.value.current -= 1;
        }

        fetchMovies();
    } catch (error) {
        message.error('删除失败');
        console.error(error);
    }
};

// 批量删除
const bulkDelete = async () => {
    try {
        // 检查是否删除了当前页的所有数据
        const currentPageData = [...movies.value];
        const allCurrentPageSelected = currentPageData.every(item =>
            selectedRowKeys.value.includes(item.id)
        );
        const isNotFirstPage = pagination.value.current > 1;

        await axios.post('/bandou/admin/movies/bulk_delete/', {
            ids: selectedRowKeys.value,
        });
        message.success('批量删除成功');
        selectedRowKeys.value = [];

        // 如果删除了当前页的所有数据且不是第一页，则跳转到前一页
        if (allCurrentPageSelected && isNotFirstPage) {
            pagination.value.current -= 1;
        }

        fetchMovies();
    } catch (error) {
        message.error('批量删除失败');
        console.error(error);
    }
};

// 编辑电影
const editMovie = (record) => {
    currentEditId.value = record.id;
    editModalVisible.value = true;
};

// 处理编辑成功
const handleEditSuccess = () => {
    fetchMovies(); // 重新加载电影列表
};

// 表格分页、排序、筛选变化
const handleTableChange = (pag) => {
    pagination.value.current = pag.current;
    pagination.value.pageSize = pag.pageSize;
    fetchMovies();
};

// 清理图表实例
const disposeCharts = () => {
    if (categoryChartInstance) {
        categoryChartInstance.dispose();
        categoryChartInstance = null;
    }
    if (ratingPieChartInstance) {
        ratingPieChartInstance.dispose();
        ratingPieChartInstance = null;
    }
    Object.keys(trendChartRefs.value).forEach((movieId) => {
        const chartDom = trendChartRefs.value[movieId];
        if (chartDom && chartDom.echartsInstance) {
            chartDom.echartsInstance.dispose();
            delete chartDom.echartsInstance;
        }
    });
};

// 监听电影数据变化，重新初始化趋势图
watch(
    () => movies.value,
    async () => {
        await nextTick();
        movies.value.forEach((movie) => {
            if (trendChartRefs.value[movie.id]) {
                fetchRatingTrend(movie.id);
            }
        });
    },
    { deep: true }
);

// 初始化加载数据
onMounted(() => {
    if (userStore.isAdmin) {
        fetchMovies();
        fetchCategoryStats();
        fetchRatingDistribution();
    }
});

// 组件销毁时清理
onUnmounted(() => {
    disposeCharts();
});
</script>

<style scoped>
.admin-movie-manage {
    padding: 32px;
    background: linear-gradient(135deg, #f5f7fa 0%, #e4e9f0 100%);
    min-height: 100vh;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* 卡片样式 */
:deep(.ant-card) {
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    background: #ffffff;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    display: flex;
    flex-direction: column;
}

:deep(.ant-card:hover) {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

:deep(.ant-card-head) {
    border-bottom: 1px solid #e8ecef;
    padding: 16px 24px;
    background: #fafbfc;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    flex-shrink: 0;
}

:deep(.ant-card-head-title) {
    font-size: 18px;
    font-weight: 600;
    color: #1f2a44;
}

/* 图表样式 */
:deep(.ant-row .ant-col .ant-card) {
    height: 400px;
    display: flex;
    flex-direction: column;
}

:deep(.ant-row .ant-col .ant-card-body) {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 16px;
}

/* 图表 */
.trend-chart,
:deep(.ant-card .chart-container) {
    border-radius: 8px;
    background: #f9fafb;
    padding: 16px;
    transition: background 0.3s ease;
}

:deep(.ant-row .ant-col .ant-card [ref="categoryChart"]),
:deep(.ant-row .ant-col .ant-card [ref="ratingPieChart"]) {
    height: 300px;
    flex: 1;
}

/* 过滤器区域的选择框 */
:deep(.filter-container .ant-select) {
    min-width: 150px;
    height: 32px;
}

:deep(.filter-container .ant-select-selector) {
    height: 32px !important;
    line-height: 32px !important;
    border-radius: 6px !important;
    border: 1px solid #d9dfe7 !important;
    transition: border-color 0.3s ease;
}

:deep(.filter-container .ant-select-selector:hover) {
    border-color: #1890ff !important;
}

/* 警告 */
:deep(.ant-alert) {
    border-radius: 8px;
    margin-bottom: 24px;
    padding: 16px;
}

:deep(.ant-alert-message) {
    font-size: 16px;
    font-weight: 500;
}

:deep(.ant-alert-description) {
    font-size: 14px;
    color: #5c6b8a;
}

/* 列表表格 */
:deep(.ant-table) {
    border-radius: 8px;
    overflow: hidden;
    background: #ffffff;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

:deep(.ant-table-thead > tr > th) {
    background: #fafbfc;
    color: #1f2a44;
    font-weight: 600;
    padding: 12px 16px;
    border-bottom: 1px solid #e8ecef;
}

:deep(.ant-table-tbody > tr > td) {
    padding: 12px 16px;
    border-bottom: 1px solid #f0f2f5;
    color: #344563;
}

:deep(.ant-table-tbody > tr:hover > td) {
    background: #f5f7fa;
}

/* 按钮 */
:deep(.ant-btn) {
    border-radius: 6px;
    padding: 8px 16px;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    line-height: 1;
}

:deep(.ant-btn-primary) {
    background: #1890ff;
    border-color: #1890ff;
}

:deep(.ant-btn-primary:hover) {
    background: #40a9ff;
    border-color: #40a9ff;
    transform: translateY(-1px);
}

:deep(.ant-btn-danger) {
    background: #ff4d4f;
    border-color: #ff4d4f;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 4px 16px;
    line-height: 20px;
}

:deep(.ant-btn-danger:hover) {
    background: #ff7875;
    border-color: #ff7875;
    transform: translateY(-1px);
}

:deep(.ant-btn-link) {
    padding: 0 8px;
}

:deep(.ant-btn-link:hover) {
    color: #40a9ff;
}

/* 分页 */
:deep(.ant-pagination) {
    margin-top: 16px;
    padding: 8px 0;
}

:deep(.ant-pagination-item) {
    border-radius: 4px;
    border: 1px solid #d9dfe7;
}

:deep(.ant-pagination-item-active) {
    background: #1890ff;
    border-color: #1890ff;
}

:deep(.ant-pagination-item-active a) {
    color: #ffffff;
}

:deep(.ant-pagination-options .ant-select) {
    width: 100px !important;
    height: 32px !important;
}

:deep(.ant-pagination-options .ant-select-selector) {
    height: 32px !important;
    line-height: 32px !important;
    font-size: 14px !important;
    padding: 0 24px 0 8px !important;
    border-radius: 4px !important;
    border: 1px solid #d9dfe7 !important;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

:deep(.ant-pagination-options .ant-select-selector:hover) {
    border-color: #1890ff !important;
}

:deep(.ant-pagination-options .ant-select .ant-select-arrow) {
    font-size: 12px !important;
    right: 8px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    color: #666 !important;
    line-height: 1 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    height: 12px !important;
    width: 12px !important;
    margin-top: 0 !important;
    pointer-events: none !important;
    position: absolute !important;
}

/* 无评分样式 */
:deep(.no-score) {
    color: #999;
    font-style: italic;
}

/* 过滤器样式 */
.filter-container {
    background: #f9fafb;
    border-radius: 8px;
    padding: 12px 16px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
}

.filter-item {
    display: flex;
    align-items: center;
    gap: 8px;
}

.filter-label {
    color: #1f2a44;
    font-weight: 500;
    font-size: 14px;
    line-height: 32px;
}

/* 日期范围选择器 */
:deep(.filter-container .ant-picker) {
    height: 32px;
    border-radius: 6px;
}

/* 重置过滤器按钮 */
:deep(.ant-btn-default) {
    height: 32px;
    line-height: 32px;
    padding: 0 16px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
}
</style>