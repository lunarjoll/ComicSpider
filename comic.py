# -*- coding: utf-8 -*-
"""
Created on Sun Jul 23 11:03:51 2017

@author: Quantum Liu
"""

import re,os,traceback
import requests
import json
from io import BytesIO
#from PIL import Image
from selenium import webdriver
from multiprocessing import Pool,cpu_count,freeze_support
#from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.wait import WebDriverWait

options = Options()
options.add_argument('-headless')
driver = Firefox( options=options)


def validatetitle(title):
    '''
    transform a string to a validate filename
    将字符串转化为合法文件名
    '''
    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/\:*?"<>|'
    new_title = re.sub(rstr, "", title).replace(' ','')
    return new_title


class Chapter():
    '''
    一个对漫画章节的抽象
    '''
    def __init__(self,comic_title,comic_dir,chapter_title,chapter_url):
        self.comic_title,self.comic_dir,self.chapter_title,self.chapter_url=comic_title,comic_dir,chapter_title,chapter_url
        self.chapter_dir=os.path.join(self.comic_dir,validatetitle(self.chapter_title))
        if not os.path.exists(self.chapter_dir):
            os.mkdir(self.chapter_dir)
        self.pages=[]

#    def open_browser(self):
#        browser_options = Options()
#        browser_options.add_argument('-headless')
#       #self.driver = Firefox(executable_path='/usr/bin/geckodriver', options=browser_options)
#        self.driver = Firefox( options=browser_options)
    
    def get_all_pages(self):
        r_slt=r'onchange="select_page\(\)">([\s\S]*?)</select>'
        r_p=r'<option value="(.*?)".*?>第(\d*?)页<'
        try :
            #driver = Firefox( options=options)
            driver = Firefox( options=options)
            driver.get(self.chapter_url)
            text=driver.page_source
            st=re.findall(r_slt,text)[0]
            self.pages = [(int(p[-1]),p[0]) for p in re.findall(r_p,st)]
        except Exception:
            traceback.print_exc()
            self.pages = []
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        finally:
            driver.quit()
            print('Got {l} pages in chapter {ch}'.format(l=len(self.pages),ch=self.chapter_title))
            return 1
        
    def get_pages(self):
        '''
        通过Phantomjs获得网页完整源码，解析出每一页漫画的url
        Get all pages' urls using selenium an phantomJS
        return:
            a list of tuple (page_num,page_url)
        '''
        r_slt=r'onchange="select_page\(\)">([\s\S]*?)</select>'
        r_p=r'<option value="(.*?)".*?>第(\d*?)页<'
        try:
#            options = Options()
#            options.add_argument('-headless')
#            driver = Firefox(options=options)
# last move init

            #wait = WebDriverWait(driver, timeout=10)
            #dcap = dict(DesiredCapabilities.PHANTOMJS)
            ## 不载入图片，爬页面速度会快很多
            #dcap["phantomjs.page.settings.loadImages"] = False
            #driver = webdriver.PhantomJS(desired_capabilities=dcap)

            #firefox_profile = webdriver.FirefoxProfile()
            #firefox_profile.set_preference('permissions.default.image', 2)
            #firefox_profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false')
            #driver = webdriver.Firefox(firefox_profile=firefox_profile)
            driver.get(self.chapter_url)
            text=driver.page_source
            st=re.findall(r_slt,text)[0]
            self.pages = [(int(p[-1]),p[0]) for p in re.findall(r_p,st)]
        except Exception:
            traceback.print_exc()
            self.pages = []
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        finally:
#            driver.quit()
            print('Got {l} pages in chapter {ch}'.format(l=len(self.pages),ch=self.chapter_title))
            return self.pages
    
#    def close_browser(self):
#        self.driver.quit()

    def download_page(self,page):
        '''
        下载一页漫画
        Download a page and save it in a local file
        args:
            page:
                a tuple (page_num,page_url)
        return:
            status code
        '''
        headers={'use-agent':"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36",'referer':self.chapter_url}
        n=page[0]
        url=page[-1]
        if not os.path.exists(self.chapter_dir):
            os.mkdir(self.chapter_dir)
# 更好的通用性, 001.jpg更好
        #path=os.path.join(self.chapter_dir,str(n)+'.'+url.split('.')[-1])
        if n <10 :
            new_n= '00'+str(n)
        elif n<100 :
            new_n='0'+str(n)
        else:
            new_n=str(n)
            
        #path=os.path.join(self.chapter_dir,str(n)+'.'+url.split('.')[-1])
        path=os.path.join(self.chapter_dir,new_n +'.'+url.split('.')[-1])
        try:
            print('Downloading page {n} into file {f}'.format(n=n,f=path))
            res=requests.get('http:'+url,headers=headers)
            data=res.content
            with open(path,'wb') as f:
                f.write(data)
        except Exception:
            e=traceback.format_exc()
            print('Got eorr when downloading picture\n'+e)
            return 0
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        else:
            return 1
    
    def download_chapter_s(self):
        '''
        单线程下载本章节全部页
        Download all pages of the chapter not using multiprocessing
        '''
        results=[]
        if not self.pages:
            print('No page')
            return None
        print('Downloading chapter {c}'.format(c=self.chapter_title))
        results=[self.download_page(page) for page in self.pages]
        num=sum(results)
        print('Downloaded {} pages'.format(num))
    def download_chapter_m(self):
        '''
        多线程下载本章节全部页
        Download all pages of the chapter using multiprocessing
        '''
        results=[]
        if not self.pages:
            print('No page')
            return None
        mp=Pool(min(8,max(cpu_count(),4)))
        for page in self.pages:
            results.append(mp.apply_async(self.download_page,(page,)))
        mp.close()
        mp.join()
        num=sum([result.get() for result in results])
        print('Downloaded {} pages'.format(num))


class Comic():
    '''
    对一部漫画的抽象
    An abstraction of comic
    args:
        comic_url:漫画主页URL
        comic_title:漫画标题，缺省值为自动填充
        comic_dir:漫画保存目录，缺省值为根据标题自动填充
    '''
    def __init__(self,comic_url,comic_title=None,comic_dir=None):
        self.comic_url=comic_url
        n_comic_title,self.des,self.cover,self.chapter_urls=self.get_info()
        self.chapter_num=len(self.chapter_urls)
        self.comic_title=(comic_title if comic_title else n_comic_title)
        self.comic_dir=os.path.abspath((comic_dir if comic_dir else validatetitle(self.comic_title)))
        if not os.path.exists(self.comic_dir):
            os.mkdir(self.comic_dir)
        print('There are {n} chapters in comic {c}'.format(n=self.chapter_num,c=self.comic_title))
        #self.chapters 的格式
        self.chapters={info[0]:Chapter(self.comic_title, self.comic_dir, *info) for info in self.chapter_urls}
        self.pages=[]
        
    def get_info(self):
        '''
        获取漫画标题、简介、封面url，章节url
        Get informations of the comic
        return:
            comic title,description,cover url,chapters' urls
        '''
        headers={'use-agent':"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36",'Referer':'http://manhua.dmzj.com/tags/s.shtml'}
        root='http://manhua.dmzj.com'
        r_title=r'<span class="anim_title_text"><a href=".*?"><h1>(.*?)</h1></a></span>'
        r_des=r'<meta name=\'description\' content=".*?(介绍.*?)"/>'#简介正则
        r_cover=r'src="(.*?)" id="cover_pic"/></a>'#封面url正则
        r_cb=r'<div class="cartoon_online_border" >([\s\S]*?)<div class="clearfix"></div>'#章节border
        r_cs=r'<li><a title="(.*?)" href="(.*?)" .*?>.*?</a>'#章节链接正则
        try:
            text=requests.get(self.comic_url,headers=headers).text
        except ConnectionError:
            traceback.print_exc()
            raise ConnectionError
        #print(text)
        #print(re.findall(r_title,text)[0])
        #r_title=r'<span class="anim_title_text"><a href="../guoranwodeqingchunlianaixijugaocuolecomic/"><h1>果然我的青春恋爱喜剧搞错了@comic</h1></a></span>'
        title=re.findall(r_title,text)[0]
        #title= '<span class="anim_title_text"><a href="../guoranwodeqingchunlianaixijugaocuolecomic/"><h1>果然我的青春恋爱喜剧搞错了@comic</h1></a></span>'
        cb=re.findall(r_cb,text)[0]

        #This is why we should give url tail must is http:/xxxx/
        #c[0] is title, c[1] is url
        #for 是列表返回
        chapter_urls=[(c[0],root+c[1]+'#@page=1') for c in re.findall(r_cs,cb)]
        cover_url=re.findall(r_cover,text)[0]
        des=re.findall(r_des,text)
        return title,des,cover_url,chapter_urls
    
    #No use
    def update(self):
        '''
        更新漫画（未测试）
        '''
        n_chapter_urls=self.get_info()
        num=0
        for info in n_chapter_urls:
            if not info in self.chapter_urls:
                num+=1
                self.chapters[info[0]]=Chapter(self.comic_title, self.comic_dir, *info)
        if num:
            self.chapter_urls=n_chapter_urls
            print('Got {n} new chapters:\n{chs}'.format(n=num,chs='\n'.join([info[0] for info in self.chapter_urls])))
        else:
            print('No new chapter found')
            
    def print_chapters(self,show=False):
        '''
        打印章节信息
        Display infos of chapters.
        '''
        headers={'use-agent':"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36",'Referer':'http://manhua.dmzj.com/tags/s.shtml'}
        text='There are {n} chapters in comic {c}:\n{chs}'.format(n=self.chapter_num,c=self.comic_title,chs='\n'.join([info[0] for info in self.chapter_urls]))
        print(text)
        if show:
            try:
                res=requests.get(self.cover,headers=headers)
                if b'403' in res.content:
                    raise ValueError('Got cover img failed')
                out=BytesIO(res.content)
                out.seek(0)
                Image.open(out).show()
            except (ConnectionError,ValueError):
                traceback.print_exc()
        return text

# It is 2
    def download_chapter(self,key,p=True):
        '''
        下载一个章节
        Download a chapter by chapter title
        key:title
        p:multiprocessing or not
        '''
        if not key in self.chapters:
            print('No such chapter {key}\nThere are chapters:\n{chs}'.format(key=key,chs='\n'.join(self.chapters.keys())))
            return None
        if not self.chapters[key].pages:
#self.pages is Class Comic is no used,
            #self.pages+=self.chapters[key].get_pages()
            self.chapters[key].get_pages()
        #多进程
        (self.chapters[key].download_chapter_m() if p else self.chapters[key].download_chapter_s())


# it is start command by lunarjoll, it is 1st
    def download_all_chapters_s(self,p=False):
        '''
        下载所有章节，在章节层面单线程
            p:在页层面是否使用多线程
        '''
        print('Downloading all chapters of comic {title} into dir {d}'.format(title=self.comic_title,d=self.comic_dir))
#循环章节
#在这里 删除chapters,实现update
        update_path=os.path.join(self.comic_dir,'update.txt')
        delete_list=[]
        down_list=[]
        if os.path.exists(update_path):
            with open(update_path,'r') as json_f:
                for line in json_f:
                    delete_list.append(line.strip('\n'))
        #print (delete_list)
        for i in self.chapters.keys():
            down_list.append(i)
        for i in delete_list:
            down_list.remove(i)

        if down_list != []:
            #[self.chapters[key].get_pages() for key in self.chapters.keys()]
#            [self.chapters[key].get_all_pages() for key in down_list]
            #[self.download_chapter(key=title,p=p) for title in self.chapters.keys()]
            for key in down_list:
                self.chapters[key].get_all_pages()
                driver.quit
            [self.download_chapter(key=title,p=p) for title in down_list]
            # close browser
#            for i in self.chapters.keys():
#                self.chapters[i].close_browser()
#                break
            with open(update_path,'w') as json_f:
                for i in self.chapters.keys():
                    json_f.write(i+'\n')
        #driver.quit()


        



# It func is't appoint, No use
    def download_all_chapters_p(self):
        '''
        在章节层面多线程
        '''
        mp=Pool(min(8,max(cpu_count(),4)))
        for key in self.chapters.keys():
            mp.apply_async(self.download_chapter,(key,False))
        mp.close()
        mp.join()
