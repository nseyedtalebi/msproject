# -*- coding: utf-8 -*-
import IMSLPtoRDF as imrdf
import rdflib
import os.path
import logging
from multiprocessing import Pool
logging.basicConfig(filename='10k_test_2.log',level=logging.DEBUG)
progressFile = 'run_progress.txt'
inputDir = "C:\\Users\\NiMo3\\Documents\\msproject\\IMSLP_dump\\rand_testset_10k"
outputDir = 'C:\\Users\\NiMo3\\Documents\\msproject\\IMSLP_dump\\10ktest_out'
#inputDir = "D:\\IMSLP_dump\\rand_testset_1"

def extract_triples(wikitext_file):
    with open(os.path.join(inputDir,wikitext_file),'r',encoding='UTF-8') as wikitextIn:
        try:
            currentPage = imrdf.IMSLPWorkPage(wikitextIn)
            #currentPage.get_triples_from_page()
            currentPage.get_triples_from_youtube_search()
            return currentPage.pageTriples
        except Exception as e:
            logging("Exception when processing file: {}".format(e))

if __name__ == '__main__':
    mpool = Pool(8)
    res = mpool.map(extract_triples, os.listdir(inputDir))
    mpool.close()
    mpool.join()
    outputGraph = rdflib.Graph()
    for p in res:
        outputGraph += p
    outputGraph.serialize(destination=os.path.join(outputDir,'test_out_10k_vids.ttl'),format='ttl')

