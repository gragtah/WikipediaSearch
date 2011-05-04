#! /usr/bin/python
#
# Stephen Poletto (spoletto)
# Peter Wilmot (pbwilmot)
# CSCI1580 - Web Search
# Spring 2011 - Brown University
#
# Given a collection of documents
# generates the adjacency matrix A 
# of the web graph. If there is a 
# hyperlink from page i to page j, 
# then line i of the output file will
# contain page j's docID number.

import string
import sys
import re
    
if (len(sys.argv) != 3):
    print ""
    print "usage: createAdjacencyMatrix <collection> <outputfile>"
    print ""
    sys.exit()

# Initial setup:
CHUNK_SIZE = 100000
collectionFile = open(sys.argv[1], "r")
outputFile = open(sys.argv[2], 'wb')

# We'll need the ID associated with each
# doc title, since the links will be given
# as doc titles.
docTitleToID = {}

# Remember the list of titles linked to
# from each document, for writing out to
# file after the entire collection has 
# been read.
docIDToLinkedTitles = {}

def process_page(page):
    # We need to extract wiki links of the form [[Target_Link]].
    links = re.compile(r'\[\[((.)*?)\]\]', re.DOTALL).findall(page)
    stemmed_links = [None] * len(links)
    for i in range(0, len(links)):
        link = links[i][0]
        # The page title that the link is pointing to is the
        # sequence of characters before the first occurrence
        # of either # or | in [[Target_Link]]
        stemmed_links[i] = re.split('\||\#', link)[0]

    id = re.compile(r'<id>(\d*)</id>').findall(page)[0]
    title = re.compile(r'<title>(.*?)</title>', re.DOTALL).findall(page)[0]
    
    # Store the doc title -> ID mapping, and the doc ID -> links 
    docTitleToID[title] = id;
    docIDToLinkedTitles[id] = stemmed_links
                   
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
               
# At this point, we've processed all the pages
# in the collection, so we can start writing out
# the adjacency matrix to file.
for id in docIDToLinkedTitles:
    for link in docIDToLinkedTitles[id]:
        if link in docTitleToID:
            outputFile.write(str(docTitleToID[link]) + " ")
    outputFile.write("\n")

# Cleanup
outputFile.close()


