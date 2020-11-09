# -*- coding: utf-8 -*-

import mwparserfromhell as mwp
import rdflib
import IMSLPtoRDF as imrdf

with open('D:/IMSLP_dump/categories/Category%3AStravinsky%2C_Igor','r',encoding='UTF-8') as wikitextin:
    w = mwp.parse(wikitextin)
for category in w.ifilter_wikilinks(matches='[^:]Category:'):
    print(category.title)