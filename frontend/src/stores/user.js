import { defineStore } from "pinia";
import axios from "../utils/axios";

export const useUserStore = defineStore("user", {
  state: () => ({
    userInfo: null,
    isLoggedIn: false,
    isAdmin: false,
  }),
  actions: {
    async fetchUserProfile() {
      try {
        const response = await axios.get("/api/user/profile/");
        this.userInfo = response.data;
        this.isLoggedIn = true;
        this.isAdmin = response.data.is_superuser || response.data.is_staff;
        return response.data;
      } catch (error) {
        this.clearUser();
        throw error;
      }
    },
    clearUser() {
      this.userInfo = null;
      this.isLoggedIn = false;
      this.isAdmin = false;
    },
    async logout() {
      try {
        const refreshToken = localStorage.getItem("refresh_token");
        if (refreshToken) {
          await axios
            .post("/api/user/logout/", { refresh: refreshToken })
            .catch((error) => {
              // 忽略黑名单错误
              if (
                error.response?.data?.error?.includes("Token is blacklisted")
              ) {
                return; // 黑名单错误直接忽略
              }
              throw error; // 其他错误继续抛出
            });
        }
      } catch (error) {
        // 记录非黑名单错误（调试用）
        console.error("注销失败:", error);
      } finally {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        this.clearUser();
      }
    },
    updateAvatar(newUrl) {
      if (this.userInfo) {
        this.userInfo.avatar_url = newUrl;
      }
    },
  },
});
