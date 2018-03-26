#!/usr/bin/env python3

# -*- coding: utf-8 -*- 
import requests
from lxml import html
import urllib
import os
import json
import time
import html2text
import pymysql

username = "***"
password = "******"

allUrls = []
listUrl = "http://%s.iteye.com/?page="%(username)
for page in range(1, 6):
    listResult = requests.get(
        listUrl + str(page), 
        headers= dict(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
                "referer": "http://%s.iteye.com"%(username)
            }
        )
    )
    listTree = html.fromstring(listResult.text)
    pageUrls = list(set(listTree.xpath("//div[@class='blog_title']/h3/a/@href")))
    allUrls.extend(pageUrls)
    time.sleep(0.4)
print(allUrls)


session_request = requests.session()

login_url = "http://www.iteye.com/login"

result = session_request.get(
    login_url,
    headers = dict({"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"})
)


tree = html.fromstring(result.text)
authenticity_token = list(set(tree.xpath("//input[@name='authenticity_token']/@value")))[0]

payload = {
    "name": username,
    "password": password,
    "authenticity_token": authenticity_token
}

result = session_request.post(
    login_url,
    data = payload,
    headers = dict(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
            "referer": login_url
        }
    )
)


mysqlconn = pymysql.connect("localhost", "root", "root123", "blog", use_unicode=True, charset="utf8")
cursor = mysqlconn.cursor()


def write2Json(title, tags, category, body, createTime):
    articleJson = {
        "title": title,
        "keyword": tags,
        "category": category,
        "content": html2text.html2text(body),
        "createdAt": createTime
    }

    backDirPath = "./backup/mardown"
    if not os.path.exists(backDirPath):
        os.makedirs(backDirPath)
    with open(backDirPath + "/" + articleId + "_" + title + ".json", "w", encoding="utf-8") as f:
        json.dump(articleJson, f, ensure_ascii=False, indent=4)
    print(articleId + "_" + title)
    time.sleep(0.6)

def write2db(title, tags, category, body, createTime):
    categoryId = 0
    csql = "select c.id, c.name from category c where c.name='%s'" % (category)
    cursor.execute(csql)
    cresult = cursor.fetchall()
    if cresult:
        for row in cresult:
            categoryId = int(row[0])
    else:
        try:
            insertCategorySql = "INSERT INTO category(name) VALUES('%s')" %(category)
            cursor.execute(insertCategorySql)
            categoryId = int(cursor.lastrowid)
            mysqlconn.commit()
        except:
            mysqlconn.rollback()

    try:
        insertArticleSql = "INSERT INTO `article`(`id`, `title`, `keyword`, `category_id`, `content`, `created_at`, `status`) VALUES(DEFAULT, '{0}', '{1}', {2}, '{3}', '{4}:00', 'draft')".format(title, tags, categoryId, html2text.html2text(body).replace("\\", "\\\\").replace("'", "\\'"), createTime)
        cursor.execute(insertArticleSql)
        mysqlconn.commit()
    except:
        mysqlconn.rollback()
        print(insertArticleSql)

    time.sleep(0.6)


for articlePath in allUrls:

    articleId = articlePath.split('/')[-1]
    url = "http://%s.iteye.com/admin/blogs/%s/edit"%(username, articleId)
    result = session_request.get(
        url,
        headers= dict(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
                "referer": login_url
            }
        )
    )


    tree = html.fromstring(result.text)
    
    body = list(set(tree.xpath("//textarea/text()")))[0]
    title = list(set(tree.xpath("//input[@name='blog[title]']/@value")))[0]
    category = list(set(tree.xpath("//input[@name='blog[category_list]']/@value")))[0]
    tags = list(set(tree.xpath("//input[@name='blog[tag_list]']/@value")))[0]

    readUrl = "http://%s.iteye.com/blog/%s"%(username, articleId)
    readResult = requests.get(
        readUrl, 
        headers= dict(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
                "referer": login_url
            }
        )
    )
    readTree = html.fromstring(readResult.text)
    createTime = list(set(readTree.xpath("//div[@class='blog_bottom']//li[1]/text()")))[0]
    createDate = createTime.split(' ')[0].replace('-', '')

    attachments = list(set(tree.xpath("//div[starts-with(@id,'attachment_')]/a[@target='_blank']/@href")))
    for imgUrl in attachments:
        imgName = imgUrl.split('/')[-1]
        dirName = "./backup/images/figures/" + createDate
        if not os.path.exists(dirName):
            os.makedirs(dirName)
        urllib.request.urlretrieve(imgUrl, dirName + "/" + imgName)
        imgUrlOld = imgUrl.replace("dl2.iteye", "dl.iteye")
        body = body.replace(imgUrl, "/resources/figures/" + createDate + "/" + imgName).replace(imgUrlOld, "/resources/figures/" + createDate + "/" + imgName)

    ##博客内容写入json文件保存
    write2Json(title, tags, category, body, createTime)

    ##博客内容直接写入数据库
    #write2db(title, tags, category, body, createTime)

mysqlconn.close()




