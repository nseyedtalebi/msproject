
#!/usr/bin/python

# This sample executes a search request for the specified search term.
# Sample usage:
#   python search.py --q=surfing --max-results=10
# NOTE: To use the sample, you must provide a developer key obtained
#       in the Google APIs Console. Search for "REPLACE_ME" in this code
#       to find the correct place to provide that key..

import argparse

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from urllib.parse import urlunparse,urlencode
import rdflib
sorg = rdflib.Namespace('https://schema.org/')
mo = rdflib.Namespace('http://purl.org/ontology/mo/')
local = rdflib.Namespace('https://schemaExtensions/')
# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
DEVELOPER_KEY = 'AIzaSyBgs-Wx1YKxMDTst6V03pCbvWlzPgxmIG8'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

def videos_list_by_id(client, **kwargs):
    return client.videos().list(**kwargs).execute()

def video_categories_list(client, **kwargs):
    return client.videoCategories().list(**kwargs).execute()

try:
    res = rdflib.Graph()
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    developerKey=DEVELOPER_KEY)

    video_categories = video_categories_list(youtube, part='snippet', regionCode='US')
    categoryID_lookup = {video_category_info['id']:video_category_info['snippet']['title']
                         for video_category_info in video_categories['items']}
    search_args = {}
    search_args['q'] = 'Symphony No.9, Op.125 (Beethoven, Ludwig van)'
    search_args['type']  = 'video'
    search_args['max_results'] = 10
    search_results = youtube.search().list(q=search_args['q'],part='id,snippet',maxResults=search_args['max_results']).execute()
    for item in search_results['items']:
        #print(search_response.uri) #Here!
        video_result = videos_list_by_id(youtube,part='id,snippet,contentDetails,topicDetails',id=item['id']['videoId'])
        for vid_result_details in video_result['items']:
            video_URI = rdflib.URIRef( urlunparse(('https','www.youtube.com','watch',None,
                                     urlencode( ( ('v',vid_result_details['id']), ))#Careful! Note trailing comma
                                     ,None) ))
            #from snippet
            res.add((video_URI,
                     sorg['datePublished'],
                     rdflib.Literal(vid_result_details['snippet']['publishedAt'], datatype=rdflib.XSD.date)))
            res.add((video_URI,
                     sorg['name'],
                     rdflib.Literal(vid_result_details['snippet']['localized']['title'], datatype=rdflib.XSD.string)))
            res.add((video_URI,
                     sorg['description'],
                    rdflib.Literal(vid_result_details['snippet']['localized']['description'], datatype=rdflib.XSD.string)))
            res.add((video_URI,
                     sorg['thumbnailUrl'],
                     rdflib.URIRef(vid_result_details['snippet']['thumbnails']['default']['url'])))
            res.add((video_URI,
                     local['inCategory'],
                     rdflib.Literal(categoryID_lookup[vid_result_details['snippet']['categoryId']],
                                    datatype=rdflib.XSD.string)))
            try:
                for tag in vid_result_details['snippet']['tags']:
                    res.add((video_URI,
                         sorg['keywords'],
                         rdflib.Literal(tag,datatype=rdflib.XSD.string)))
            except KeyError:
                pass
            #From contentDetails
            res.add((video_URI,
                     sorg['duration'],
                     rdflib.Literal(vid_result_details['contentDetails']['duration'],datatype=rdflib.XSD.duration)))
            #from topicDetails
            for topic in vid_result_details['topicDetails']['topicCategories']:
                res.add((video_URI,
                        local['additionalInfo'],
                        rdflib.URIRef(topic)))
            #print(vid_result_details['snippet'])
            #print(vid_result_details['contentDetails'])
            #print(vid_result_details['id'])
            #https://www.youtube.com/watch?v=<video_id_here>
except HttpError as e:
    print('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))

res.serialize(destination='./blazegraph/youtubeResults.n3',format='n3')