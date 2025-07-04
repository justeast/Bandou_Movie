import urllib.parse
from datetime import timedelta
import requests
import random
import logging

logger = logging.getLogger(__name__)  # 获取日志记录器

from django.db import transaction
from django.http import HttpResponse
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from django.db.models import Value, Case, When, FloatField, Avg, Count, Q
from django.core.files.storage import default_storage
from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth import get_user_model
from bandou.utils.get_redis_instance import get_redis_instance
from bandou.utils.user_auth import get_tokens_for_user
from bandou.models import Movie, Rating, Comments, User, LoginRecord
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


class MovieSearchView(generics.ListAPIView):
    """电影搜索"""
    serializer_class = MovieModelSerializer

    def get_queryset(self):
        queryset = Movie.objects.all()
        keyword = self.request.query_params.get('keyword', None)

        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword) |
                Q(brief_introduction__icontains=keyword) |
                Q(director__icontains=keyword) |
                Q(starring__icontains=keyword) |
                Q(type__icontains=keyword)
            )

        # 按评分排序
        return queryset.order_by('-score')


class MovieRankingView(generics.ListAPIView):
    """电影榜单"""
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

        # 首先尝试直接通过用户名查找用户（不使用authenticate，因为对于被封禁的用户，authenticate会直接返回None）
        try:
            user = User.objects.get(username=username_or_email)
        except User.DoesNotExist:
            # 如果不存在，尝试通过邮箱查找
            if '@' in username_or_email:
                try:
                    user = User.objects.get(email=username_or_email)
                except User.DoesNotExist:
                    return Response({"error": "该邮箱未注册！"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error": "用户名不存在！"}, status=status.HTTP_400_BAD_REQUEST)

        # 检查用户是否被封禁
        if not user.is_active:
            return Response({"error": "该账号已被封禁，请联系管理员！"}, status=status.HTTP_403_FORBIDDEN)

        # 检查密码是否正确
        if not user.check_password(password):
            return Response({"error": "密码错误！"}, status=status.HTTP_400_BAD_REQUEST)

        # 手动更新用户的上次登录时间
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        # 记录用户登录信息
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        LoginRecord.objects.create(
            user=user,
            login_ip=ip,
        )

        tokens = get_tokens_for_user(user)
        return Response({"access": tokens["access"],
                         "refresh": tokens["refresh"],
                         "username": user.username}, status=status.HTTP_200_OK)


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


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class AdminMovieViewSet(ModelViewSet):
    """
    后台电影管理视图集
    提供对电影的增删改查和数据统计
    """
    queryset = Movie.objects.all()
    serializer_class = MovieModelSerializer
    permission_classes = [IsAdminUser]  # 限制只有管理员才能访问
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # 支持表单和文件上传
    pagination_class = StandardResultsSetPagination

    # 过滤、搜索、排序
    filter_backends = [SearchFilter]
    search_fields = ["title", "director", "type", "starring"]
    ordering_fields = ["id", "score", "release_time"]
    ordering = ['id']

    def get_queryset(self):
        """
        重写 get_queryset 方法，添加评分和上映日期过滤
        根据请求的查询参数判断使用哪种过滤方式
        """
        queryset = Movie.objects.all()

        # 默认排序字段
        ordering_field = 'id'

        # 检查是否有评分过滤
        has_rating_filter = False

        # 评分过滤
        min_score = self.request.query_params.get('min_score')
        max_score = self.request.query_params.get('max_score')
        no_rating = self.request.query_params.get('no_rating')

        # 3分以上、4分以上
        if min_score:
            try:
                min_score = float(min_score)
                queryset = queryset.filter(score__gte=min_score)
                has_rating_filter = True
            except (ValueError, TypeError) as e:
                logger.warning(f"最小评分过滤参数无效: {min_score}, 错误: {str(e)}")

        # 3分以下
        if max_score:
            try:
                max_score = float(max_score)
                queryset = queryset.filter(score__lt=max_score)
                has_rating_filter = True
            except (ValueError, TypeError) as e:
                logger.warning(f"最大评分过滤参数无效: {max_score}, 错误: {str(e)}")

        # 无评分和0分
        if no_rating and no_rating.lower() == 'true':
            queryset = queryset.filter(Q(score__isnull=True) | Q(score=0))

        # 如果有评分过滤，按评分降序排列
        if has_rating_filter:
            ordering_field = '-score'

        # 上映日期过滤
        release_date_start = self.request.query_params.get('release_date_start')
        release_date_end = self.request.query_params.get('release_date_end')
        filter_type = self.request.query_params.get('filter_type')

        if release_date_start:
            try:
                queryset = queryset.filter(release_time__gte=release_date_start)
            except (ValueError, TypeError) as e:
                logger.warning(f"开始日期过滤参数无效: {release_date_start}, 错误: {str(e)}")

        if release_date_end:
            try:
                queryset = queryset.filter(release_time__lte=release_date_end)
            except (ValueError, TypeError) as e:
                logger.warning(f"结束日期过滤参数无效: {release_date_end}, 错误: {str(e)}")

        # 最近上映则按上映日期降序(最新的在前)
        if filter_type == 'recent_release':
            ordering_field = '-release_time'

        request_ordering = self.request.query_params.get('ordering')
        if request_ordering:  # 若用户在请求中明确指定了排序字段
            return queryset.order_by(request_ordering)
        else:
            return queryset.order_by(ordering_field)

    def _delete_cover_file(self, cover_url):  # noqa
        """从OSS中删除封面文件"""
        if not cover_url:
            return

        # 初始化path变量，避免未定义警告
        path = None

        try:
            # 从URL中提取文件路径
            # 实际OSS URL格式: https://bandou-movie.oss-cn-guangzhou.aliyuncs.com/media/covers/movie_122_1747822938.png
            parsed_url = urllib.parse.urlparse(cover_url)
            path = parsed_url.path
            if path.startswith('/media/'):
                alt_path = path[7:]  # 去掉'/media/'
                default_storage.delete(alt_path)
                logger.info(f"已从OSS删除文件: {alt_path}")
        except Exception as e:
            logger.error(f"删除OSS文件失败: {cover_url}, 路径: {path}, 错误: {str(e)}")

    def perform_destroy(self, instance):
        """
        重写删除方法，确保在删除电影记录时也删除相关的封面文件
        """
        # 保存封面URL
        cover_url = instance.cover_url

        # 删除数据库记录
        instance.delete()

        # 删除封面文件
        self._delete_cover_file(cover_url)

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """批量删除电影"""
        ids = request.data.get('ids', [])
        if not ids:
            return Response({"error": "未提供要删除的电影ID"}, status=status.HTTP_400_BAD_REQUEST)

        # 获取要删除的电影记录
        movies_to_delete = Movie.objects.filter(id__in=ids)

        # 收集所有要删除的封面URL
        cover_urls = [movie.cover_url for movie in movies_to_delete if movie.cover_url]

        # 删除数据库记录
        with transaction.atomic():
            deleted_count, _ = movies_to_delete.delete()

        # 删除封面文件
        for url in cover_urls:
            self._delete_cover_file(url)

        return Response({"message": f"成功删除{deleted_count}部电影"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def category_stats(self, request):
        """获取各分类电影数量统计"""
        stats = Movie.objects.values('type').annotate(count=Count('id')).order_by('-count')

        # 处理多类型电影（如"动作/喜剧"）
        categories = {}
        for item in stats:
            movie_type = item['type']
            count = item['count']

            # 处理包含多个类型的情况
            if '/' in movie_type:
                types = movie_type.split('/')
                for t in types:
                    t = t.strip()
                    if t in categories:
                        categories[t] += count
                    else:
                        categories[t] = count
            else:
                if movie_type in categories:
                    categories[movie_type] += count
                else:
                    categories[movie_type] = count

        # 转换为字典列表给前端
        result = [{"category": k, "count": v} for k, v in categories.items()]
        return Response(result)

    @action(detail=False, methods=['get'])
    def rating_distribution(self, request):
        """各分类电影不同分数段占比"""
        ranges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]
        result = []
        categories = set()

        # 获取所有电影类型
        for movie in Movie.objects.all():
            if '/' in movie.type:
                for t in movie.type.split('/'):
                    categories.add(t.strip())
            else:
                categories.add(movie.type)

        for category in categories:
            distribution = []
            movie_ids = set()
            # 获取包含该类型的电影 ID
            for movie in Movie.objects.all():
                if '/' in movie.type:
                    types = [t.strip() for t in movie.type.split('/')]
                    if category in types:
                        movie_ids.add(movie.id)
                elif movie.type == category:
                    movie_ids.add(movie.id)

            rated_count = 0

            # 按评分分段统计
            for start, end in ranges:
                count = Movie.objects.filter(id__in=movie_ids, score__gte=start, score__lt=end).count()
                distribution.append({
                    "range": f"{start}-{end}",
                    "count": count
                })
                rated_count += count

            # 添加无评分分段
            unrated_count = Movie.objects.filter(id__in=movie_ids, score__isnull=True).count()
            distribution.append({
                "range": "无评分",
                "count": unrated_count
            })

            # 返回各个电影分类中各个分数段的电影数量，占比计算由前端完成
            result.append({
                "category": category,
                "distribution": distribution
            })

        return Response(result)

    @action(detail=True, methods=['get'])
    def rating_trend(self, request, pk=None):
        """获取特定电影的评分趋势"""
        movie = self.get_object()

        # 获取最近7天每天的平均评分
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)

        # 按日期分组获取评分
        daily_ratings = Rating.objects.filter(
            movie=movie,
            rating_time__gte=start_date,
            rating_time__lte=end_date
        ).extra(
            select={'date': "DATE(rating_time)"}  # 提取评分时间的日期部分
        ).values('date').annotate(avg_rating=Avg('rating')).order_by('date')

        # 将查询结果转换为字典(将日期对象转换为字符串格式（'YYYY-MM-DD'）作为字典的键,将平均评分转换为浮点数作为字典的值)
        ratings_dict = {
            item['date'].strftime('%Y-%m-%d'): float(item['avg_rating'])
            for item in daily_ratings
        }

        # 生成完整的7天日期序列
        complete_trend_data = []
        current_date = start_date.date()
        end_date_only = end_date.date()

        # 获取默认评分值 - 使用None表示暂无评分，区别于0分
        default_rating = None

        # 检查电影是否有评分（不管是最近7天内还是历史评分）
        has_any_rating = False

        # 先检查电影对象的score
        if movie.score is not None:
            default_rating = float(movie.score)
            has_any_rating = True
        else:
            # 检查最近7天内的评分
            if ratings_dict:
                has_any_rating = True
                sorted_dates = sorted(ratings_dict.keys())
                default_rating = ratings_dict[sorted_dates[0]]
            else:
                # 检查历史评分
                latest_rating = Rating.objects.filter(movie=movie).order_by('-rating_time').first()
                if latest_rating:
                    has_any_rating = True
                    default_rating = float(Rating.objects.filter(
                        movie=movie,
                        rating_time__date=latest_rating.rating_time.date()
                    ).aggregate(Avg('rating'))['rating__avg'])

        # 填充每一天的数据，从最早日期开始
        last_rating = default_rating
        dates_to_process = []

        # 先收集所有需要处理的日期
        while current_date <= end_date_only:
            dates_to_process.append(current_date)
            current_date += timedelta(days=1)

        # 如果电影完全没有任何评分记录，返回全部为null的数据
        if not has_any_rating:
            for date in dates_to_process:
                date_str = date.strftime('%Y-%m-%d')
                complete_trend_data.append({
                    "date": date_str,
                    "avg_rating": None  # 使用None表示暂无评分
                })
            return Response(complete_trend_data)

        # 从第一天到倒数第二天，按时间顺序填充
        for i in range(len(dates_to_process) - 1):
            current_date = dates_to_process[i]
            date_str = current_date.strftime('%Y-%m-%d')

            if date_str in ratings_dict:
                current_rating = ratings_dict[date_str]
                last_rating = current_rating
            else:
                current_rating = last_rating

            complete_trend_data.append({
                "date": date_str,
                "avg_rating": current_rating
            })

        # 最后一天（最新日期）特殊处理，使用电影的当前score
        if dates_to_process:
            last_date = dates_to_process[-1]
            last_date_str = last_date.strftime('%Y-%m-%d')

            # 优先使用电影当前评分作为最新日期的评分
            if movie.score is not None:
                last_date_rating = float(movie.score)
            # 如果当天有评分数据，使用当天的评分
            elif last_date_str in ratings_dict:
                last_date_rating = ratings_dict[last_date_str]
            # 否则使用前一天的评分
            else:
                last_date_rating = last_rating

            complete_trend_data.append({
                "date": last_date_str,
                "avg_rating": last_date_rating
            })

        return Response(complete_trend_data)

    @action(detail=False, methods=['get'])
    def movie_types(self, request):
        """获取所有唯一的电影类型列表"""
        # 获取所有电影类型
        all_types = set()

        # 遍历所有电影，提取并分割类型
        for movie in Movie.objects.all():
            if not movie.type:
                continue

            if '/' in movie.type:
                for t in movie.type.split('/'):
                    t = t.strip()
                    if t:
                        all_types.add(t)
            else:
                if movie.type.strip():
                    all_types.add(movie.type.strip())

        # 默认按字母顺序排序
        sorted_types = sorted(all_types)

        return Response(sorted_types)
