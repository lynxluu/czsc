import os
# import io
from datetime import datetime
from lib108 import *

import requests
from bs4 import BeautifulSoup

from docx import Document
from docx.shared import Pt,Cm,Inches
from docx.oxml.ns import qn
from docx.image.image import Image


# import concurrent.futures


# 忽略 SSL 证书警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# 单线程循环, 解析html使用递归，直接写文件
def single_doc():
    target_url = get_abs_url('/stocks/wolves')

    ext = datetime.now().strftime('%y%m%d%H%M%S')
    file_path = os.path.join(f'czsc108a3_{ext}.docx')
    print(file_path)


    # 获取所有相关相对链接
    rel_urls = get_links(target_url)[7:9]

    document = Document()
    set_format(document)

    urls = []
    # 获得绝对链接
    for rel_url in rel_urls:
        url = get_abs_url(rel_url)
        urls.append(url)

        # 获取对应url的内容
        response = get_response(url)

        soup = BeautifulSoup(response.content, 'html.parser')
        article = soup.find('article')
        # content = article.contents

        # 获取标题
        title_tag = article.find('h1')
        title = title_tag.get_text() if title_tag else ''
        document.add_heading(title, level=1)

        # 获取时间
        # time_tag = article.find('blockquote')
        # time_str = time_tag.get_text() if time_tag else ''
        # time = datetime.strptime(time_str, '%Y/%m/%d %H:%M:%S')
        # document.add_paragraph(time_str)

        # 递归遍历所有子标签
        def traverse(tag):
            if tag.name is None:
                return
            for child in tag.children:
                if child.name == 'p':
                    document.add_paragraph(child.text)
                elif child.name == 'img':
                    image_url = get_abs_url(child['src'])
                    image = get_image(image_url)
                    if image:
                        document.add_picture(image, width=Inches(6))

                elif child.name in ['h2', 'h3']:
                    document.add_paragraph('回复')
                elif child.name == 'span':
                    document.add_paragraph(child.text)
                elif child.name =='br':
                    # 杜绝无内容的br占据很大篇幅
                    if child.previous_sibling.name != 'br':
                        document.add_paragraph(child.previous_sibling.text)
                else:
                    traverse(child)

        # 遍历正文
        for tag in article:
            traverse(tag)

    document.save(file_path)


# if __name__ == '__main__':
#     main()
single_doc()

def list_doc():
    target_url = get_abs_url('/stocks/wolves')

    ext = datetime.now().strftime('%y%m%d%H%M%S')
    file_path = os.path.join(f'czsc108a4_{ext}.docx')
    print(file_path)


    # 获取所有相关相对链接
    rel_urls = get_links(target_url)[7:9]

    document = Document()
    set_format(document)

    urls = []
    pages = []
    # 获得绝对链接
    for rel_url in rel_urls:
        url = get_abs_url(rel_url)
        urls.append(url)

        # 获取对应url的内容
        response = get_response(url)

        soup = BeautifulSoup(response.content, 'html.parser')
        article = soup.find('article')
        # content = article.contents
        
        # 查找文章标题和发表时间
        title = article.find('h1').text.strip()
        ptime = article.find('blockquote').text.strip()