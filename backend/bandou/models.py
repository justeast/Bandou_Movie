from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    用户表
    """
    phone = models.CharField(
        max_length=11,
        blank=True,
        verbose_name="手机号"
    )

    # ImageField继承自FileField,FileField有url属性
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        verbose_name="头像"
    )
    email = models.EmailField(unique=True, blank=False, verbose_name="邮箱")

    def __str__(self):
        return self.username

    class Meta:
        db_table = "user"
        verbose_name = "用户信息"
        verbose_name_plural = verbose_name


class LoginRecord(models.Model):
    """
    用户登录记录表
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户", related_name="login_records")
    login_time = models.DateTimeField(verbose_name="登录时间", auto_now_add=True)
    login_ip = models.GenericIPAddressField(verbose_name="登录IP", blank=True, null=True)

    class Meta:
        db_table = "login_record"
        verbose_name = "登录记录"
        verbose_name_plural = verbose_name
        ordering = ['-login_time']

    def __str__(self):
        formatted_time = self.login_time.strftime("%Y-%m-%d %H:%M:%S")
        return f"{self.user.username} - {formatted_time} - {self.login_ip}"


class Movie(models.Model):
    """
    电影表
    """
    title = models.CharField(verbose_name="片名", max_length=128)
    brief_introduction = models.CharField(verbose_name="简介", max_length=512)
    cover_url = models.CharField(verbose_name="封面url", max_length=255)
    score = models.FloatField(verbose_name="评分", null=True, blank=True)  # 这是综合了每个user的对该movie的综合评分
    release_time = models.DateField(verbose_name="上映时间")
    director = models.CharField(verbose_name="导演", max_length=32)
    starring = models.CharField(verbose_name="主演", max_length=255)
    type = models.CharField(verbose_name="电影类别", max_length=32)

    def __str__(self):
        return self.title

    class Meta:
        db_table = "movie"
        verbose_name = "电影信息"
        verbose_name_plural = verbose_name


class Rating(models.Model):
    """
    评分表
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, verbose_name="电影")
    rating = models.FloatField(verbose_name="评分", default=5)  # 这是相关user对所对应movie的个性化主观评分
    rating_time = models.DateTimeField(verbose_name="评分时间", auto_now=True)

    class Meta:
        unique_together = ['user', 'movie']
        db_table = "rating"
        verbose_name = "评分信息"
        verbose_name_plural = verbose_name


class Comments(models.Model):
    """
    评论表
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, verbose_name="电影")
    comment = models.TextField(verbose_name="评论")
    comment_time = models.DateTimeField(verbose_name="评论时间")
    # 父评论，通过related_name实现双向关联
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                                       verbose_name="父评论", related_name='replies')

    class Meta:
        db_table = "comments"
        verbose_name = "评论信息"
        verbose_name_plural = verbose_name
