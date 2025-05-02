import requests
from lxml import etree
from datetime import datetime
import os
import django

# 配置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BanDou_Movie.settings')
django.setup()
from bandou.models import Movie


def fetch_movies():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0",
        "Cookie": 'bid=qbLX4HJaR2A; ll="118305"; _ck_desktop_mode=1; vmode=pc; ap_v=0,6.0; dbcl2="261504977:vQArx6oV4S4"; ck=4InB; push_noty_num=0; push_doumail_num=0',
        "Referer": "https://movie.douban.com/cinema/nowplaying/wuzhou/"
    }
    movie_html_url = "https://movie.douban.com/cinema/nowplaying/shenzhen/"
    movie_resp = requests.get(movie_html_url, headers=headers)
    movie_et = etree.HTML(movie_resp.text)
    # 获取每个电影详情页的url
    movies_detail_url_list = movie_et.xpath("//li[@class='poster']/a[@class='ticket-btn']/@href")

    for movie_detail_url in movies_detail_url_list:
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
            starring.append("无")
        else:
            starred_actors = " / ".join(starring)
            if len(starred_actors) > 255:
                print(f"跳过电影《{''.join(title)}》：主演信息过长")
                continue
            starring = starred_actors

        if score:
            score = float("".join(score))
        else:
            score = None

        brief_introduction = "".join(brief_introduction).strip().replace('\n', '').replace(' ', '').replace('<br/>',
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


if __name__ == '__main__':
    fetch_movies()
