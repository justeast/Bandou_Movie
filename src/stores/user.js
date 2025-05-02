// src/stores/user.js
import { defineStore } from "pinia";
import axios from "../utils/axios";

export const useUserStore = defineStore("user", {
  state: () => ({
    userInfo: null,
    isLoggedIn: false,
  }),
  actions: {
    async fetchUserProfile() {
      try {
        const response = await axios.get("/api/user/profile/");
        this.userInfo = response.data;
        this.isLoggedIn = true;
        return response.data;
      } catch (error) {
        this.clearUser();
        throw error;
      }
    },
    clearUser() {
      this.userInfo = null;
      this.isLoggedIn = false;
    },
    async logout() {
      try {
        const refreshToken = localStorage.getItem("refresh_token");
        await axios.post("/api/user/logout/", { refresh: refreshToken });
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
