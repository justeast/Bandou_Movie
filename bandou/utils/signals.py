from django.db.models import Avg
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from bandou.models import Rating


@receiver([post_save, post_delete], sender=Rating)
def update_movie_score(sender, instance, **kwargs):
    """
    当评分创建、更新或删除时，自动更新对应电影的 score 字段
    """
    movie = instance.movie

    # 计算最新平均分
    avg_rating = Rating.objects.filter(
        movie=movie
    ).aggregate(avg=Avg('rating'))['avg']

    # 更新 score 字段
    movie.score = round(avg_rating, 1) if avg_rating else None
    movie.save(update_fields=['score'])
