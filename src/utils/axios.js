import axios from "axios";
import router from "../router";
import { message } from "ant-design-vue";
import { getErrorMessage } from "./errorHandler";

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
});

let isRefreshing = false; // 是否正在刷新 token
let refreshSubscribers = []; // 队列：等待 token 刷新的请求们

// 订阅 token 刷新完成的回调
function subscribeTokenRefresh(cb) {
  refreshSubscribers.push(cb);
}

// 通知所有等待的请求：token 刷新好了
function onRefreshed(newToken) {
  refreshSubscribers.forEach((cb) => cb(newToken));
  refreshSubscribers = [];
}

// 请求拦截器: 附加Authorization
instance.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：统一处理 401(access_token 过期)
instance.interceptors.response.use(
  (response) => response,
  async (error) => {
    // 确保error和error.config存在
    if (!error || !error.config) {
      console.error("未知错误:", error);
      message.error("发生未知错误，请刷新页面重试");
      return Promise.reject(error);
    }

    const originalRequest = error.config;
    const response = error.response;

    if (response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true; // 标记这个请求已经尝试过了

      if (!isRefreshing) {
        isRefreshing = true;
        const refreshToken = localStorage.getItem("refresh_token");

        // 如果没有refreshToken，直接跳转登录
        if (!refreshToken) {
          isRefreshing = false;
          localStorage.removeItem("access_token");
          message.error("会话已过期，请重新登录");

          // 登录跳转处理
          if (router.currentRoute.value.meta.requiresAuth) {
            router.push("/user/login");
          } else {
            router.app.config.globalProperties.$showLoginModal?.();
          }

          return Promise.reject(error);
        }

        try {
          const res = await axios.post(
            `${
              import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"
            }/api/token/refresh/`,
            { refresh: refreshToken }
          );

          const newAccessToken = res.data.access;
          const newRefreshToken = res.data.refresh;
          if (newAccessToken) {
            localStorage.setItem("access_token", newAccessToken);
          }
          if (newRefreshToken) {
            localStorage.setItem("refresh_token", newRefreshToken);
          }

          isRefreshing = false;
          onRefreshed(newAccessToken); // 通知所有等待的请求

          // 重新发送原始请求
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return instance(originalRequest);
        } catch (refreshError) {
          console.error("Token刷新失败:", getErrorMessage(refreshError));
          isRefreshing = false;
          refreshSubscribers = []; // 清空等待的请求

          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");

          message.error("会话已过期，请重新登录");

          // 登录跳转处理
          if (router.currentRoute.value.meta.requiresAuth) {
            router.push("/user/login");
          } else {
            router.app.config.globalProperties.$showLoginModal?.();
          }

          return Promise.reject(refreshError);
        }
      }

      // 等待新的 token 刷新完再继续请求
      return new Promise((resolve) => {
        subscribeTokenRefresh((newToken) => {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          resolve(instance(originalRequest)); // 重新发送请求
        });
      });
    }

    // 其他错误直接提示
    try {
      const errorMessage = getErrorMessage(error);
      message.error(errorMessage);
    } catch (e) {
      message.error("发生未知错误");
      console.log(e);
    }
    return Promise.reject(error);
  }
);

export default instance;
