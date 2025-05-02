import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    component: () => import("../components/Layout.vue"),
  },
  {
    path: "/movie/:id",
    name: "MovieDetail",
    component: () => import("../pages/MovieDetail.vue"),
    meta: {
      breadcrumb: (route) => {
        const from = route.query.from;
        return from === "ranking" ? ["榜单", "详情"] : ["首页", "详情"]; // 动态面包屑
      },
    },
  },
  {
    path: "/movies/ranking",
    component: () => import("../pages/RankList.vue"),
    meta: {
      menuKey: "ranking", // 菜单标识
      breadcrumb: ["榜单"],
    },
  },
  {
    path: "/movies/recommend",
    component: () => import("../pages/RecommendPage.vue"),
    meta: {
      menuKey: "recommend",
      breadcrumb: ["推荐"],
    },
  },
  {
    path: "/user/register",
    component: () => import("../pages/Register.vue"),
    meta: { fullScreen: true }, // 标记为全屏页面
  },
  {
    path: "/user/login",
    component: () => import("../pages/Login.vue"),
    meta: { fullScreen: true },
  },
  {
    path: "/user/profile",
    component: () => import("../pages/UserProfile.vue"),
    meta: {
      requiresAuth: true, // 需要登录才能访问
    },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes: routes,
});

// 路由全局前置守卫
router.beforeEach(async (to) => {
  const isAuthRoute = to.meta.requiresAuth;
  const hasValidToken = !!localStorage.getItem("access_token");

  // 需要认证但未登录 → 跳转登录，并记录当前路径
  if (isAuthRoute && !hasValidToken) {
    return {
      path: "/user/login",
      query: { redirect: to.fullPath }, // 保存完整路径，包括查询参数
    };
  }

  // 已登录但访问登录/注册页 → 跳首页
  if (["/user/login", "/user/register"].includes(to.path) && hasValidToken) {
    return "/";
  }
});

export default router;
