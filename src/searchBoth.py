# -*- coding: utf-8 -*-
"""
Created on Sun Sep 17 11:39:07 2017
TODO:
    Try searching IMSLP first, then use those results to search MB, then use local search engine to match results.
    See if that does better than what's here currently.
"""
import mwclient,csv,re
import musicbrainzngs as mb

from whoosh import fields,index,analysis
from whoosh.support import charset
from whoosh.qparser import QueryParser,MultifieldParser
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
    #Seems like this is just asking to be parallelized. Why can't both searches run at once?
    #using the accent folding is probably a waste - it's most likely done on the other end
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
        if not artist or len(workRes)==0:
            workRes = mb.search_works(query=workQuery,limit=limit,offset=offset)['work-list']
    return {'artists':artistRes,'works':workRes}

def SearchMBByIMSLPPageTitle(pageTitle):
    m = titleMatcher.match(pageTitle)
    lim = 5
    if m:
        artistRes = mb.search_artists(query=m.group(2),limit=lim)['artist-list']
        workRes = mb.search_works(query='work:{workname} AND artist:{artistname}'.format(workname=m.group(1),artistname=m.group(2)),limit=lim)['work-list']
        results = {}
        if artistRes:
            results['artists']=artistRes
        if workRes:
            results['workRes']=workRes
        return results

class MBResultSchema(fields.SchemaClass):
    mbid = fields.ID(stored=True)
    name = fields.TEXT(analyzer=accentCaseFoldAnalyzer,stored=True)
    rawResult = fields.TEXT(analyzer=accentCaseFoldAnalyzer)

class IMSLPResultSchema(fields.SchemaClass):
    pageTitle = fields.TEXT(analyzer=accentCaseFoldAnalyzer,stored=True)
    wikiText = fields.TEXT(analyzer=accentCaseFoldAnalyzer)

def GetResultIndexes(indexBasePath='.'):
    mbIndexName = 'mbResultIndex'
    mbIndexPath = os.path.join(indexBasePath,mbIndexName)
    imslpIndexName = 'imslpResultIndex'
    imslpIndexPath = os.path.join(indexBasePath,imslpIndexName)
    if not os.path.exists(indexBasePath):
        os.mkdir(indexBasePath)
    if not os.path.exists(mbIndexPath):
        os.mkdir(mbIndexPath)
    if not os.path.exists(imslpIndexPath):
        os.mkdir(imslpIndexPath)
    #Note: Calling create_in on a path that alreay has an index clears the idx
    mbIdx = index.create_in(mbIndexPath,MBResultSchema(),mbIndexName)
    imslpIdx = index.create_in(imslpIndexPath,IMSLPResultSchema(),imslpIndexName)
    return {'mbIndex':mbIdx,'imslpIndex':imslpIdx}

def IndexSearchResults(indexDict,imslpResults,mbResults):
    with indexDict['imslpIndex'].writer() as imslpIdxWriter:
        for res in imslpResults:
            imslpIdxWriter.add_document(pageTitle=res.page_title,wikiText=res.text())
    with indexDict['mbIndex'].writer() as mbIdxWriter:
        for res in mbResults['artists']:
            mbIdxWriter.add_document(mbid=res['id'],name=res['name'],rawResult=str(res))
        for res in mbResults['works']:
            mbIdxWriter.add_document(mbid=res['id'],name=res['title'],rawResult=str(res))

def SearchIndexes(indexDict,queryString):
    with resultIndexes['imslpIndex'].searcher() as imslpIdxSearcher:
        print('Searching imslp index for {}'.format(queryString))
        wquery = MultifieldParser(('pageTitle','wikiText'),resultIndexes['imslpIndex'].schema).parse(queryString)
        imslpHits = [dict(hit) for hit in imslpIdxSearcher.search(wquery)]
    with resultIndexes['mbIndex'].searcher() as mbIdxSearcher:
        print('Searching musicbrainz index for {}'.format(queryString))
        wquery = MultifieldParser(('name','rawResult'),resultIndexes['mbIndex'].schema).parse(queryString)
        mbHits = [dict(hit) for hit in mbIdxSearcher.search(wquery)]
        return {'imslp':imslpHits,'mb':mbHits}

#~~~~~~~~~~~~~~~~~~~~~~~~~Main~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
try:
    resultIndexes = GetResultIndexes('searchIndexes')
    columnHeaders = ['work','artist','queryString','mbHit','imslpHit']
    #queryString = "Alkan Chemin Fer"
    with open('testQueries.csv','r',encoding='utf-8') as infile, open('testOutput.csv','w',encoding='utf-8') as testResultsFile:
        csvwriter = csv.DictWriter(testResultsFile,columnHeaders,lineterminator='\n')
        csvwriter.writeheader()
        for row in csv.DictReader(infile):
            queryString = '{artist} {work}'.format(artist=row['artist'],work=row['search_string'])
            out_row = {}
            out_row['artist'] = row['artist']
            out_row['work'] = row['work']
            out_row['queryString'] = queryString
            #mbResults = SearchMB(queryString)
            imslpResults = SearchIMSLP(queryString)
            mbResults = SearchMB(artist=row['artist'],work=row['search_string'])
            #mbResults = SearchMBByIMSLPPageTitle(row['pageTitle'])
            #mbResultList.append(SearchMBByIMSLPPageTitle(row['pageTitle']))
            IndexSearchResults(resultIndexes,imslpResults,mbResults)
            searchHits = SearchIndexes(resultIndexes,queryString)
            if searchHits['imslp']:
                out_row['imslpHit'] = searchHits['imslp'][0]['pageTitle']
            else:
                out_row['imslpHit'] = None
       
            if searchHits['mb']:
                out_row['mbHit']=searchHits['mb'][0]['name']
            else:
                out_row['mbHit']=None
            csvwriter.writerow(out_row)
            
except mb.MusicBrainzError as e:
    print('MusicBrainz request failed: {0}'.format(e))