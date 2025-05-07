import { defineStore } from "pinia";
export const useUIStore = defineStore("ui", {
  state: () => ({
    showLoginModal: false,
    showRegisterModal: false,
    showPasswordResetRequestModal: false,
    showPasswordResetConfirmModal: false,
    resetEmail: localStorage.getItem("resetEmail") || "",
    codeExpirySeconds: 0, //验证码存储的剩余秒数
    codeExpiryTimestamp: 0, // 记录设置时间
  }),
  actions: {
    openLoginModal() {
      this.showLoginModal = true;
    },
    openRegister() {
      this.showRegisterModal = true;
    },
    openPasswordResetRequestModal() {
      this.showPasswordResetRequestModal = true;
    },
    openPasswordResetConfirmModal() {
      this.showPasswordResetConfirmModal = true;
    },
    setResetEmail(email) {
      this.resetEmail = email;
      localStorage.setItem("resetEmail", email);
    },
    clearResetEmail() {
      this.resetEmail = "";
      localStorage.removeItem("resetEmail");
    },
    setCodeExpiry(seconds) {
      this.codeExpirySeconds = Math.max(0, seconds);
      this.codeExpiryTimestamp = Date.now();
    },
    clearCodeExpiry() {
      this.codeExpirySeconds = 0;
      this.codeExpiryTimestamp = 0;
    },
  },
});
