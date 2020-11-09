import mwclient
import os.path
from urllib.parse import quote
dumpdir = 'D:/IMSLP_dump/rand_testset'
ua = 'NimasWikiExtractor'

site = mwclient.Site('imslp.org', path='/', clients_useragent=ua)
page = site.pages['Symphony_No.9,_Op.125_(Beethoven,_Ludwig_van)']
normalizedName = str(mwclient.page.Page.normalize_title(page.name))
pageOutPath = os.path.join(dumpdir, quote(normalizedName, safe=()))
print(page.text(expandtemplates=True))
with open(pageOutPath+'noexpand', 'w', encoding='UTF-8') as pageout:
    print(page.name)
    pageout.write('<!--Pagename:{}-->\n'.format(page.name))
    pageout.write(page.text(expandtemplates=False))
'''for page in site.allpages(start=startAt):
    with open(progressFile,'w',encoding='UTF-8') as progressfile:
        progressfile.write(mwclient.page.Page.normalize_title(page.name))
    pageOutPath = os.path.join('D:\IMSLP_dump\wikitext_out',str(page.pageid))
    with open(pageOutPath,'w',encoding='UTF-8') as pageout:
        print(page.name)
        pageout.write('<!--Pagename:{}-->\n'.format(page.name))
        pageout.write(page.text(expandtemplates=True))'''