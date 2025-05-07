from datetime import timedelta
import requests
import random
from django.http import HttpResponse
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from django.db.models import Value, Case, When, FloatField, Avg, Count
from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate, get_user_model
from bandou.utils.get_redis_instance import get_redis_instance
from bandou.utils.user_auth import get_tokens_for_user
from bandou.models import Movie, Rating, Comments, User
from bandou.serializers import MovieModelSerializer, UserModelSerializer, UserLoginSerializer, UserProfileSerializer, \
    UserAvatarUploadSerializer, UserPasswordChangeSerializer, RatingSerializer, CommentSerializer, \
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer

"""
电影类别中英文映射
"""
CATEGORY_MAPPING = {
    "comedy": "喜剧",
    "action": "动作",
    "drama": "剧情",
    "other": "其他"
}


@csrf_exempt
def proxy_bouban_movie_image(request):
    """
    根据cover_url获取电影封面图片
    """
    image_url = request.GET.get("url")
    if not image_url:
        return HttpResponse("URL 参数缺失", status=400)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0"}
    response = requests.get(image_url, headers=headers)

    if response.status_code == 200:
        img_response = HttpResponse(response.content, content_type="image/jpeg")
        img_response["Cache-Control"] = "public, max-age=86400"  # 缓存 1 天
        return img_response
    else:
        return HttpResponse("获取图片失败", status=response.status_code)


class MovieModelViewSet(ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieModelSerializer
    filter_backends = [SearchFilter]
    search_fields = ["type"]

    def get_queryset(self):
        """
        给对应分类返回对应电影数据
        """
        queryset = super().get_queryset()
        category = self.request.query_params.get("category", None)

        if category:
            if category == "other":
                exclude_types = ["喜剧", "动作", "剧情"]
                for exclude_type in exclude_types:
                    queryset = queryset.exclude(type__contains=exclude_type)
            else:
                chinese_category = CATEGORY_MAPPING.get(category)
                if chinese_category:
                    queryset = queryset.filter(type__contains=chinese_category)

        return queryset


class MovieRankingView(generics.ListAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieModelSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['score', 'release_time']
    ordering = ['-score']  # 默认按评分降序

    def get_queryset(self):
        # 将无评分的电影放在最后
        queryset = super().get_queryset()
        return queryset.order_by('-score', 'id').annotate(
            has_score=Case(
                When(score__isnull=True, then=Value(0)),
                default=Value(1),
                output_field=FloatField()
            )
        ).order_by('-has_score', '-score')


class UserRegisterView(generics.CreateAPIView):
    serializer_class = UserModelSerializer

    def create(self, request, *args, **kwargs):
        """用户注册"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "用户注册成功", "username": serializer.data['username']},
                            status=status.HTTP_201_CREATED)
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    def post(self, request):  # noqa
        """用户登录"""
        serializer = UserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        username_or_email = serializer.validated_data.get('username') or serializer.validated_data.get('email')
        password = serializer.validated_data['password']

        user = authenticate(username=username_or_email, password=password)
        if user is None and '@' in username_or_email:
            try:
                user = User.objects.get(email=username_or_email)
                user = authenticate(username=user.username, password=password)
            except User.DoesNotExist:
                return Response({"error": "该邮箱未注册！"}, status=status.HTTP_400_BAD_REQUEST)

        if user is not None:
            tokens = get_tokens_for_user(user)
            return Response({"access": tokens["access"],
                             "refresh": tokens["refresh"],
                             "username": user.username}, status=status.HTTP_200_OK)
        return Response({"error": "用户名/邮箱或密码错误！"}, status=status.HTTP_400_BAD_REQUEST)


class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):  # noqa
        """用户注销"""
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': '注销成功！'}, status=status.HTTP_204_NO_CONTENT)
        except KeyError:
            return Response({'error': '缺少 refresh 字段'}, status=status.HTTP_400_BAD_REQUEST)
        except TokenError as e:
            return Response({'error': f'令牌无效: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):  # noqa
        """获取用户个人信息"""
        # 实例化序列化器时传递request对象，是为了可以在序列化器中通过request.build_absolute_uri()来构建用户头像的绝对url
        serializer = UserProfileSerializer(instance=request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):  # noqa
        """修改用户个人信息"""
        serializer = UserProfileSerializer(instance=request.user, data=request.data, partial=True,
                                           context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UserAvatarUploadView(APIView):
    parser_classes = [MultiPartParser]  # 支持文件上传
    permission_classes = [IsAuthenticated]

    def patch(self, request):  # noqa
        """修改用户头像"""
        serializer = UserAvatarUploadSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response({'avatar_url': request.user.avatar.url})
        return Response(
            {'error': serializer.errors.get('avatar', ['未知错误'])[0]},
            status=status.HTTP_400_BAD_REQUEST
        )


class UserPasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):  # noqa
        """修改用户密码"""
        serializer = UserPasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            RefreshToken.for_user(request.user).blacklist()  # 使当前用户的所有现有token失效
            return Response({'detail': '密码修改成功！'}, status=status.HTTP_200_OK)

        # 统一错误格式
        errors = serializer.errors
        if 'old_password' in errors:
            return Response({'detail': errors['old_password'][0]}, status=status.HTTP_400_BAD_REQUEST)
        elif 'new_password' in errors:
            return Response({'detail': errors['new_password'][0]}, status=status.HTTP_400_BAD_REQUEST)
        elif 'confirm_password' in errors:
            return Response({'detail': errors['confirm_password'][0]}, status=status.HTTP_400_BAD_REQUEST)
        elif 'non_field_errors' in errors:
            return Response({'detail': errors['non_field_errors'][0]}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': '密码修改失败'}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    def post(self, request):  # noqa
        """密码重置请求"""
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            redis_client = get_redis_instance()
            # 检查发送频率限制
            last_sent = redis_client.get(f"reset_cooldown:{email}")
            if last_sent and (timezone.now().timestamp() - float(last_sent)) < 60:
                return Response(
                    {'error': '请等待60秒后再试'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            # 生成6位随机验证码
            verification_code = str(random.randint(100000, 999999))

            # 存储到 Redis，设置5分钟过期
            redis_client.setex(f"reset_code:{email}", 300, verification_code)  # 300秒=5分钟
            redis_client.setex(f"reset_timestamp:{email}", 300, timezone.now().timestamp())
            redis_client.setex(f"reset_cooldown:{email}", 60, str(timezone.now().timestamp()))  # 设置60秒冷却
            # 发送邮件验证码
            subject = '密码重置验证码'
            message = f'您的密码重置验证码是: {verification_code},有效期为5分钟,请尽快验证!'
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False
            )

            return Response({
                'message': '验证码已发送',
                'code_expiry': str(timedelta(minutes=5))
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    def post(self, request):  # noqa
        """密码重置确认"""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            new_password = serializer.validated_data['new_password']

            # 更新用户密码
            User = get_user_model()
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()

            # 清理 Redis 中的验证码
            redis_client = get_redis_instance()
            redis_client.delete(f"reset_code:{email}")
            redis_client.delete(f"reset_timestamp:{email}")

            return Response({'message': '密码重置成功'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserRatingView(APIView):
    """获取或设置当前用户对特定电影的评分"""
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id):  # noqa
        """获取当前用户对电影的评分"""
        rating = Rating.objects.filter(
            movie_id=movie_id,
            user=request.user
        ).first()

        if rating:
            serializer = RatingSerializer(rating)
            return Response(serializer.data)
        return Response({'id': None, 'rating': 0}, status=status.HTTP_200_OK)

    def post(self, request, movie_id):  # noqa
        """当前用户对电影创建或更新评分"""
        rating, created = Rating.objects.update_or_create(
            user=request.user,
            movie_id=movie_id,
            defaults={'rating': request.data.get('rating')}
        )
        serializer = RatingSerializer(rating)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class UserRatingListCreateView(generics.ListCreateAPIView):
    """暂时保留，用于后续实现‘我评分过的电影’"""

    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """当前用户对相关电影的评分"""
        return Rating.objects.filter(user=self.request.user).select_related('movie')

    def perform_create(self, serializer):
        """将评分与当前用户相关联"""
        serializer.save(user=self.request.user)


class MovieRatingListView(generics.ListAPIView):
    """暂时保留，用于后续实现‘最新评分展示’"""

    serializer_class = RatingSerializer

    def get_queryset(self):
        """所有用户对该电影的评分"""
        movie_id = self.kwargs['movie_id']
        return (
            Rating.objects
            .filter(movie_id=movie_id)
            .select_related('user')
            .order_by('-rating_time')  # 按评分时间倒排
        )


class MovieRatingStatsView(APIView):
    """电影评分统计"""

    def get(self, request, movie_id):  # noqa
        """向下取整(1位小数)计算平均分"""
        stats = Rating.objects.filter(movie_id=movie_id).aggregate(
            avg_rating=Avg('rating'),
            rating_count=Count('rating')
        )
        return Response({
            'avg_rating': round(stats['avg_rating'], 1) if stats['avg_rating'] else None,
            'rating_count': stats['rating_count']
        })


class UserCommentListCreateView(generics.ListCreateAPIView):
    """当前用户评论创建和列表"""
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()  # 获取默认上下文(含request)
        context['request'] = self.request  # 显式覆盖
        return context

    def get_queryset(self):
        return Comments.objects.filter(user=self.request.user).select_related('movie', 'user')  # 返回当前用户的所有评论

    def perform_create(self, serializer):
        movie_id = self.request.data.get('movie')  # 从请求数据中获取movie_id
        movie = get_object_or_404(Movie, pk=movie_id)  # 根据movie_id获取Movie对象
        # 将评论与当前用户和电影关联
        serializer.save(
            user=self.request.user,  # 通过request获取当前用户
            movie=movie
        )


class CommentDeleteView(generics.DestroyAPIView):
    """删除当前用户评论"""
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        return Comments.objects.filter(user=self.request.user)


class CommentReplyView(generics.CreateAPIView):
    """创建回复评论"""
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        parent_comment = get_object_or_404(Comments, pk=self.kwargs['pk'])  # 通过路径参数获取父级评论
        serializer.save(
            user=self.request.user,
            movie_id=parent_comment.movie.id,
            comment=serializer.validated_data['comment'],
            parent_comment=parent_comment
        )


class MovieCommentListView(generics.ListAPIView):
    """所有用户对该电影的评论列表"""
    serializer_class = CommentSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        return Comments.objects.filter(
            movie_id=self.kwargs['movie_id'],
            parent_comment__isnull=True  # 先筛选出顶级评论
        ).select_related(  # 关联预加载：外键字段和一对一字段
            'user', 'movie', 'parent_comment__user'
        ).prefetch_related(  # 关联预加载：多对多字段和反向外键关系
            'replies__user'
        ).order_by('comment_time')


class MovieRecommendationView(APIView):
    """电影推荐"""
    permission_classes = []

    def get(self, request):
        if request.user.is_authenticated:
            user = request.user

            # 检查用户是否有评分记录
            user_ratings = Rating.objects.filter(user=user).exists()

            if user_ratings:
                # 有评分记录 : 基于用户评分推荐
                recommended_movies = self.get_recommendations_based_on_ratings(user)
            else:
                # 无评分记录 : 推荐各分类高分电影
                recommended_movies = self.get_top_rated_by_category()

            serializer = MovieModelSerializer(recommended_movies, many=True)
            return Response(serializer.data)
        else:
            recommended_movies = self.get_anonymous_recommendations()
            serializer = MovieModelSerializer(recommended_movies, many=True)
            return Response({
                'movies': serializer.data,
                'is_anonymous': True,
                'message': '登录后可获得个性化推荐'
            })

    def get_recommendations_based_on_ratings(self, user):  # noqa
        """基于用户评分推荐电影"""
        # 获取用户评分过的电影类型
        rated_types = Rating.objects.filter(
            user=user
        ).values_list('movie__type', flat=True).distinct()  # flat=True表示返回单值列表,不设置默认返回元组列表

        # 获取这些类型中评分高的电影(排除用户已评分的)
        recommended = Movie.objects.filter(
            type__in=rated_types
        ).exclude(
            rating__user=user
        ).order_by('-score')[:10]

        return recommended

    def get_top_rated_by_category(self):  # noqa
        """推荐各分类高分电影"""
        # 获取所有电影类型
        movie_types = Movie.objects.values_list('type', flat=True).distinct()

        recommended_movies = []

        for movie_type in movie_types:
            # 获取该类型评分最高的2部电影
            top_movies = Movie.objects.filter(
                type=movie_type
            ).order_by('-score')[:2]

            recommended_movies.extend(top_movies)

            # 如果已经收集到10部，提前结束
            if len(recommended_movies) >= 10:
                break

        return recommended_movies[:10]

    def get_anonymous_recommendations(self):
        """为匿名用户生成推荐"""
        return self.get_top_rated_by_category()
