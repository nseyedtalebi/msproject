import mwclient
import os.path
from urllib.parse import quote
progressFile = 'D:\IMSLP_dump\wikitext_out\progress.txt'

try:
    with open(progressFile,'r') as progressIn:
        startAt = progressIn.readline()        
except FileNotFoundError as e:
    startAt = None
site = mwclient.Site('imslp.org',path='/')
for page in site.allpages(start=startAt):
    normalizedName = mwclient.page.Page.normalize_title(page.name)
    with open(progressFile,'w',encoding='UTF-8') as progressfile:
        progressfile.write(normalizedName)
    pageOutPath = os.path.join('D:\IMSLP_dump\wikitext_out', quote(normalizedName,safe=()))
    with open(pageOutPath,'w',encoding='UTF-8') as pageout:
        print(page.name)
        pageout.write('<!--Pagename:{}-->\n'.format(page.name))
        pageout.write(page.text(expandtemplates=True))