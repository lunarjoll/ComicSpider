# -*- coding: utf-8 -*-
"""
Created on Tue Jul 25 21:17:05 2017

@author: Quantum Liu
"""

from comic import *
import sys
def download_from_file(path,p=False):
    with open(path,'r') as f:
        ls=f.readlines()
    for l in ls:
# should trust url end is /
        l=l.strip(' \n')
        if l.find('manhua.dmzj.com') == -1:
            print("This script only support https://manhua.dmzj.com, new web www.dmzj.com's manhua not support")
            break
        if not l.endswith('/'):
            print(l)
            print("urls should end with / ")
            break
        if l=='':
            continue
        comic=Comic(l)
        comic.download_all_chapters_s(p)
if __name__=='__main__':
    if sys.platform.startswith('win'):
        freeze_support()
    path=(sys.argv[1] if len(sys.argv)>1 else './url.txt')
    print('Download comics based on file {f}'.format(f=path))
    p= (sys.argv[-1]=='1')
    if p:
        print('Using multi threads...')
    else:
        print('Using single thread...')
    download_from_file(path,p)
