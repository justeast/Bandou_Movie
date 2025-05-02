from rest_framework.routers import DefaultRouter
from bandou.views import MovieModelViewSet

routers = DefaultRouter()
routers.register("movies", MovieModelViewSet, "movies")

urlpatterns = []
urlpatterns += routers.urls
