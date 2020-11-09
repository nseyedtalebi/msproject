    def process_edition_info_table(self, parentTag, file_URI):
        for outer_edition_info_table in parentTag.contents.ifilter_tags(
                matches=lambda node: check_tag_class(node, 
                'table',
                classesToMatch=['we_edition_info'])):
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
                                         rdflib.URIRef(get_url_for_wikipage(
                                         imslpBase, wikilink.title))))
                        self.pageTriples.add((rdflib.URIRef(get_url_for_wikipage(
                        imslpBase, wikilink.title)),
                                              rdflib.RDF.type,
                                              sorg['Person']))
                    else:
                        self.pageTriples.add((file_URI,
                                         sorg['creator'],
                                         rdflib.URIRef(get_url_for_wikipage(
                                         imslpBase, wiki_uri_quote(
                                             field_value.strip_code())))))
                        self.pageTriples.add((rdflib.URIRef(
                                             get_url_for_wikipage(
                                             imslpBase,
                                             wiki_uri_quote(field_value.strip_code()))),
                                              rdflib.RDF.type,
                                              sorg['Person']))