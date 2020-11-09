    def get_triples_from_page(self):
        for node in self.page_wikitext.ifilter():
            if type(node) == mwp.nodes.Tag:
                if node.tag == 'div' and node.has('id')
                and node.get('id').value == 'wpscore_tabs':
                    self.get_triples_from_scores(node)
                if node.tag == 'div' and node.has('id')
                and node.get('id').value == 'wpaudio_tabs':
                    self.get_triples_from_audio_files(node)
                if check_tag_class(node,'div',['wi_body']):
                    self.get_triples_from_geninfo_section(node)
            if type(node) == mwp.nodes.Wikilink:
                if category_link_title_pattern.search(node.title.strip_code()):
                    self.get_triples_from_category_link(node)
            if type(node) == mwp.nodes.Text:
                if 'REDIRECT' in node.value:
                    redirect_link = self.page_wikitext.get(
                    self.page_wikitext.index(node) + 1)
                    self.pageTriples.add((self.pageURI,
                                          sorg['sameAs'],
                                          rdflib.URIRef(
                                          get_url_for_wikipage(imslpBase,
                                          redirect_link.title))))