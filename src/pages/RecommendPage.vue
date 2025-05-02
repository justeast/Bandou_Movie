<template>
    <div class="recommend-page">
        <movie-recommendation />
    </div>
</template>

<script setup>
import MovieRecommendation from '../components/MovieRecommendation.vue';
</script>

<style scoped>
.recommend-page {
    max-width: 1200px;
    margin: 0 auto;
    padding: 24px;
}
</style>