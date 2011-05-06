#! /usr/bin/python
#
# Stephen Poletto (spoletto)
# CSCI1580 - Web Search
# Spring 2011 - Brown University
#
# Given a list of stop words and
# a collection of documents, generates
# an inverted index and associated
# title index.

from positionalIndex import *
from porterStemmer import *
from kgramIndex import *
import marshal
import string
import bsddb
import math
import sys
import re
    
CHUNK_SIZE = 100000
    
if (len(sys.argv) != 9):
    print ""
    print "usage: createIndex <collection> <index> <stopWords> <titleIndex> <kgramIndex> <outgoingLinks> <features> <vecrepOutput>"
    print ""
    sys.exit()

# Initial setup:
stopWordsFile = open(sys.argv[3], "r")
collectionFile = open(sys.argv[1], "r")
titleIndexFile = open(sys.argv[4], 'wb')
outgoingLinksFile = open(sys.argv[6], 'wb')
featuresFile = open(sys.argv[7], 'r')
vecrepFile = open(sys.argv[8], 'wb')
stemmer = PorterStemmer()
index = PositionalIndex()
k_gram = KGramIndex()

stopWords = []
for stop in stopWordsFile.readlines():
    word = stop.rstrip("\n")
    stopWords.append(word)
stopWords = set(stopWords)
stopWordsFile.close()

features = {}
featureID = 0
for feature in featuresFile.readlines():
    feature = feature.rstrip("\n")
    features[feature] = featureID
    featureID += 1
featuresFile.close()

def process_page(page):
    
    # Extract wiki links of the form [[Target_Link]].
    # Wikipedia pages are probably related to the artciles they
    # link to. So if the user's query contains the text of an
    # outgoing link, we will weight this document higher.
    links = re.compile(r'\[\[((.)*?)\]\]', re.DOTALL).findall(page)
    for i in range(0, len(links)):
        link = links[i][0].lower()
        link = string.replace(link, '\|', ' ')
        link = string.replace(link, '\#', ' ')
        terms = re.compile(r'\b[a-z0-9]+\b').findall(link)
        for term in terms:
            if term not in stopWords:
                outgoingLinksFile.write(stemmer.stem(term, 0, len(term)-1) + " ")
    outgoingLinksFile.write('\n')
    
    docID = re.compile(r'<id>(\d*)</id>').findall(page)[0]
    title = re.compile(r'<title>(.*?)</title>', re.DOTALL).findall(page)[0]
    text = re.compile('<text>((.)*?)</text>', re.DOTALL).findall(page)[0][0]
    text = title + '\n' + text
    text = string.replace(text, '\r', ' ').lower()
    text = string.replace(text, '\t', ' ')
    text = string.replace(text, '\n', ' ')
    text = string.replace(text, '_', ' ')
    text = re.compile(r'\b[a-z0-9]+\b').findall(text)
    currWordNumber = 1
    term_to_occurrence_count = {}
    feature_id_to_occurrence_count = {}
    for word in text:
        if word not in stopWords:
            keyword = stemmer.stem(word, 0, len(word)-1)
            
            # Now check to see if the keyword is a feature we care about:
            if keyword in features:
                featureID = features[keyword]
                if featureID in feature_id_to_occurrence_count:
                    feature_id_to_occurrence_count[featureID] += 1
                else:
                    feature_id_to_occurrence_count[featureID] = 1
            
            term_to_occurrence_count[keyword] = term_to_occurrence_count.setdefault(keyword, 0) + 1
            if index.lookup(keyword) == None:
                k_gram.insert(keyword)
            index.insert(keyword, docID, currWordNumber)
            currWordNumber = currWordNumber + 1
    sum = 0.0
    for term_count in term_to_occurrence_count.values():
        sum += (term_count * term_count)
    divisor = math.sqrt(sum)
    
    for term in term_to_occurrence_count:
        weight = term_to_occurrence_count[term] / divisor
        index.dict[term][docID].append(weight)
    
    titleIndexFile.write(docID + " " + title + "\n")
    
    # Need to write out the vector representation as
    # d sum_d f_i:occ_i ...
    vecrepFile.write(str(docID) + " ")
    sum_d = 0
    for term_count in feature_id_to_occurrence_count.values():
        sum_d += (term_count * term_count)
    vecrepFile.write(str(sum_d) + " ")
    for featureID in feature_id_to_occurrence_count:
        vecrepFile.write(str(featureID) + ":" + str(feature_id_to_occurrence_count[featureID]) + " ")
    vecrepFile.write("\n")

# Main run loop.
# Read the collection in as chunks of data.
# Process the pages to build the index.
chunk = ""
while True:
    lines = collectionFile.readlines(CHUNK_SIZE)
    if not lines:
        # EOF
        break
    for line in lines:
        chunk = chunk + line
    before, found, page = chunk.partition("<page>")
    while found:
        page, found, after = page.partition("</page>")
        if found:
            process_page(page)
        else:
            chunk = "<page>" + page
            break
        before, found, page = after.partition("<page>")
collectionFile.close()
titleIndexFile.close() 
outgoingLinksFile.close()

# Write the k-gram index to disk
kgramIndexFile = open(sys.argv[5], 'wb')
kgramIndexFile.write(marshal.dumps(k_gram.dict))
kgramIndexFile.close()

# Write the main index out to disk
indexFile = open(sys.argv[2], 'wb')
term_to_file_position = {}
for term in index.dict.keys():
    start = indexFile.tell()
    indexFile.write(marshal.dumps(index.dict[term]))
    end = indexFile.tell()
    
    # Record the byte position in the file where
    # this term's posting list was written
    term_to_file_position[term] = (start, end)
    
# Write the term-> byte position dictionary to the end of the file.
start = indexFile.tell()
indexFile.write(marshal.dumps(term_to_file_position))
indexFile.write('\n')

# Record where the term-> byte position dictionary was written.
indexFile.write(str(start))
indexFile.close()

