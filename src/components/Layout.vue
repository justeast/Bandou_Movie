Layout.vue:
<template>
  <!-- 全屏页面直接显示路由内容 -->
  <div v-if="isFullScreen" class="fullscreen-page">
    <router-view />
  </div>

  <a-layout v-else class="layout-with-fixed-header">
    <template v-if="isRouteReady">
      <a-layout-header class="header">
        <div class="logo">
          <img src="../assets/bandou_logo.png" alt="Logo">
        </div>
        <a-menu v-model:selectedKeys="selectedKeysTop" theme="dark" mode="horizontal" :style="{ lineHeight: '64px' }">
          <a-menu-item key="home" @click="selectHome">首 页</a-menu-item>
          <a-menu-item key="ranking" @click="selectRanking">榜 单</a-menu-item>
          <a-menu-item key="recommend" @click="selectRecommend">推 荐</a-menu-item>
        </a-menu>
        <!-- 用户头像区域 -->
        <div class="user-avatar-container">
          <a-dropdown v-if="userStore.isLoggedIn" class="avatar-dropdown">
            <a-avatar :src="userAvatar" :size="43" />
            <template #overlay>
              <a-menu>
                <a-menu-item key="profile" @click="router.push('/user/profile')">
                  <UserOutlined /> 个人中心
                </a-menu-item>
                <a-menu-item key="logout" @click="handleLogout">
                  <LogoutOutlined /> 注销
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>

          <a-dropdown v-else class="login-dropdown">
            <a-button type="link">
              登录/注册
            </a-button>
            <template #overlay>
              <a-menu>
                <a-menu-item key="login" @click="uiStore.showLoginModal = true">
                  <LoginOutlined /> 登录
                </a-menu-item>
                <a-menu-item key="register" @click="uiStore.showRegisterModal = true">
                  <UserAddOutlined /> 注册
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>

      <!-- 注册模态框 -->
      <a-modal v-model:open="uiStore.showRegisterModal" title="用户注册" :footer="null" :width="500">
        <register-form @success="handleRegisterSuccess" />
      </a-modal>

      <!-- 登录模态框 -->
      <a-modal v-model:open="uiStore.showLoginModal" title="用户登录" :footer="null" :width="400">
        <login-form @success="handleLoginSuccess" />
      </a-modal>

      <a-layout-content style="padding: 0 50px">
        <a-breadcrumb class="fixed-breadcrumb" style="margin: 0">
          <a-breadcrumb-item v-for="(item, index) in breadcrumbItems" :key="index">
            {{ item }}
          </a-breadcrumb-item>
        </a-breadcrumb>
        <div style="height: 60px"></div> <!-- 添加空白区域，确保内容不被面包屑遮挡 -->

        <a-layout style="padding: 24px 0; background: #fff">
          <a-layout-sider width="200" style="background: #fff" class="fixed-sider">
            <a-menu v-model:selectedKeys="selectedKeysSide" v-model:openKeys="openKeys" mode="inline"
              style="height: 100%">
              <a-sub-menu key="sub1">
                <template #title>
                  <span>

                    全 部
                  </span>
                </template>
                <a-menu-item key="all" @click="selectAllMovies">所有电影</a-menu-item>
              </a-sub-menu>
              <a-sub-menu key="sub2">
                <template #title>
                  <span>

                    分 类
                  </span>
                </template>
                <a-menu-item key="comedy" @click="selectCategory('comedy')">喜剧</a-menu-item>
                <a-menu-item key="action" @click="selectCategory('action')">动作</a-menu-item>
                <a-menu-item key="drama" @click="selectCategory('drama')">剧情</a-menu-item>
                <a-menu-item key="other" @click="selectCategory('other')">其他</a-menu-item>
              </a-sub-menu>
            </a-menu>
          </a-layout-sider>
          <a-layout-content :style="{ padding: '0 24px', minHeight: '600px' }" class="content-with-fixed-sider">
            <template v-if="$route.path === '/'">
              <a-row :gutter="[16, 24]">
                <a-col v-for="movie in movies" :key="movie.id" :span="6">
                  <movie-card :movie="movie"></movie-card>
                </a-col>
              </a-row>
            </template>
            <template v-else>
              <router-view @updateCategory="updateCategory"></router-view> <!--更新分类侧边栏-->
            </template>
            <a-back-top class="back-top" :visibilityHeight="700" />
          </a-layout-content>
        </a-layout>
      </a-layout-content>
    </template>
    <a-layout-footer style="text-align: center">
      HNIT ©2025 Created by LCL
    </a-layout-footer>
  </a-layout>
</template>
<script setup>
import axios from "../utils/axios";
import { onMounted, ref, computed, getCurrentInstance, watch } from "vue";
import MovieCard from "./MovieCard.vue";
import { useUserStore } from '../stores/user'
import { useUIStore } from '../stores/ui'
import { useRoute, useRouter } from "vue-router";
import { UserOutlined, LoginOutlined, LogoutOutlined, UserAddOutlined } from '@ant-design/icons-vue'; // 引入图标
import avatarImg from '../assets/avatar.png';
import { message } from 'ant-design-vue';
import RegisterForm from "./RegisterForm.vue";
import LoginForm from "./LoginForm.vue";
import { emitter } from "../utils/eventBus";

const route = useRoute()
const router = useRouter()

const userStore = useUserStore() //用户状态管理
const uiStore = useUIStore() // 注册登录模态框状态管理

const userAvatar = computed(() => userStore.userInfo?.avatar_url || avatarImg)

const isFullScreen = computed(() => route.meta.fullScreen);

// 顶部导航状态管理
const selectedKeysTop = ref([])

// 侧边栏状态管理
const selectedKeysSide = ref([])

// 打开菜单管理
const openKeys = ref(["sub1", "sub2"]);

// 同步初始化路由状态
const syncRouteState = () => {
  // 处理详情页的特殊情况
  if (route.path.startsWith('/movie/')) {
    const from = route.query.from;
    selectedKeysTop.value = [from || 'home']; // 默认为home如果没指定来源
    selectedKeysSide.value = ['all']; // 侧边栏默认选择
    return;
  }

  // 处理顶部导航
  const currentMenuKey = route.meta.menuKey || 'home'
  selectedKeysTop.value = [currentMenuKey]

  // 处理侧边栏
  if (route.path === '/') {
    const category = route.query.category?.toString() || 'all'
    selectedKeysSide.value = [category]
  } else {
    selectedKeysSide.value = ['all']
  }
}

// 动态面包屑计算属性
const breadcrumbItems = computed(() => {
  // 处理全屏页面
  if (isFullScreen.value) return []

  // 处理详情页
  if (route.path.startsWith('/movie/')) {
    const from = route.query.from || 'home';
    return from === 'ranking'
      ? ['榜单', '详情']
      : ['首页', '详情'];
  }

  // 处理首页路径
  if (route.path === '/') {
    const category = route.query.category?.toString() || 'all'
    const items = ['首页']

    if (category === 'all') {
      items.push('全部', '所有电影')
    } else {
      items.push('分类', getCategoryLabel(category))
    }
    return items
  }

  if (route.path === '/movies/recommend') {
    return ['推荐'];
  }

  // 其他页面使用meta中的配置
  return route.meta.breadcrumb || []
})

const instance = getCurrentInstance()
// 暴露方法给全局
instance.appContext.config.globalProperties.$showLoginModal = () => {
  uiStore.showLoginModal = true
}

// 注册成功处理
const handleRegisterSuccess = () => {
  uiStore.showRegisterModal = false
  message.info('请登录您的账号', 3)
  uiStore.showLoginModal = true
}

// 登录成功处理
const handleLoginSuccess = async () => {
  uiStore.showLoginModal = false
  try {
    await userStore.fetchUserProfile()
    message.success('登录成功', 3)
    emitter.emit('login-success') // 触发登录成功事件：为了登录成功后用户评分的加载和评论的相关操作
  } catch (error) {
    message.error('获取用户信息失败', 3)
    console.log(error)
  }
}

// 注销处理
const handleLogout = async () => {
  try {
    await userStore.logout()
    message.success('注销成功', 3)
    router.push('/')
  } catch (error) {
    // 忽略黑名单错误
    if (!error.response?.data?.error?.includes("Token is blacklisted")) {
      message.error("注销失败", 3);
    }
  }
}

const movies = ref([])

// 获取全部电影
const getAllMovies = async () => {
  try {
    const response = await axios.get("/bandou/movies/")
    movies.value = response.data
  }
  catch (error) {
    console.error("获取全部电影失败！", error)
  }
}

// 跳转至全部电影
const selectAllMovies = () => {
  router.push({ path: "/", query: { category: "all" } }); // 只修改 URL，不调用 API
};

// 分类映射函数
const getCategoryLabel = (key) => {
  const categoryMap = {
    all: '所有电影',
    comedy: '喜剧',
    action: '动作',
    drama: '剧情',
    other: '其他'
  }
  return categoryMap[key] || key
}

// 获取分类电影
const getMoviesByCategory = async (categoryKey) => {
  try {
    const response = await axios.get(`/bandou/movies/?category=${categoryKey}`);
    movies.value = response.data;
  } catch (error) {
    console.error(`获取分类 ${categoryKey} 电影失败！`, error);
  }
};

// 点击首页
const selectHome = () => {
  router.push("/");
};

// 点击分类
const selectCategory = (categoryKey) => {
  router.push({ path: "/", query: { category: categoryKey } });
};

// 更新选中的分类
const updateCategory = (category) => {
  selectedKeysSide.value = [category];
};

// 跳转至榜单
const selectRanking = () => {
  router.push('/movies/ranking');
};

// 跳转至推荐
const selectRecommend = () => {
  router.push('/movies/recommend');
};

// 使用路由准备状态控制渲染
const isRouteReady = ref(false)
router.isReady().then(() => {
  isRouteReady.value = true
})

// 使用watch而不是watchEffect进行精确控制
watch(
  () => [route.path, route.query.category],
  () => {
    syncRouteState()
    // 仅在首页时加载数据
    if (route.path === '/') {
      const category = route.query.category?.toString() || 'all'
      getMoviesByCategory(category)
    }
  },
  { immediate: true }
)


onMounted(() => {
  getAllMovies() // 首次加载获取电影数据
})



</script>
<style scoped>
.header {
  display: flex;
  align-items: center;
  padding: 0 24px;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
}

.layout-with-fixed-header {
  padding-top: 64px;
  /* 导航栏高度 */
}

.logo {
  width: 80px;
  margin-right: 6px;
  margin-bottom: 6px;
}

.site-layout-background {
  background: #fff;
}

.back-top:hover {
  background: rgba(153, 142, 190, 0.5);
}


.user-avatar-container {
  margin-left: auto;
  display: flex;
  align-items: center;
}

/* 头像下拉菜单样式 */
.avatar-dropdown {
  cursor: pointer;
}

/* 登录按钮下拉菜单样式 */
.login-dropdown .ant-btn-link {
  padding: 0 12px;
  color: rgba(255, 255, 255, 0.85);
}

.login-dropdown .ant-btn-link:hover {
  color: #fff;
}


.fullscreen-page {
  min-height: 100vh;
  display: flex;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.fixed-breadcrumb {
  position: fixed;
  top: 64px;
  /* 导航栏高度 */
  left: 50px;
  right: 50px;
  z-index: 999;
  background: rgba(255, 255, 255, 0.65);
  /* 半透明背景 */
  padding: 10px 0;
  padding-left: 25px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  /* 添加轻微阴影 */
  border-radius: 4px;
  /* 圆角 */
}

/* 为固定面包屑腾出空间 */
.content-with-fixed-breadcrumb {
  margin-top: 60px;
  /* 调整为面包屑的实际高度加一些间距 */
  padding-top: 0;
  /* 移除原来的 padding-top */
}

.fixed-sider {
  position: fixed;
  top: 134px;
  /* 导航栏高度 + 面包屑高度 + 一些间距 */
  left: 50px;
  bottom: 70px;
  overflow-y: auto;
  z-index: 998;
  width: 200px !important;
  background: #fff;
  border-right: 1px solid #f0f0f0;
}

/* 为固定侧边栏腾出空间 */
.content-with-fixed-sider {
  margin-left: 200px;
  /* 侧边栏宽度 */
}
</style>
