# encoding=utf8

"""
根据小说名和作者名获取对应小说的发表平台
"""

import re
import time
import urllib
import requests


def download(url):
    """
    下载器
    """
    headers = {
        'Host': 'baike.baidu.com', 'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'
    }
    resp = None
    html = None

    if 'baike.baidu.com/error.html' in url:
        print 'error url: %s' % url
        return resp, html

    try:
        resp = requests.get(url, headers=headers, allow_redirects=False, timeout=10)
        html = resp.content
        html = html.replace('&nbsp;', '')
    except Exception as e:
        print '----- download error: %s, url: %s' % (e, url)
        time.sleep(2)
    return resp, html


def check_location(resp, ourl):
    """
    处理跳转链接
    """
    location = resp.headers['Location']
    html = None
    url = ''
    if location:
        url = 'https://baike.baidu.com' + location
        resp, html = download(url)
    else:
        print 'no location, ourl: %s' % ourl

    return resp, html, url


def find_author(html):
    """
    获取作者名
    """
    author_name = '<dt class="basicInfo-item name">.*?作者</dt>\s+<dd class="basicInfo-item value">(.*?)</dd>'
    author_name = re.search(author_name, html, re.S)
    author_name = author_name.group(1) if author_name else ''
    author_name = author_name.strip()
    return author_name


def work(name, author):
    name = re.sub('(【.*?】|（.*?）|「.*?」|\(.*?\))', '', name)
    name = name.strip()

    url = 'https://baike.baidu.com/item/%s' % urllib.quote(name)
    ourl = url
    pingtai = ''
    print 'ourl: ', ourl

    resp, html = download(url)
    if not resp:
        print 'no resp1, url: %s' % url
        return pingtai, url

    if resp.status_code == 302:
        time.sleep(1)
        resp, html, url = check_location(resp, url)

    if not resp:
        print 'no resp2, url: %s' % url
        return pingtai, url

    # 有可能会多跳转一次：https://baike.baidu.com/item/%E8%AF%9B%E4%BB%992
    if resp.status_code == 302:
        time.sleep(1)
        resp, html, url = check_location(resp, url)

    if not html:
        print 'html error1, url: %s' % url
        return pingtai, url

    author_name = find_author(html)
    new_url = ''
    if author not in author_name:
        print 'no author_name, url: %s' % url
        # 该小说名可能有多个义词:千山暮雪
        force_url = 'https://baike.baidu.com/item/%s?force=1' % urllib.quote(name)
        resp, html = download(force_url)
        if not resp:
            print 'no force html, url: %s' % ourl
            return pingtai, url
        more = re.findall('(<a target=.*?data-lemmaid=.*?</a>)', html, re.S)
        for m in more:
            if '小说' not in m:
                continue
            # 小说作者会出现在词条介绍中
            if author in m:
                aid = re.search('data-lemmaid="(\d+)"', m)
                aid = aid.group(1) if aid else ''
                if aid:
                    new_url = ourl + '/' + aid
                    break
    if new_url:
        url = new_url
        resp, html = download(url)

    if not html:
        print 'html error2, url: %s' % url
        return pingtai, url

    pattern = '<dt class="basicInfo-item name">[连载平台|首发网站]+</dt>\s+<dd class="basicInfo-item value">(.*?)</dd>'
    pingtai = re.search(pattern, html, re.S)
    pingtai = pingtai.group(1) if pingtai else ''
    pingtai = pingtai.strip()
    if '<a' in pingtai:
        pingtais = re.findall('<a[^>]*>(.*?)</a>', pingtai, re.S)
        pingtai = ','.join(pingtais)

    return pingtai, url


def main():
    name = '尊上'
    author = '九哼'
    work(name, author)


if __name__ == '__main__':
    main()
