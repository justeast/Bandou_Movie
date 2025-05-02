"""
URL configuration for BanDou_Movie project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from bandou.views import proxy_bouban_movie_image, UserRegisterView, UserLoginView, UserLogoutView, UserProfileView, \
    UserAvatarUploadView, UserPasswordChangeView, MovieRankingView, UserRatingListCreateView, \
    MovieRatingListView, MovieRatingStatsView, UserCommentListCreateView, MovieCommentListView, \
    CurrentUserRatingView, CommentDeleteView, CommentReplyView, MovieRecommendationView

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
                  path("admin/", admin.site.urls),  # 超级管理员
                  path("proxy_image/", proxy_bouban_movie_image),  # 获取电影图片
                  path("bandou/", include("bandou.urls")),  # 电影增删改查
                  path("movies/ranking/", MovieRankingView.as_view()),  # 电影榜单
                  path("api/user/register/", UserRegisterView.as_view()),  # 用户注册
                  path("api/user/login/", UserLoginView.as_view()),  # 用户登录
                  path("api/user/logout/", UserLogoutView.as_view()),  # 用户注销
                  path("api/user/profile/", UserProfileView.as_view()),  # 用户个人中心
                  path("api/user/avatar/", UserAvatarUploadView.as_view()),  # 用户头像上传
                  path("api/user/change_password/", UserPasswordChangeView.as_view()),  # 用户修改密码
                  path('api/token/', TokenObtainPairView.as_view()),  # 用户认证
                  path('api/token/refresh/', TokenRefreshView.as_view()),  # 用户认证
                  path('api/user/ratings/', UserRatingListCreateView.as_view()),  # todo："我评分过的电影"
                  path('api/movies/<int:movie_id>/my_rating/', CurrentUserRatingView.as_view(), ),  # 用户对电影评分
                  path('api/movies/<int:movie_id>/ratings/', MovieRatingListView.as_view()),  # todo:"最新评分"
                  path('api/movies/<int:movie_id>/rating_stats/', MovieRatingStatsView.as_view()),  # 电影评分统计
                  path('api/user/comments/', UserCommentListCreateView.as_view()),  # 用户对电影评论
                  path('api/comments/<int:pk>/', CommentDeleteView.as_view()),  # 用户评论删除
                  path('api/comments/<int:pk>/reply/', CommentReplyView.as_view()),  # 评论回复
                  path('api/movies/<int:movie_id>/comments/', MovieCommentListView.as_view()),  # 对应电影的评论列表
                  path('api/movies/recommend/', MovieRecommendationView.as_view()),  # 电影推荐
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
