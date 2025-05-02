import { defineStore } from "pinia";
export const useUIStore = defineStore("ui", {
  state: () => ({
    showLoginModal: false,
    showRegisterModal: false,
  }),
  actions: {
    openLoginModal() {
      this.showLoginModal = true;
    },
    openRegister() {
      this.showRegisterModal = true;
    },
  },
});
