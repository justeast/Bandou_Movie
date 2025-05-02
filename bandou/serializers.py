from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy
from django.utils import timezone
import os
import time
from bandou.models import Movie, User, Rating, Comments


class MovieModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = "__all__"


class UserModelSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)  # 确认密码字段，只用于序列化输入，不保存至数据库

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 'phone']
        extra_kwargs = {
            'password': {'write_only': True},  # 用户输入的密码不需要存储到数据库，需经过哈希加密处理
            'email': {'required': True}
        }

    def validate(self, attrs):
        """
        验证两次密码输入一致
        """
        if attrs['password'] != attrs.pop('confirm_password'):
            raise serializers.ValidationError('请确保两次输入的密码一致!')
        return attrs

    def create(self, validated_data):
        """
        反序列化创建用户并对密码进行加密
        """
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            password=make_password(validated_data['password']),
            phone=validated_data.get('phone', '')  # 将"phone"作为可选字段
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class UserProfileSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()  # 用户头像url,只读，由get_avatar_url方法动态生成

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'avatar_url', 'avatar']
        extra_kwargs = {
            'phone': {
                'required': False
            },
            'avatar': {
                'write_only': True
            }
        }

    def get_avatar_url(self, obj):
        """
        动态生成用户头像绝对路径
        :param obj:当前被序列化的用户对象(即User模型实例)
        """
        if obj.avatar:
            # ImageField继承自FileField,FileField有url属性 => MEDIA_URL + 文件相对路径
            return self.context['request'].build_absolute_uri(obj.avatar.url)
        return None

    def validate_username(self, value):
        """用户名唯一性验证"""
        if User.objects.exclude(pk=self.instance.pk).filter(username=value).exists():
            raise serializers.ValidationError('该用户名已被使用！')
        return value


class UserAvatarUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['avatar']
        extra_kwargs = {'avatar': {'required': False}}

    def validate_avatar(self, value):  # noqa
        """用户头像上传图片文件校验"""
        if not value:
            return None

        valid_extensions = ['jpg', 'jpeg', 'png']  # 限制文件类型
        extension = value.name.split('.')[-1].lower()
        if extension not in valid_extensions:
            raise ValidationError(f"不支持的文件格式，仅支持 {', '.join(valid_extensions)}")

        max_size = 5 * 1024 * 1024  # 限制文件大小 (5MB)
        if value.size > max_size:
            raise ValidationError(f"文件大小超过限制（最大 {max_size // 1024 // 1024}MB）")

        return value

    def update(self, instance, validated_data):
        avatar_file = validated_data.get('avatar')

        if avatar_file:
            # 删除旧文件
            if instance.avatar:
                instance.avatar.delete()

            # 生成新文件名
            ext = os.path.splitext(avatar_file.name)[1]
            new_name = f"user_{instance.id}_{int(time.time())}{ext}"

            # 保存文件
            instance.avatar.save(new_name, avatar_file)

        return instance


def validate_password_custom(value):
    """自定义用户新密码校验"""
    if len(value) < 8:
        raise ValidationError(gettext_lazy("密码至少8个字符"))
    if not any(c.isupper() for c in value):
        raise ValidationError(gettext_lazy("需包含至少一个大写字母"))
    if not any(c.islower() for c in value):
        raise ValidationError(gettext_lazy("需包含至少一个小写字母"))
    if not any(c.isdigit() for c in value):
        raise ValidationError(gettext_lazy("需包含至少一个数字"))


class UserPasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password_custom])
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        """用户旧密码校验"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise ValidationError('原密码错误！')
        return value

    def validate(self, attrs):
        """用户输入新密码一致性校验"""
        if attrs['new_password'] != attrs['confirm_password']:
            raise ValidationError('两次输入的新密码不一致！')
        return attrs


class RatingSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(source='movie.title', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Rating
        fields = ['id', 'user', 'movie', 'movie_title', 'username', 'rating', 'rating_time']
        read_only_fields = ['user', 'rating_time']
        extra_kwargs = {
            'rating': {'min_value': 0, 'max_value': 5}
        }

    def validate(self, attrs):
        # 如果是更新操作
        if self.instance is not None:
            # 如果请求数据中有movie字段
            if 'movie' in attrs:
                # 如果尝试修改关联的电影
                if self.instance.movie.id != attrs['movie'].id:
                    raise serializers.ValidationError("不能修改电影关联")
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        movie = validated_data['movie']

        # 检查是否已评分，如果已评分则更新
        rating, created = Rating.objects.update_or_create(
            user=user,
            movie=movie,
            defaults={
                'rating': validated_data['rating'],
                'rating_time': timezone.now()
            }
        )
        return rating


class CommentSerializer(serializers.ModelSerializer):
    # 通过PrimaryKeyRelatedField,在反序列化时,可以将movie_id转换为movie对象
    movie = serializers.PrimaryKeyRelatedField(
        queryset=Movie.objects.all(),
        required=False,
        write_only=True
    )

    movie_title = serializers.CharField(source='movie.title', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    avatar_url = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    comment = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={'blank': '评论内容不能为空'}
    )
    replies = serializers.SerializerMethodField()

    # 在反序列化时，使用PrimaryKeyRelatedField将parent_comment_id转换为Comments对象
    parent_comment = serializers.PrimaryKeyRelatedField(queryset=Comments.objects.all(), required=False)

    parent_comment_user = serializers.SerializerMethodField()

    class Meta:
        model = Comments
        fields = ['id', 'user', 'movie', 'movie_title', 'username', 'avatar_url', 'comment', 'comment_time', 'rating',
                  'replies', 'parent_comment', 'parent_comment_user']
        read_only_fields = ['user', 'comment_time', 'replies', 'parent_comment_user']

    def get_avatar_url(self, obj):
        """动态生成用户头像绝对路径"""
        if not hasattr(obj.user, 'avatar'):
            return None
        if not obj.user.avatar:
            return None
        if 'request' not in self.context:
            return None
        return self.context['request'].build_absolute_uri(obj.user.avatar.url)

    def get_rating(self, obj):  # noqa
        """获取该评论用户对该电影的评分"""
        rating = Rating.objects.filter(user=obj.user, movie=obj.movie).first()
        return rating.rating if rating else None

    def get_replies(self, obj):  # noqa
        """获取该评论的回复"""
        replies = obj.replies.all()
        return CommentSerializer(replies, many=True, context=self.context).data

    def get_parent_comment_user(self, obj):  # noqa
        """获取该评论的父评论用户"""
        if obj.parent_comment:
            return obj.parent_comment.user.username
        return None

    def create(self, validated_data):
        user = self.context['request'].user
        comment = Comments.objects.create(
            user=user,
            movie=validated_data.get('movie'),
            comment=validated_data['comment'],
            comment_time=timezone.now(),
            parent_comment=validated_data.get('parent_comment')
        )
        return comment
