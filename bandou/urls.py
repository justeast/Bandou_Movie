from rest_framework.routers import DefaultRouter
from bandou.views import MovieModelViewSet, AdminMovieViewSet

router = DefaultRouter()
router.register("movies", MovieModelViewSet, "movies")
router.register("admin/movies", AdminMovieViewSet, "admin-movies")  # 后台电影管理

urlpatterns = []
urlpatterns += router.urls
