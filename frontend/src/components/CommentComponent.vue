<template>
    <div class="comment-container">
        <h3>评论 ({{ totalCommentsCount }})</h3>

        <!-- 评论输入区 -->
        <div v-if="isLoggedIn">
            <div v-if="showForm" class="comment-form">
                <a-textarea v-model:value="newComment" placeholder="写下你的评论..." :rows="4" />
                <div class="form-actions">
                    <a-button type="primary" @click="submitComment" :loading="submitting">提交</a-button>
                    <a-button style="margin-left: 8px;" @click="showForm = false">取消</a-button>
                </div>
            </div>
            <div v-else class="comment-button">
                <a-button type="primary" @click="showForm = true">我要评论</a-button>
            </div>
        </div>
        <div v-else class="login-prompt">
            <a-button type="link" @click="showLogin">登录后评论</a-button>
        </div>

        <!-- 评论列表 -->
        <div class="comment-list">
            <CommentItem v-for="comment in comments" :key="comment.id" :comment="comment"
                :currentUsername="currentUsername" :isLoggedIn="isLoggedIn" @reply="submitReply"
                @delete="deleteComment" />
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import axios from '../utils/axios';
import { message } from 'ant-design-vue';
import { useRoute } from 'vue-router';
import { useUIStore } from '../stores/ui';
import { useUserStore } from '../stores/user';
import CommentItem from './CommentItem.vue';
import { emitter } from '../utils/eventBus';

const props = defineProps({
    movieId: {
        type: Number,
        required: true
    }
});

const uiStore = useUIStore();
const userStore = useUserStore();

const route = useRoute();
const comments = ref([]);
const newComment = ref('');
const submitting = ref(false); // 是否提交评论
const isLoggedIn = computed(() => userStore.isLoggedIn);
const currentUsername = localStorage.getItem('username'); // 当前登录用户名

const showForm = ref(false); // 是否显示评论输入框

// 计算某个评论及其子评论的总评论数
const countComments = (comment) => {
    let count = 1; // 本条评论
    if (comment.replies && comment.replies.length > 0) {
        for (const reply of comment.replies) {
            count += countComments(reply); // 递归加子评论
        }
    }
    return count;
};

// 计算总评论数
const totalCommentsCount = computed(() => {
    return comments.value.reduce((total, comment) => total + countComments(comment), 0);
});

// 获取评论
const fetchComments = async () => {
    try {
        const res = await axios.get(`/api/movies/${props.movieId}/comments/`);
        comments.value = res.data;
    } catch (error) {
        console.error('获取评论失败:', error);
    }
};

// 提交评论
const submitComment = async () => {
    if (!newComment.value.trim()) {
        message.warning('评论内容不能为空');
        return;
    }

    submitting.value = true;
    try {
        await axios.post('/api/user/comments/', {
            movie: props.movieId,
            comment: newComment.value
        }, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        message.success('评论成功');
        newComment.value = '';
        showForm.value = false;
        fetchComments();
    } catch (error) {
        console.error('评论失败:', error);
        message.error('评论失败');
    } finally {
        submitting.value = false;
    }
};

// 显示登录
const showLogin = () => {
    if (route.path !== '/') {
        uiStore.openLoginModal()
    } else {
        message.info('请先登录');
    }
};

// 删除评论
const deleteComment = async (commentId) => {
    try {
        await axios.delete(`/api/comments/${commentId}/`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        message.success('评论已删除');
        fetchComments(); // 重新拉取评论列表
    } catch (error) {
        console.error('删除评论失败:', error);
        message.error('删除评论失败');
    }
};

// 提交回复
const submitReply = async (parentId, content) => {
    try {
        await axios.post(`/api/comments/${parentId}/reply/`, {
            comment: content,
            movie: props.movieId
        }, {
            headers: {
                Authorization: `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        message.success('回复成功');
        fetchComments();
    } catch (error) {
        console.error('回复失败:', error);
        message.error('回复失败');
    }
};

// 登录成功后加载数据
const handleLoginSuccess = () => {
    fetchComments();
};

// 挂载时获取评论
onMounted(() => {
    emitter.on('login-success', handleLoginSuccess);
    fetchComments();
});

// 组件卸载时移除事件监听
onUnmounted(() => {
    emitter.off('login-success', handleLoginSuccess);
});
</script>

<style scoped>
.comment-container {
    margin: 20px 0;
}

.comment-button {
    margin-bottom: 20px;
    text-align: left;
}

.comment-form {
    margin-bottom: 20px;
}

.form-actions {
    margin-top: 10px;
    text-align: right;
}

.login-prompt {
    margin-bottom: 20px;
    text-align: center;
}

.comment-list {
    border-top: 1px solid #f0f0f0;
    max-height: 500px;
    overflow-y: auto;
    padding-right: 10px;
}
</style>
