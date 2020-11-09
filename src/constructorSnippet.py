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