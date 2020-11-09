import mwclient
import os.path
from urllib.parse import quote
dumpdir = 'D:\\IMSLP_dump\\categories'
ua = 'NimasWikiExtractor'

site = mwclient.Site('imslp.org', path='/', clients_useragent=ua)
for page in site.allpages(namespace=14):
    normalizedName = str(mwclient.page.Page.normalize_title(page.name))
    pageOutPath = os.path.join(dumpdir, quote(normalizedName, safe=()))
    with open(pageOutPath,'w',encoding='UTF-8') as pageout:
        print(page.name)
        pageout.write('<!--Pagename:{}-->\n'.format(page.name))
        pageout.write(page.text(expandtemplates=True))