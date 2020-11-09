import rdflib, re, dateparser, datetime, logging
import mwparserfromhell as mwp
from urllib.parse import quote, urljoin, urlsplit, urlunsplit, urlunparse, urlencode
from mwclient.page import Page
from itertools import product
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
sorg = rdflib.Namespace('http://schema.org/')
mo = rdflib.Namespace('http://purl.org/ontology/mo/')
local = rdflib.Namespace('http://schemaExtensions/')
getty = rdflib.Namespace('http://vocab.getty.edu/aat/')
imslpBase = 'http://imslp.org/wiki/'
wikipediaBase = 'https://en.wikipedia.org/wiki/'
imslp = rdflib.Namespace(imslpBase)
scoreURLpattern = re.compile('https://imslp.org/wiki/Special:ImagefromIndex/\d+')
fileDetailPattern = re.compile('(\w+) by (\w+)')
uploadDatePattern = re.compile('\((\d+/\d+/\d+)\)')
duration_size_info_pattern = re.compile('\s-\s(\d+\.\d+MB)(?:,\s|\s-\s)(\d+\spp\.|\d*\:*\d+\:\d+)\s')
duration_format_pattern = re.compile('(?:(\d+)\:)*(\d+)\:(\d+)')
category_link_title_pattern = re.compile('^Category:')
DEVELOPER_KEY = 'AIzaSyBgs-Wx1YKxMDTst6V03pCbvWlzPgxmIG8'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
MAX_YOUTUBE_RESULTS = 10

def videos_list_by_id(client, **kwargs):
    return client.videos().list(**kwargs).execute()

def video_categories_list(client, **kwargs):
    return client.videoCategories().list(**kwargs).execute()

def wiki_uri_quote(input_uri):
    return quote(str(Page.normalize_title(input_uri)),safe='/:')

def get_url_for_wikipage(wikibaseurl, wikilink):
    quotedWikilink = wiki_uri_quote(wikilink)
    newurl = urljoin(wikibaseurl,quotedWikilink)
    if newurl == quotedWikilink:#missing leading slash or colon can make urljoin return only 'wikilink' part
        newurl = urljoin(wikibaseurl,':'+quotedWikilink)
    return newurl

def add_fragment_to_url(url,fragmentToAdd):
    spliturl = urlsplit(url)
    newurl = (spliturl.scheme,spliturl.netloc,spliturl.path,spliturl.query,quote(fragmentToAdd))
    return urlunsplit(newurl)

def iterate_table_rows(some_wikitable):
    for tablerow in some_wikitable.contents.ifilter_tags(recursive=False):
        yield tuple(tableCol.contents for tableCol in tablerow.contents.ifilter_tags(recursive=False))

def iterate_table_key_value_pairs(some_wikitable):
    for tablerow in iterate_table_rows(some_wikitable):
        #yield tablerow[0],tablerow[1]
        yield(tuple(val for val in tablerow))

def check_tag_class(node,tagTypeName=None,classesToMatch=[]):
    if node.tag == tagTypeName and node.has('class'):
        return any((x == y for x,y in product(str(node.get('class').value).split(sep=' '),classesToMatch)))

def format_date(datetime):
    return datetime.strftime('%Y-%m-%d')

def format_hms_duration(hms_duration_str):
    m = duration_format_pattern.search(hms_duration_str)
    if m:
        if m.group(1):
            return 'PT{hours}H{mins}M{sec}S'.format(hours=m.group(1),mins=m.group(2),sec=m.group(3))
        else:
            return 'PT{mins}M{sec}S'.format(mins=m.group(2), sec=m.group(3))

class IMSLPWorkPage:
    def __init__(self,wikitextin):
        self.page_wikitext = mwp.parse(wikitextin)
        pagetitle_comment = next(self.page_wikitext.ifilter_comments(matches='Pagename')).contents.split(':')
        self.pagetitle = ":".join(pagetitle_comment[1:])
        self.pageURI = rdflib.URIRef(get_url_for_wikipage(imslpBase, self.pagetitle))
        self.pageTriples = rdflib.Graph(identifier=self.pageURI)
        self.pageTriples.add( (self.pageURI,
                               rdflib.RDF.type,
                               sorg['MusicComposition']) )
        self.pageTriples.add( (self.pageURI,
                               sorg['url'],
                               self.pageURI))

    def get_triples_from_category_link(self,category_link):

        self.pageTriples.add((self.pageURI,
                              sorg['category'],
                              rdflib.URIRef(get_url_for_wikipage(imslpBase, category_link.title))))

    def get_triples_from_geninfo_section(self,start_node):
        for table in start_node.contents.ifilter_tags(matches=lambda node: node.tag == "table"):
            try:
                for fieldName,fieldValue in iterate_table_key_value_pairs(table):
                    if fieldName.matches('Work Title'):
                        self.pageTriples.add((self.pageURI,
                                         sorg['name'],
                                         rdflib.Literal(fieldValue, datatype=sorg['Text'])))
                    elif fieldName.matches(
                            'Alt<span class=\'mh555\'>ernative</span><span class=\'ms555\'>.</span> Title'):
                        self.pageTriples.add((self.pageURI,
                                         sorg['alternateName'],
                                         rdflib.Literal(fieldValue, datatype=sorg['Text'])))
                    elif fieldName.matches('Composer'):
                        hasAny = None
                        for wikilink in fieldValue.ifilter_wikilinks():
                            hasAny = True
                            composer_URI = rdflib.URIRef(get_url_for_wikipage(imslpBase, wikilink.title))
                            self.pageTriples.add((self.pageURI,
                                             sorg['composer'],
                                             composer_URI))
                            self.pageTriples.add( (composer_URI,
                                                   rdflib.RDF.type,
                                                   sorg['Person']) )
                        if not hasAny:
                            composer_URI =  get_url_for_wikipage(imslpBase, fieldValue.strip_code())
                            self.pageTriples.add( (self.pageURI,
                                             sorg['composer'],
                                             rdflib.URIRef(composer_URI)) )
                            self.pageTriples.add( (rdflib.URIRef(composer_URI),
                                                   rdflib.RDF.type,
                                                   sorg['Person']) )
                    elif fieldName.matches(
                            '<span class="mh555">Opus/Catalogue Number</span><span class="ms555">Op./Cat. No.</span>'):
                        self.pageTriples.add((self.pageURI,
                                         mo['opus'],
                                         rdflib.Literal(fieldValue, datatype=rdflib.RDFS.Literal)))
                    elif fieldName.matches('Key'):
                        hasAny = None
                        for wikilink in fieldValue.ifilter_wikilinks(recursive=False):
                            hasAny = True
                            self.pageTriples.add((self.pageURI,
                                             sorg['musicalKey'],
                                             rdflib.URIRef(
                                                 get_url_for_wikipage(imslpBase, wikilink.title))))
                        if not hasAny:
                            self.pageTriples.add((self.pageURI,
                                             sorg['musicalKey'],
                                             rdflib.Literal(fieldValue, datatype=sorg['Text'])))

                    elif fieldName.matches(
                            "<span class='mh555'>Movements/Sections</span><span class='ms555'>Mov'ts/Sec's</span>"):
                        textnodes = [str(node).strip('\n') for node in fieldValue.filter_text(recursive=False)]
                        if textnodes:
                            for textnode in textnodes[1:]:  # first node is usu header info so skip it
                                included_comp_name = add_fragment_to_url(self.pageURI, textnode)
                                self.pageTriples.add((self.pageURI,
                                                 sorg['includedComposition'],
                                                 rdflib.URIRef(included_comp_name)))
                                self.pageTriples.add((rdflib.URIRef(included_comp_name),
                                                      rdflib.RDF.type,
                                                      sorg['MusicComposition']))
                                ''' Name movements in compositions using URL fragment. 
                                No anchors exist on the pages so it
                                won't do anything special in a browser, 
                                but it makes a good unique name for each movement
                                where it's easy to tell by inspection which piece 
                                the movement belongs with'''
                                self.pageTriples.add((rdflib.URIRef(add_fragment_to_url(self.pageURI, textnode)),
                                                 sorg['name'],
                                                 rdflib.Literal(textnode, datatype=sorg['Text'])))

                    elif fieldName.matches(
                        "<span class='mh555'>Year/Date of Composition</span><span class='ms555'>Y/D of Comp.</span>"):
                        yearComposed = dateparser.parse(fieldValue.strip_code())
                        if yearComposed:
                            self.pageTriples.add((self.pageURI,
                                             sorg['dateCreated'],
                                                  rdflib.Literal(yearComposed.year, datatype=sorg['Date'])))
                    elif fieldName.matches(
                            'First Perf<span class=\'mh555\'>ormance</span><span class=\'ms555\'>.</span>'):
                        self.pageTriples.add((self.pageURI,
                                         local['descriptionOfFirstPerformance'],
                                         rdflib.Literal(fieldValue, datatype=sorg['Text'])))
                    elif fieldName.matches(
                            'First Pub<span class=\'mh555\'>lication</span><span class=\'ms555\'>.</span>'):
                        yearPublished = dateparser.parse(fieldValue.strip_code())
                        if yearPublished:
                            self.pageTriples.add((self.pageURI,
                                             sorg['datePublished'],
                                                  rdflib.Literal(yearPublished.year, datatype=sorg['Date'])))
                    elif fieldName.matches('Librettist'):
                        wikilinks = fieldValue.filter_wikilinks()
                        for link in wikilinks:
                            self.pageTriples.add((self.pageURI,
                                             local['Librettist'],
                                             # link to 'librettists'
                                             rdflib.URIRef(get_url_for_wikipage(imslpBase, link.title))))
                            self.pageTriples.add((rdflib.URIRef(get_url_for_wikipage(imslpBase, link.title)),
                                                  rdflib.RDF.type,
                                                  sorg['Person']))
                        if not wikilinks:
                            self.pageTriples.add((self.pageURI,
                                                  local['Librettist'],
                                                  rdflib.URIRef(get_url_for_wikipage(
                                                      imslpBase,fieldValue.strip_code()))))
                            self.pageTriples.add((rdflib.URIRef(get_url_for_wikipage(
                                imslpBase,fieldValue.strip_code())),
                                                  rdflib.RDF.type,
                                                  sorg['Person']))
                    elif fieldName.matches('Language'):
                        wiki_language_link = rdflib.URIRef(get_url_for_wikipage(wikipediaBase,
                                                            '{}_language'.format(fieldValue.strip_code())))
                        self.pageTriples.add((self.pageURI,
                                         sorg['inLanguage'],
                                             wiki_language_link))
                        self.pageTriples.add((wiki_language_link,
                                              rdflib.RDF.type,
                                              sorg['Language']))
                    elif fieldName.matches(
                            '<span class=\'mh555\'>Average Duration</span><span class=\'ms555\'>Avg. Duration</span>'):
                        avgDuration = dateparser.parse(fieldValue.strip_code())
                        if avgDuration:
                            avgDurationMinutes = int(abs(avgDuration - datetime.datetime.now()).total_seconds() / 60)
                            self.pageTriples.add((self.pageURI,
                                             sorg['timeRequired'],
                                             rdflib.Literal('PT{}M'.format(avgDurationMinutes),
                                                            datatype=sorg['Duration'])))
                    elif fieldName.matches('Piece Style'):
                        hasAny = None
                        for wikilink in fieldValue.ifilter_wikilinks():
                            hasAny = True
                            self.pageTriples.add((self.pageURI,
                                             sorg['genre'],
                                             rdflib.URIRef(
                                                 get_url_for_wikipage(imslpBase, wikilink.title))))
                        if not hasAny:
                            self.pageTriples.add((self.pageURI,
                                             #local['genre_text'],
                                             sorg['genre'],
                                             rdflib.URIRef(
                                                 get_url_for_wikipage(imslpBase, fieldValue.strip_code()))))
                    elif fieldName.matches('Instrumentation'):
                        self.pageTriples.add((self.pageURI,
                                         local['writtenForInstruments'],
                                         rdflib.Literal(fieldValue.strip_code(), datatype=sorg['Text'])))
            except Exception as e:
                logging.exception('''Exception of type {0} while 
                processing general info table:{1}'''.format(type(e),e))

    def get_triples_from_scores(self,start_node):

        for div_we in start_node.contents.ifilter_tags(matches=lambda node: check_tag_class(node, 'div', ['we'])):
            self.process_div_we(div_we)

    def get_triples_from_audio_files(self,start_node):
        for div_we in start_node.contents.ifilter_tags(matches=lambda node: check_tag_class(node, 'div', ['we'])):
            self.process_div_we(div_we)

    def process_div_we(self, parentTag):
        for div_we_file in parentTag.contents.ifilter_tags(
                matches=lambda node: check_tag_class(node, 'div', ['we_file', 'we_file_first'])):
            for downloadLink in div_we_file.contents.ifilter_external_links(
                    matches=lambda node: scoreURLpattern.match(str(node.url))):
                file_URI = rdflib.URIRef(downloadLink.url)
                self.pageTriples.add( (file_URI,
                                       rdflib.RDF.type,
                                       sorg['MediaObject']) )
                self.pageTriples.add((file_URI,
                                      sorg['contentURL'],
                                      file_URI))
                self.pageTriples.add((file_URI,
                                 sorg['encodesCreativeWork'],
                                      self.pageURI))
                self.pageTriples.add((file_URI,
                                 sorg['name'],
                                 rdflib.Literal(downloadLink.title.strip_code(), datatype=sorg['Text'])))
            for size_info in div_we_file.contents.ifilter_tags(matches=lambda node:
            check_tag_class(node,'span',['we_file_info2'])):
                m = duration_size_info_pattern.search(size_info.contents.strip_code())
                if m:
                    file_size_str = m.group(1)
                    file_len_duration = m.group(2)
                    self.pageTriples.add( (file_URI,
                                           sorg['contentSize'],
                                           rdflib.Literal(file_size_str,datatype=sorg['Text'])) )
                    if format_hms_duration(file_len_duration):
                        self.pageTriples.add ((file_URI,
                                               sorg['duration'],
                                               rdflib.Literal(format_hms_duration(file_len_duration),
                                                              datatype=sorg['Duration'])))
                    else:
                        self.pageTriples.add( (file_URI,
                                               local['numberOfPages'],
                                               rdflib.Literal(file_len_duration,datatype=sorg['Number'])) )
            for div_we_file_info in div_we_file.contents.ifilter_tags(
                    matches=lambda node: check_tag_class(node, 'div', ['we_file_info'])):
                # print(div_we_file_info)
                for span_details in div_we_file_info.contents.ifilter_tags(
                        matches=lambda node: check_tag_class(node, 'span', ['mh555'])):
                    for file_format_link in span_details.contents.ifilter_wikilinks(
                            matches='IMSLP:File formats'):
                        self.pageTriples.add((file_URI,
                                              sorg['encodingFormat'],
                                              rdflib.Literal(file_format_link.text.strip_code(),
                                                             datatype=sorg['Text'])))
                    for wikilink in span_details.contents.ifilter_wikilinks(matches='User:.*'):
                        self.pageTriples.add((file_URI,
                                         local['uploadedBy'],
                                         rdflib.URIRef(get_url_for_wikipage(imslpBase, wikilink.title))))
                        self.pageTriples.add((rdflib.URIRef(get_url_for_wikipage(imslpBase, wikilink.title)),
                                                            rdflib.RDF.type,
                                                            sorg['Person']))
                    m = uploadDatePattern.search(str(span_details))
                    if m:
                        uploadDate = dateparser.parse(str(m.group(1)))
                        self.pageTriples.add((file_URI,
                                         sorg['uploadDate'],
                                         rdflib.Literal(format_date(uploadDate), datatype=sorg['Date'])))
                    m = fileDetailPattern.search(str(span_details))
                    # Not sure what to do with this info
                    if m:
                        actType = m.group(1)
                        actPerson = m.group(2)
            self.process_edition_info_table(parentTag, file_URI)

    def process_edition_info_table(self, parentTag, file_URI):
        for outer_edition_info_table in parentTag.contents.ifilter_tags(
                matches=lambda node: check_tag_class(node, 'table', classesToMatch=['we_edition_info'])):
            innerTable = outer_edition_info_table.contents.filter_tags(
                matches=lambda node: node.tag == 'table')
            if innerTable:
                tbl = iterate_table_key_value_pairs(innerTable[0])
            else:
                tbl = iterate_table_key_value_pairs(outer_edition_info_table)
            for field_name, field_value in tbl:
                field_name = field_name.strip_code()
                if field_name == 'Arranger':
                    self.pageTriples.add((file_URI,
                                     sorg['musicArrangement'],
                                     self.pageURI))
                    # Only want the first one of these
                    wikilink = next(field_value.ifilter_wikilinks(), None)
                    if wikilink:
                        self.pageTriples.add((file_URI,
                                         sorg['creator'],
                                         rdflib.URIRef(get_url_for_wikipage(imslpBase, wikilink.title))))
                        self.pageTriples.add((rdflib.URIRef(get_url_for_wikipage(imslpBase, wikilink.title)),
                                              rdflib.RDF.type,
                                              sorg['Person']))
                    else:
                        self.pageTriples.add((file_URI,
                                         sorg['creator'],
                                         rdflib.URIRef(get_url_for_wikipage(imslpBase, wiki_uri_quote(
                                             field_value.strip_code())))))
                        self.pageTriples.add((rdflib.URIRef(get_url_for_wikipage(imslpBase, wiki_uri_quote(
                                             field_value.strip_code()))),
                                              rdflib.RDF.type,
                                              sorg['Person']))
                if field_name == 'Copyright':
                    wikilink = next(field_value.ifilter_wikilinks(), None)
                    if wikilink:
                        self.pageTriples.add((file_URI,
                                         sorg['license'],
                                         rdflib.URIRef(get_url_for_wikipage(imslpBase, wikilink.title))))
                    else:
                        self.pageTriples.add((file_URI,
                                         sorg['license'],
                                         rdflib.URIRef(get_url_for_wikipage(imslpBase,
                                                                            wiki_uri_quote(
                                                                            field_value.strip_code())))))
                if field_name == 'Publisher. Info.':
                    self.pageTriples.add((file_URI,
                                     local['publicationInfo'],
                                     rdflib.Literal(field_value.strip_code(),
                                                    datatype=sorg['Text'])))
                if field_name == 'Misc. Notes':
                    self.pageTriples.add((file_URI,
                                     local['additionalInfo'],
                                     rdflib.Literal(field_value.strip_code(), datatype=sorg['Text']))
                                    )
                if field_name == 'Editor':
                    wikilink = next(field_value.ifilter_wikilinks(), None)
                    if wikilink:
                        self.pageTriples.add((file_URI,
                                         sorg['editor'],
                                         rdflib.URIRef(
                                             get_url_for_wikipage(imslpBase, wikilink.title))))
                        self.pageTriples.add((rdflib.URIRef(get_url_for_wikipage(imslpBase, wikilink.title)),
                                              rdflib.RDF.type,
                                              sorg['Person']))
                    else:
                        self.pageTriples.add((file_URI,
                                         sorg['editor'],
                                         rdflib.URIRef(get_url_for_wikipage(imslpBase,
                                                                            wiki_uri_quote(
                                                                            field_value.strip_code())))))
                        self.pageTriples.add((rdflib.URIRef(get_url_for_wikipage(imslpBase,
                                                                                 wiki_uri_quote(
                                                                                 field_value.strip_code()))),
                                              rdflib.RDF.type,
                                              sorg['Person']))
                if field_name == 'Language':
                    wiki_language_link = rdflib.URIRef(get_url_for_wikipage(wikipediaBase,
                                                                            '{}_language'.format(
                                                                                field_value.strip_code())))
                    self.pageTriples.add((file_URI,
                                          sorg['inLanguage'],
                                          wiki_language_link))
                    self.pageTriples.add((wiki_language_link,
                                          rdflib.RDF.type,
                                          sorg['Language']))
                #if field_name == 'Translator':
                #    print('Translator:{}'.format(field_value))
                #if field_name == 'Copyist':
                #    print('Copyist:{}'.format(field_value))
                #if field_name == 'Scanner':
                #    print('Scanner:{}'.format(field_value))

    def get_triples_from_page(self):
        for node in self.page_wikitext.ifilter():
            if type(node) == mwp.nodes.Tag:
                if node.tag == 'div' and node.has('id') and node.get('id').value == 'wpscore_tabs':
                    self.get_triples_from_scores(node)
                if node.tag == 'div' and node.has('id') and node.get('id').value == 'wpaudio_tabs':
                    self.get_triples_from_audio_files(node)
                if check_tag_class(node,'div',['wi_body']):
                    self.get_triples_from_geninfo_section(node)
            if type(node) == mwp.nodes.Wikilink:
                if category_link_title_pattern.search(node.title.strip_code()):
                    self.get_triples_from_category_link(node)
            if type(node) == mwp.nodes.Text:
                if 'REDIRECT' in node.value:
                    redirect_link = self.page_wikitext.get(self.page_wikitext.index(node) + 1)
                    self.pageTriples.add((self.pageURI,
                                          sorg['sameAs'],
                                          rdflib.URIRef(get_url_for_wikipage(imslpBase,
                                                                             redirect_link.title))))

    def get_triples_from_youtube_search(self):
        try:
            youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                            developerKey=DEVELOPER_KEY,cache_discovery=False)

            video_categories = video_categories_list(youtube, part='snippet', regionCode='US')
            categoryID_lookup = {video_category_info['id']: video_category_info['snippet']['title']
                                 for video_category_info in video_categories['items']}
            search_args = {}
            search_args['q'] = self.pagetitle
            search_args['type'] = 'video'
            search_args['max_results'] = MAX_YOUTUBE_RESULTS
            youtube_search_request = youtube.search().list(q=search_args['q'], part='id,snippet',
                                     maxResults=search_args['max_results'],type=search_args['type'])
            search_results = youtube_search_request.execute()
            #https://www.youtube.com/results?search_query=<search query here>
            browser_search_uri = rdflib.URIRef(urlunparse(('https', 'www.youtube.com', 'results', None,
                                                          urlencode((('search_query', self.pagetitle),))
                                                          # Careful! Note trailing comma
                                                          , None)))

            self.pageTriples.add((self.pageURI,
                                 local['youtubeSearchURL'],
                                 browser_search_uri))
            self.pageTriples.add((self.pageURI,
                                 local['youtubeAPIRequestURL'],
                                 rdflib.URIRef(youtube_search_request.uri)))
            for item in search_results['items']:
                try:
                    video_result = videos_list_by_id(youtube,
                                                     part='id,snippet,contentDetails,topicDetails',
                                                     id=item['id']['videoId'])
                except KeyError as e:
                    logging.exception("No videoId in video_result")
                for vid_result_details in video_result['items']:
                    #watch video URL looks like https://www.youtube.com/watch?v=<video_id_here>
                    video_URI = rdflib.URIRef(urlunparse(('https', 'www.youtube.com', 'watch', None,
                                                          urlencode((('v', vid_result_details['id']),))
                                                          # Careful! Note trailing comma
                                                          , None)))
                    self.pageTriples.add((video_URI,
                                         rdflib.RDF.type,
                                         sorg['VideoObject']))
                    #Forgot this before. It's kind of important...
                    self.pageTriples.add((video_URI,
                                          sorg['encodesCreativeWork'],
                                          self.pageURI))
                    try:
                        # from snippet
                        self.pageTriples.add((video_URI,
                                 sorg['datePublished'],
                                 rdflib.Literal(vid_result_details['snippet']['publishedAt'],
                                                datatype=sorg['Date'])))
                    except KeyError as e:
                        logging.exception('No key in vid_result_details')


                        self.pageTriples.add((video_URI,
                                 sorg['name'],
                                 rdflib.Literal(vid_result_details['snippet']['localized']['title'],
                                                datatype=sorg['Text'])))
                    except KeyError as e:
                        logging.exception('No key in vid_result_details')

                    try:
                        self.pageTriples.add((video_URI,
                                 sorg['description'],
                                 rdflib.Literal(vid_result_details['snippet']['localized']['description'],
                                                datatype=sorg['Text'])))
                    except KeyError as e:
                        logging.exception('No key in vid_result_details')

                    try:
                        self.pageTriples.add((video_URI,
                                 sorg['thumbnailUrl'],
                                 rdflib.URIRef(vid_result_details['snippet']['thumbnails']['default']['url'])))
                    except KeyError as e:
                        logging.exception('No key in vid_result_details')

                    try:
                        self.pageTriples.add((video_URI,
                                 sorg['category'],
                                 rdflib.Literal(categoryID_lookup[vid_result_details['snippet']['categoryId']],
                                                datatype=sorg['Text'])))
                    except KeyError as e:
                        logging.exception('No key in vid_result_details')


                    try:
                        for tag in vid_result_details['snippet']['tags']:#apparently these don't always exist
                            self.pageTriples.add((video_URI,
                                     sorg['keywords'],
                                     rdflib.Literal(tag, datatype=sorg['Text'])))
                    except KeyError as e:
                        logging.exception('No key in vid_result_details')

                        # From contentDetails
                    try:
                        self.pageTriples.add((video_URI,
                                 sorg['duration'],
                                 rdflib.Literal(vid_result_details['contentDetails']['duration'],
                                                datatype=sorg['Duration'])))
                    except KeyError as e:
                        logging.exception('No key in vid_result_details')

                        # from topicDetails
                    try:
                        for topic in vid_result_details['topicDetails']['topicCategories']:
                            self.pageTriples.add((video_URI,
                                     local['additionalInfo'],
                                     rdflib.URIRef(topic)))
                    except KeyError as e:
                        logging.exception('No key in vid_result_details')

        except HttpError as e:
            print('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))