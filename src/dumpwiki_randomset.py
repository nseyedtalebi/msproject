import mwclient
import os.path
from os import listdir
from urllib.parse import quote
dumpdir = 'D:/IMSLP_dump/rand_testset_10k'
site = mwclient.Site('imslp.org',path='/')
while len(listdir(dumpdir)) < 10000:
    for pageInfo in site.random(0,limit=10):
        page = site.pages[pageInfo['title']]
        normalizedName = str(mwclient.page.Page.normalize_title(page.name))
        pageOutPath = os.path.join(dumpdir, quote(normalizedName, safe=()))
        with open(pageOutPath,'w',encoding='UTF-8') as pageout:
            #print(page.name)
            pageout.write('<!--Pagename:{}-->\n'.format(page.name))
            pageout.write(page.text(expandtemplates=True))
