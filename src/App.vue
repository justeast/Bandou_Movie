<script setup>
import { onMounted } from "vue";
import Layout from "./components/Layout.vue";
import { useUserStore } from "./stores/user";

const userStore = useUserStore();

onMounted(() => {
    // 如果已有 token 则尝试获取用户信息
    if (localStorage.getItem('access_token')) {
        userStore.fetchUserProfile().catch(() => {
            // 如果获取失败则清除无效 token
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
        })
    }
})
</script>

<template>
    <Layout></Layout>
</template>

<style scoped></style>
