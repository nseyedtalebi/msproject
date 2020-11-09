# -*- coding: utf-8 -*-
"""
Created on Sat Aug 26 14:49:25 2017

@author: Nima Seyedtalebi
"""
'''TODO:
    -Create mapping between entity type and fields to use for comparison
    -Create a list containing only these fields, entity type, and ext:score. 
    I will want to be able to sort by that score across all the different
    entity types used in a query
    -research fuzzy string matching. This seems like the way I will have to
    match up my results since the wiki data is relatively unstructured
'''
from itertools import chain
import musicbrainzngs as mb
mbEntities = ['annotations','areas','artists','events','instruments','labels'
              ,'places','recordings','release_groups','releases','series'
              ,'works']

def SearchMulti(query,*entityList,limit=None,offset=None):
    """Search MusicBrainz for multiple types of entity using the default fields
    
    Returns a dict of search results with entity names as keys.
    See the MusicBrainz webservice documentation for a full description
    of the MusicBrainz schema and API:
    https://wiki.musicbrainz.org/Development/XML_Web_Service/Version_2
    """
    res = {}
    if not entityList:
        entityList = ['artist','work']
    
    if 'annotation' in entityList:
        print('Searching annotation')
        res['annotation'] = mb.search_annotations(query=query,limit=limit
           ,offset=offset)
    if 'area' in entityList:
        print('Searching area')
        res['area'] = mb.search_areas(query=query,limit=limit,offset=offset)
    if 'artist' in entityList:
        print('Searching artist')
        res['artist'] = mb.search_artists(query=query,limit=limit
           ,offset=offset)
    if 'event' in entityList:
        print('Searching event')
        res['event'] = mb.search_events(query=query,limit=limit,offset=offset)
    if 'instrument' in entityList:
        print('Searching instrument')
        res['instrument'] = mb.search_instruments(query=query,limit=limit
           ,offset=offset)
    if 'label' in entityList:
        print('Searching label')
        res['label'] = mb.search_labels(query=query,limit=limit,offset=offset)
    if 'place' in entityList:
        print('Searching place')
        res['place'] = mb.search_places(query=query,limit=limit,offset=offset)
    if 'recording' in entityList:
        print('Searching recording')
        res['recording'] = mb.search_recordings(query=query,limit=limit
           ,offset=offset)
    if 'release_group' in entityList:
        print('Searching release_group')
        res['release_group'] = mb.search_release_groups(query=query,limit=limit
           ,offset=offset)
    if 'release' in entityList:
        print('Searching release')
        res['release'] = mb.search_releases(query=query,limit=limit
           ,offset=offset)
    if 'series' in entityList:
        print('Searching series')
        res['series'] = mb.search_series(query=query,limit=limit,offset=offset)
    if 'work' in entityList:
        print('Searching work')
        res['work'] = mb.search_works(query=query,limit=limit,offset=offset)
    return res

def GetCombinedResultsList(resultsDict):
    """Convert the dict returned by SearchMulti to a list
    
    The keys in resultsDict should be MusicBrainz entity names and the values
    should be the dicts returned by each search query.
    
    This may very well be useless because the fields used for comparison to
    the IMSLP results will vary depending on the entity.
    """
    combinedResults = []
    for entity in resultsDict.keys():
        resultListName = '{}-list'.format(entity)
        resultList = resultsDict[entity][resultListName]
        for result in resultList:
            result['resultType'] = entity
        combinedResults.append(resultList)
    combinedResults = chain.from_iterable(combinedResults)
    return combinedResults
    #This doesn't work the way I expected. Not worth troubleshooting until I
    #establish whether this will be useful.
    #sorted(combinedResults,key = lambda k:k['ext:score'],reverse=True)

mb.set_useragent('MusicBrainz-IMSLP Mediator','0.1','nseyedtalebi@gmail.com')
try:
    queryString = 'Alkan Festin d''Esope'
    searchResults = GetCombinedResultsList(SearchMulti(queryString))

except mb.MusicBrainzError as e:
    print('MusicBrainz request failed: {0}'.format(e.args))
