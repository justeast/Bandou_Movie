<template>
    <a-modal :open="visible" :title="isNew ? '添加电影' : '编辑电影'" @cancel="handleCancel" @ok="handleSubmit"
        :confirmLoading="loading" width="800px" cancelText="取消" okText="保存">
        <a-form :model="formData" :rules="rules" ref="editForm" :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }">
            <a-form-item label="电影名称" name="title">
                <a-input v-model:value="formData.title" placeholder="请输入电影名称" />
            </a-form-item>

            <a-form-item label="导演" name="director">
                <a-input v-model:value="formData.director" placeholder="请输入导演" />
            </a-form-item>

            <a-form-item label="主演" name="starring">
                <a-select v-model:value="actorTags" mode="tags" style="width: 100%" placeholder="输入演员名称后按回车，多个演员将自动分隔"
                    :token-separators="['/']" @change="handleActorsChange"></a-select>
            </a-form-item>

            <a-form-item label="电影类型" name="type">
                <a-select v-model:value="typeTags" mode="tags" style="width: 100%" placeholder="选择或输入电影类型"
                    :token-separators="['/']" @change="handleTypesChange" :options="movieTypeOptions"
                    :loading="loadingTypes">
                </a-select>
            </a-form-item>

            <a-form-item label="上映日期" name="release_time">
                <a-date-picker v-model:value="releaseDateMoment" style="width: 100%" :format="dateFormat"
                    placeholder="选择上映日期" :locale="locale" @change="handleDateChange" />
            </a-form-item>

            <a-form-item label="简介" name="brief_introduction">
                <a-textarea v-model:value="formData.brief_introduction" :rows="4" placeholder="请输入电影简介" />
            </a-form-item>

            <a-form-item label="封面图片" name="cover">
                <a-upload list-type="picture-card" v-model:file-list="fileList" :custom-request="handleCustomUpload"
                    @remove="handleRemove" :locale="uploadLocale" @preview="handlePreview">
                    <div v-if="fileList.length < 1">
                        <plus-outlined />
                        <div style="margin-top: 8px">上传</div>
                    </div>
                </a-upload>
                <!-- 自定义预览模态框 -->
                <a-modal :open="previewVisible" :footer="null" @cancel="handlePreviewCancel">
                    <img alt="预览图片" style="width: 100%" :src="previewImage" />
                </a-modal>
            </a-form-item>
        </a-form>
    </a-modal>
</template>

<script setup>
import { ref, reactive, watch, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import axios from '../utils/axios';
import { PlusOutlined } from '@ant-design/icons-vue';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import locale from 'ant-design-vue/es/date-picker/locale/zh_CN';

const props = defineProps({
    visible: Boolean,
    movieId: [Number, String, null],
});

const emit = defineEmits(['update:visible', 'success']);

const isNew = computed(() => !props.movieId);
const loading = ref(false);
const fileList = ref([]);
const dateFormat = 'YYYY-MM-DD';
const releaseDateMoment = ref(null);
const editForm = ref(null);

const actorTags = ref([]);
const typeTags = ref([]);
const movieTypeOptions = ref([]);
const loadingTypes = ref(false);

// 自定义上传组件文本
const uploadLocale = {
    removeFile: '删除文件',
    previewFile: '预览文件',
    downloadFile: '下载文件',
    uploading: '上传中...',
    uploadError: '上传错误',
    uploadSuccess: '上传成功'
};

// 图片缓存处理
const imageCache = ref(JSON.parse(localStorage.getItem("imageCache")) || {});

// 处理图片 URL
const cachedImage = (url) => {
    if (!url) return '';

    // 检查是否是本地图片路径（以/media/开头）
    if (url.startsWith('/media/')) {
        // 本地图片直接返回完整URL
        return `http://127.0.0.1:8000${url}`;
    }

    // 外部图片使用代理
    if (!imageCache.value[url]) {
        const proxyUrl = `http://127.0.0.1:8000/proxy_image/?url=${encodeURIComponent(url)}`;
        imageCache.value[url] = proxyUrl;
        localStorage.setItem("imageCache", JSON.stringify(imageCache.value));
    }
    return imageCache.value[url];
};

// 添加预览相关的状态
const previewVisible = ref(false);
const previewImage = ref('');

// 处理图片预览
const handlePreview = (file) => {
    // 优先使用原始文件对象的URL
    if (file.originFileObj) {
        previewImage.value = URL.createObjectURL(file.originFileObj);
    } else {
        previewImage.value = file.url || file.thumbUrl;
    }
    previewVisible.value = true;
};

// 关闭预览
const handlePreviewCancel = () => {
    previewVisible.value = false;
    // 释放 createObjectURL 创建的URL
    if (previewImage.value && previewImage.value.startsWith('blob:')) {
        URL.revokeObjectURL(previewImage.value);
    }
    previewImage.value = '';
};

// 自定义上传处理
const handleCustomUpload = ({ file, onSuccess }) => {
    // 验证文件
    const isImage = file.type.startsWith('image/');
    if (!isImage) {
        message.error('只能上传图片文件!');
        return;
    }

    const isLt5M = file.size / 1024 / 1024 < 5;
    if (!isLt5M) {
        message.error('图片必须小于5MB!');
        return;
    }

    // 创建预览
    const reader = new FileReader();
    reader.onload = () => {
        const dataUrl = reader.result;

        // 创建预览对象
        const fileObj = {
            uid: `-${Date.now()}`,
            name: file.name,
            status: 'done',
            url: dataUrl,
            thumbUrl: dataUrl,
            originFileObj: file,
        };

        // 更新文件列表
        fileList.value = [fileObj];

        // 更新表单数据
        formData.cover = file;
        formData.cover_url = '';

        // 触发验证
        if (editForm.value) {
            editForm.value.validateFields(['cover']);
        }

        // 通知上传组件上传成功
        onSuccess();
    };

    reader.readAsDataURL(file);
};

// 表单数据
const formData = reactive({
    title: '',
    director: '',
    starring: '',
    brief_introduction: '',
    type: '',
    release_time: '',
    cover: null,
    cover_url: '',
});

// 表单验证规则
const rules = {
    title: [{ required: true, message: '请输入电影名称' }],
    director: [{ required: true, message: '请输入导演' }],
    type: [{ required: true, message: '请输入电影类型' }],
    release_time: [{ required: true, message: '请选择上映日期' }],
    cover: [{
        required: isNew.value,
        message: '请上传电影封面图片',
        validator: () => {
            // 直接检查fileList长度或formData.cover是否存在
            if (isNew.value && fileList.value.length === 0 && !formData.cover) {
                return Promise.reject('请上传电影封面图片');
            }
            return Promise.resolve();
        }
    }],
};

// 获取所有电影类型
const fetchMovieTypes = async () => {
    try {
        loadingTypes.value = true;
        const response = await axios.get('/bandou/admin/movies/movie_types/');
        const uniqueTypes = new Set();

        // 从所有电影中提取类型
        response.data.forEach(type => {
            if (type && type.trim()) {
                uniqueTypes.add(type.trim());
            }
        });

        // 转换为选项格式
        movieTypeOptions.value = Array.from(uniqueTypes).map(type => ({
            label: type,
            value: type
        }));
    } catch (error) {
        console.error('获取电影类型失败', error);
    } finally {
        loadingTypes.value = false;
    }
};

// 在组件挂载时获取电影类型
onMounted(() => {
    fetchMovieTypes();
});

const resetForm = () => {
    Object.keys(formData).forEach(key => {
        formData[key] = '';
    });
    fileList.value = [];
    releaseDateMoment.value = null;
    actorTags.value = [];
    typeTags.value = [];
    if (editForm.value) {
        editForm.value.resetFields();
    }
};

// 加载电影数据
const loadMovieData = async (id) => {
    try {
        loading.value = true;
        const response = await axios.get(`/bandou/admin/movies/${id}/`);
        const movie = response.data;

        // 填充表单数据
        formData.title = movie.title || '';
        formData.director = movie.director || '';
        formData.starring = movie.starring || '';
        formData.brief_introduction = movie.brief_introduction || '';
        formData.type = movie.type || '';
        formData.cover_url = movie.cover_url || '';

        // 处理主演标签
        if (movie.starring) {
            actorTags.value = movie.starring.split(' / ').map(actor => actor.trim());
        } else {
            actorTags.value = [];
        }

        // 处理电影类型标签
        if (movie.type) {
            typeTags.value = movie.type.split(' / ').map(type => type.trim());
        } else {
            typeTags.value = [];
        }

        // 处理日期
        if (movie.release_time) {
            formData.release_time = movie.release_time;
            releaseDateMoment.value = dayjs(movie.release_time);
        }

        // 处理封面图片 - 使用代理URL
        if (movie.cover_url) {
            const proxyUrl = cachedImage(movie.cover_url);
            fileList.value = [
                {
                    uid: '-1',
                    name: 'cover.jpg',
                    status: 'done',
                    url: proxyUrl,
                    thumbUrl: proxyUrl,
                },
            ];
        }
    } catch (error) {
        message.error('加载电影数据失败');
        console.error(error);
    } finally {
        loading.value = false;
    }
};

// 处理演员变化
const handleActorsChange = (values) => {
    // 将数组转换回格式 "演员1 / 演员2 / 演员3"
    formData.starring = values.join(' / ');
};

// 处理类型变化
const handleTypesChange = (values) => {
    // 将数组转换回格式 "类型1 / 类型2"
    formData.type = values.join(' / ');
};

// 监听movieId变化，加载电影数据
watch(
    () => props.movieId,
    async (newId) => {
        if (newId) {
            await loadMovieData(newId);
        } else {
            resetForm();
        }
    }
);

// 监听visible变化，当关闭时重置表单
watch(
    () => props.visible,
    (isVisible) => {
        if (!isVisible) {
            // 模态框关闭时重置表单
            resetForm();
        } else if (props.movieId) {
            // 模态框打开且有ID时加载数据
            loadMovieData(props.movieId);
        } else {
            // 模态框打开但没有ID时重置表单（新建）
            resetForm();
        }
    }
);

// 监听日期选择器的变化
watch(
    () => releaseDateMoment.value,
    (newDate) => {
        if (newDate) {
            formData.release_time = dayjs(newDate).format('YYYY-MM-DD');
        } else {
            formData.release_time = '';
        }
    }
);



// 添加日期选择的change事件处理函数
const handleDateChange = (date) => {
    if (date) {
        formData.release_time = dayjs(date).format('YYYY-MM-DD');
        // 手动触发release_time字段的验证
        if (editForm.value) {
            editForm.value.validateFields(['release_time']);
        }
    } else {
        formData.release_time = '';
    }
};

// 处理图片移除
const handleRemove = () => {
    fileList.value = [];
    formData.cover = null;
    formData.cover_url = '';

    // 手动触发cover字段的验证
    if (editForm.value) {
        editForm.value.validateFields(['cover']);
    }
};

// 取消表单
const handleCancel = () => {
    emit('update:visible', false);
};

// 提交表单
const handleSubmit = async () => {
    // 确保日期已经被正确设置
    if (releaseDateMoment.value) {
        formData.release_time = dayjs(releaseDateMoment.value).format('YYYY-MM-DD');
    }


    if (editForm.value) {
        try {
            await editForm.value.validate();
        } catch (error) {
            console.error('表单验证失败:', error);
            return; // 验证失败，不继续提交
        }
    }

    try {
        loading.value = true;

        // 构建表单数据
        const formDataToSend = new FormData();
        Object.keys(formData).forEach(key => {
            if (formData[key] !== null && formData[key] !== undefined && formData[key] !== '') {
                if (key === 'cover' && formData[key]) {
                    formDataToSend.append('cover', formData[key]);
                } else if (key !== 'cover') {
                    formDataToSend.append(key, formData[key]);
                }
            }
        });

        let response;
        if (isNew.value) {
            // 创建新电影
            response = await axios.post('/bandou/admin/movies/', formDataToSend, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
        } else {
            // 更新电影 - PATCH部分更新
            response = await axios.patch(`/bandou/admin/movies/${props.movieId}/`, formDataToSend, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
        }

        message.success(isNew.value ? '添加电影成功' : '更新电影成功');
        // 清除图片缓存
        if (response.data && response.data.cover_url) {
            // 更新缓存
            const oldCoverUrl = formData.cover_url; // 保存修改前的URL
            if (oldCoverUrl && imageCache.value[oldCoverUrl]) {
                delete imageCache.value[oldCoverUrl]; // 删除旧缓存
            }
            // 为新URL添加缓存
            localStorage.setItem("imageCache", JSON.stringify(imageCache.value));
        }
        resetForm();
        emit('success');
        emit('update:visible', false);
    } catch (error) {
        if (error.response && error.response.data) {
            // 记录后端返回的错误信息
            const errorData = error.response.data;
            Object.keys(errorData).forEach(key => {
                message.error(`${key}: ${errorData[key].join(', ')}`);
            });
        } else {
            message.error(isNew.value ? '添加电影失败' : '更新电影失败');
        }
        console.error(error);
    } finally {
        loading.value = false;
    }
};
</script>

<style scoped>
/* 上传按钮样式 */
:deep(.ant-upload-select) {
    width: 128px !important;
    height: 128px !important;
}

:deep(.ant-upload-list-item) {
    width: 128px !important;
    height: 128px !important;
}

:deep(.ant-upload-list-item-thumbnail img) {
    object-fit: cover !important;
    width: 100% !important;
    height: 100% !important;
}

:deep(.ant-modal-content) {
    max-width: 90vw;
}

:deep(.ant-modal-body img) {
    max-width: 100%;
    max-height: 80vh;
    object-fit: contain;
    display: block;
    margin: 0 auto;
}

/* 表单样式 */
:deep(.ant-form-item-label > label) {
    font-weight: 500;
}

:deep(.ant-input),
:deep(.ant-picker),
:deep(.ant-input-textarea) {
    border-radius: 4px;
}
</style>