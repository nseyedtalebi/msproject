import mwclient,csv,re
import musicbrainzngs as mb

from whoosh import fields,index,analysis
from whoosh.support import charset
from whoosh.qparser import QueryParser
import os
mb.set_useragent('MusicBrainz-IMSLP Mediator','0.1','nseyedtalebi@gmail.com')
titlePattern =r'([^\(\)]*)\((.*,.*)\)'
titleMatcher = re.compile(titlePattern)

charmap = charset.charset_table_to_dict(
            charset.default_charset)
accentCaseFoldAnalyzer = analysis.RegexTokenizer() | analysis.CharsetFilter(charmap) | analysis.SubstitutionFilter(r'[{}\[\]:\']','')

def SearchIMSLP(queryString,searchType=None):
    site = mwclient.Site('imslp.org',path='/')
    return [mwclient.page.Page(site,res['title']) for res in site.search(queryString)]

mbEntities = ['annotations','areas','artists','events','instruments','labels'
              ,'places','recordings','release_groups','releases','series'
              ,'works']

def SearchMB(artist=None,work=None,limit=None,offset=None):
    #Seems like this is juts asking to be parallelized. Why can't both searches run at once?
    reTokenizer = analysis.tokenizers.RegexTokenizer()
    charFilter = analysis.CharsetFilter(charmap)
    if artist:
        artistQuery = ' '.join([word.text for word in charFilter(reTokenizer(artist))])
        artistRes = mb.search_artists(query=artistQuery,limit=limit
       ,offset=offset)['artist-list']
    if work:
        workQuery = ' '.join([word.text for word in charFilter(reTokenizer(work))])
        if artist:
            queryString = 'work:{workname} OR alias:{workname} AND artist:{artistname}'.format(workname=workQuery,artistname=artistQuery)
            workRes = mb.search_works(query=queryString,limit=limit,offset=offset)['work-list']
        else:
            workRes = mb.search_works(query=workQuery,limit=limit,offset=offset)['work-list']
    return {'artists':artistRes,'works':workRes}

res = SearchMB(artist='Schütz, Heinrich',work='Christ ist erstanden')