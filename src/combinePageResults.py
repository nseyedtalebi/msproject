import IMSLPtoRDF as imrdf
import rdflib
import os.path
from multiprocessing import Pool

inputDir = 'C:\\Users\\NiMo3\\Documents\\msproject\\IMSLP_dump\\1ktest_out'
outputFile = r'C:\Users\NiMo3\Documents\msproject\blazegraph\1k_testset.n3'
def readgraph(inputPath):
    return rdflib.Graph().parse(source=inputPath,format='n3')


if __name__ == '__main__':
    mpool = Pool(12)
    outputGraphList = mpool.map(readgraph,(os.path.join(inputDir,file) for file in os.listdir(inputDir)))
    mpool.close()
    mpool.join()
    testsetGraph = rdflib.Graph()
    for graph in outputGraphList:
        testsetGraph+=graph
    testsetGraph.serialize(outputFile, format='n3')

