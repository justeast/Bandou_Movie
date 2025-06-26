import time

import requests
import random
from lxml import etree
from datetime import datetime
import os
import django

import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from apscheduler.schedulers.blocking import BlockingScheduler

# 配置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BanDou_Movie.settings')
django.setup()
from bandou.models import Movie

# User-Agent列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 OPR/119.0.0.0",
]

# ip代理列表
PROXY_POOL = [
    "http://36.6.145.114:8089",
    "http://223.215.176.114:8089",
    "http://114.231.42.92:8089",
    "http://117.69.237.102:8089",
    "http://114.232.110.101:8089",
    "http://39.108.82.243:808",
    "http://182.34.20.41:9999",
]

# 城市列表，轮换抓取不同城市的电影信息，降低单一URL的请求频率
CITIES = [
    "shenzhen", "guangzhou", "beijing", "shanghai", "hangzhou",
    "nanjing", "chengdu", "wuhan", "xian", "chongqing"
]


def fetch_movies():
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Cookie": 'bid=qbLX4HJaR2A; ll="118305"; push_noty_num=0; push_doumail_num=0; dbcl2="261504977:WbuJe+GqX+E"; ck=ZFwx; _ck_desktop_mode=1; vmode=pc; frodotk_db="9ae4195bca28ca43d0ac4c135e7a5ec9"',
        "Referer": "https://movie.douban.com/"
    }
    movie_html_url = f"https://movie.douban.com/cinema/nowplaying/{random.choice(CITIES)}/"
    flag = False  # 是否需要进行人机验证
    try:
        movie_resp = requests.get(movie_html_url, headers=headers, proxies={"http": random.choice(PROXY_POOL)})

        # 需要进行人机验证时进行提示
        if "证明你是人类" in movie_resp.text:
            input("请手动前往网页进行验证后回车继续...")  # 输入阻塞，等待人工验证
            flag = True

        # 若进行了人机验证，则重新请求
        if flag:
            movie_resp = requests.get(movie_html_url, headers=headers, proxies={"http": random.choice(PROXY_POOL)})

        movie_et = etree.HTML(movie_resp.text)
        # print(movie_resp.text)
        # 获取每个电影详情页的url
        movies_detail_url_list = movie_et.xpath("//li[@class='poster']/a[@class='ticket-btn']/@href")

        logger.info(f"找到 {len(movies_detail_url_list)} 部电影，开始抓取...")

        for movie_detail_url in movies_detail_url_list:
            title = "未知电影"  # 初始化title，防止异常处理中引用未定义变量
            try:
                time.sleep(random.uniform(1, 3))  # 随机延时，避免请求过于频繁

                movie_detail_resp = requests.get(movie_detail_url, headers=headers)
                movie_detail_et = etree.HTML(movie_detail_resp.text)
                # html页面提取对应数据
                title = movie_detail_et.xpath("//span[@property='v:itemreviewed']/text()")
                cover_url = movie_detail_et.xpath("//img[@rel='v:image']/@src")
                score = movie_detail_et.xpath("//strong[@property='v:average']/text()")
                director = movie_detail_et.xpath("//a[@rel='v:directedBy']/text()")
                starring = movie_detail_et.xpath("//a[@rel='v:starring']/text()")
                type_name = movie_detail_et.xpath("//span[@property='v:genre']/text()")
                release_time = movie_detail_et.xpath("//span[@property='v:initialReleaseDate']/text()")[0]
                brief_introduction = movie_detail_et.xpath("//span[@property='v:summary']/text()")
                # 将提取到的数据列表转为字符串
                type_name = " / ".join(type_name)
                director = "".join(director)
                title = "".join(title)
                cover_url = "".join(cover_url)
                release_time = datetime.fromisoformat(release_time[:10]).date()

                if not starring:
                    starring = "无"
                else:
                    starred_actors = " / ".join(starring)
                    if len(starred_actors) > 255:
                        print(f"跳过电影《{''.join(title)}》：主演信息过长")
                        continue
                    starring = starred_actors

                if score:
                    score = round(float("".join(score)) / 2, 1)
                else:
                    score = None

                brief_introduction = "".join(brief_introduction).strip().replace('\n', '').replace(' ', '').replace(
                    '<br/>',
                    '').replace(
                    '<br />', '')
                # 存入数据库（防止重复存入）
                movie_obj, created = Movie.objects.get_or_create(
                    title=title,
                    defaults={
                        "brief_introduction": brief_introduction,
                        "cover_url": cover_url,
                        "score": score,
                        "release_time": release_time,
                        "director": director,
                        "starring": starring,
                        "type": type_name
                    }
                )
                if created:
                    print(f"电影《{title}》已添加到数据库！")
                else:
                    print(f"电影《{title}》已存在，跳过。")
            except Exception as e:
                logger.error(f"抓取电影《{title}》失败：{str(e)}")
    except Exception as e:
        logger.error(f"抓取电影列表失败：{str(e)}")


def start_scheduler():
    """
    启动定时任务调度器，每天定期执行一次抓取任务
    """
    scheduler = BlockingScheduler()
    scheduler.add_job(fetch_movies, 'cron', hour=6, minute=0, id='movie_spider_job')
    logger.info("定时任务已设置，将在每天早上6:00执行电影数据抓取")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("定时任务已停止")


if __name__ == '__main__':
    #  测试
    # for _ in range(10):
    #     time.sleep(random.uniform(1, 3))
    #     fetch_movies()

    # fetch_movies()  # 立即执行一次抓取

    start_scheduler()
