# -*- coding: utf-8 -*-
import IMSLPtoRDF as imrdf
import rdflib
import os.path
import logging
logging.basicConfig(filename='10k_test.log',level=logging.DEBUG)
progressFile = 'run_progress.txt'
inputDir = "C:\\Users\\NiMo3\\Documents\\msproject\\IMSLP_dump\\rand_testset_1"
outputDir = 'C:\\Users\\NiMo3\\Documents\\msproject\\IMSLP_dump\\single_test'
#inputDir = "D:\\IMSLP_dump\\rand_testset_1"
outputGraph = rdflib.Graph()
try:
    with open(progressFile) as progressIn:
        startAt = int(progressIn.read())
except FileNotFoundError:
    startAt = 0

for idx,file in enumerate(sorted(os.listdir(inputDir)),start=startAt):
    print("Extracting triples from file {0}, named {1}".format(idx,file))
    with open(os.path.join(inputDir,file),'r',encoding='UTF-8') as wikitextIn:
        try:
            currentPage = imrdf.IMSLPWorkPage(wikitextIn)
            currentPage.get_triples_from_page()
            currentPage.get_triples_from_youtube_search()
        except Exception as e:
            logging("Exception when processing file {}".format(file))
        #currentPage.get_triples_from_geninfo_section()
        #currentPage.get_triples_from_scores()
        #currentPage.get_triples_from_audio_files()
        #currentPage.get_triples_from_categories()
    currentPage.pageTriples.serialize(destination=os.path.join(outputDir,'{}.n3'.format(file)), format='n3')
    #with open(progressFile,mode='w') as progress:
    #    progress.write(str(idx))
    #outputGraph += currentPage.pageTriples

#outputGraph.serialize(destination='./blazegraph/testset_10k.n3',format='n3')
