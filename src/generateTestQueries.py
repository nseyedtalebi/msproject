# -*- coding: utf-8 -*-
"""
Created on Sun Sep 24 15:09:47 2017

@author: NiMo3
"""

import mwclient
import re
import csv
titlePattern = r'([^\(\),]*)(,*.*)\((.*,.*)\)'
titleMatcher = re.compile(titlePattern)
site = mwclient.Site('imslp.org',path='/')
randomPages = []

while len(randomPages) < 100:
    randomPages.extend(site.random(0))

columnHeaders = ['work','artist','search_string','pageTitle']
with open('testQueries.csv','w',encoding='utf-8') as outfile:
    writecsv = csv.DictWriter(outfile,columnHeaders,lineterminator='\n')
    writecsv.writeheader()
    for page in randomPages:
        m = titleMatcher.match(page['title'].strip('\n'))
        if m:
            writecsv.writerow({'work':m.group(1)+m.group(2),
                               'artist':m.group(3),
                               'search_string':m.group(1),
                               'pageTitle':m.group(0)})
        
    #splitTitle = page['title'].split(',')
    #print(splitTitle[0])