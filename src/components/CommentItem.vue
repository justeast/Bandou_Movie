<template>
    <transition-group name="fade-slide" tag="div" class="comment-item">
        <div :key="comment.id">
            <!-- 头部 -->
            <div class="comment-header">
                <a-avatar :src="comment.avatar_url" />
                <span class="username">{{ comment.username }}</span>

                <div class="comment-actions">
                    <span v-if="comment.rating !== null" class="user-rating">评分：{{ comment.rating }}⭐</span>
                    <a-popconfirm v-if="props.isLoggedIn && comment.username === props.currentUsername" title="确定要删除吗？"
                        @confirm="$emit('delete', comment.id)" ok-text="确定" cancel-text="取消">
                        <a-button danger size="small" type="text">删除</a-button>
                    </a-popconfirm>
                    <a-button v-if="props.isLoggedIn" size="small" type="link" @click="showReplyInput">回复</a-button>
                </div>
            </div>

            <!-- 内容 -->
            <div class="comment-content-wrap">
                <div class="comment-content">
                    <span v-if="comment.parent_comment" style="color:#666;margin-right:5px">
                        @{{ comment.parent_comment_user }}:
                    </span>
                    {{ comment.comment }}
                </div>
                <div class="comment-time">
                    {{ formatTime(comment.comment_time) }}
                </div>
            </div>

            <!-- 回复输入框 -->
            <div v-if="isReplyVisible" class="reply-box">
                <a-textarea v-model:value="replyContent" placeholder="回复内容..." :rows="2" />
                <div class="form-actions">
                    <a-button size="small" type="primary" @click="submit">提交</a-button>
                    <a-button size="small" @click="cancel">取消</a-button>
                </div>
            </div>

            <!-- 子评论递归 -->
            <CommentItem v-for="reply in comment.replies" :key="reply.id" :comment="reply"
                :currentUsername="currentUsername" :isLoggedIn="isLoggedIn"
                @reply="(parentId, content) => $emit('reply', parentId, content)" @delete="$emit('delete', $event)" />
        </div>
    </transition-group>
</template>



<script setup>
import { ref } from 'vue';

const props = defineProps({
    comment: Object,
    currentUsername: String,
    isLoggedIn: Boolean
});
const emit = defineEmits(['reply', 'delete']);

const isReplyVisible = ref(false); // 是否显示回复输入框
const replyContent = ref('');

// 格式化时间
const formatTime = (timeString) => {
    return new Date(timeString).toLocaleString();
};

// 显示回复输入框
const showReplyInput = () => {
    isReplyVisible.value = true;
};

// 取消回复
const cancel = () => {
    isReplyVisible.value = false;
    replyContent.value = '';
};

// 提交回复
const submit = () => {
    if (!replyContent.value.trim()) return;
    emit('reply', props.comment.id, replyContent.value);
    cancel();
};
</script>

<style scoped>
.comment-item {
    margin: 15px 0;
    padding: 15px;
    border-radius: 10px;
    background: #ffffff;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    transition: box-shadow 0.3s;
}

.comment-item:hover {
    box-shadow: 0 4px 12px rgba(24, 144, 255, 0.4);
}

.comment-header {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
}

.header-left {
    display: flex;
    align-items: center;
    gap: 10px;
}

.username {
    margin-left: 10px;
    font-weight: bold;
}

.comment-actions {
    margin-left: auto;
    display: flex;
    gap: 8px;
}

.comment-content-wrap {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}

.comment-content {
    flex: 1;
    line-height: 1.6;
}

.comment-time {
    font-size: 12px;
    color: #999;
    margin-left: 10px;
    white-space: nowrap;
}

.user-rating {
    margin-left: 10px;
    color: #faad14;
    font-size: 14px;
}

.reply-box {
    margin-top: 12px;
    margin-left: 40px;
    padding: 12px;
    background: #f0f7ff;
    border: 1px solid #cce3ff;
    border-radius: 8px;
}

.reply-box .form-actions {
    margin-top: 8px;
    text-align: right;
}

.reply-list {
    margin-top: 12px;
    margin-left: 40px;
    padding-left: 16px;
    border-left: 2px solid #e6f4ff;
}

a-button[type="link"] {
    padding: 0;
    font-size: 13px;
    color: #1890ff;
}

a-button[type="link"]:hover {
    color: #40a9ff;
}


.fade-slide-enter-active {
    transition: all 0.4s ease;
}

.fade-slide-leave-active {
    transition: all 0.3s ease;
}

.fade-slide-enter-from {
    opacity: 0;
    transform: translateY(10px);
}

.fade-slide-enter-to {
    opacity: 1;
    transform: translateY(0);
}

.fade-slide-leave-from {
    opacity: 1;
    transform: translateY(0);
}

.fade-slide-leave-to {
    opacity: 0;
    transform: translateY(5px);
}
</style>
