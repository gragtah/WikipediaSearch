#! /usr/bin/python
#
# Stephen Poletto (spoletto)
# CSCI1580 - Web Search
# Spring 2011 - Brown University
#
# Reads in a list of queries
# and returns matching documents
# using the provided index file.

from bool_parser import bool_expr_ast
from positionalIndex import *
from porterStemmer import *
from kgramIndex import *
import marshal
import string
import bsddb
import math
import sys
import re
import os

K_TOP_DOCUMENTS = 10

class QuerySideIndex:
    
    def __init__(self, file, term_to_file_position):
        self.file = file
        self.term_to_file_position = term_to_file_position
    
    def lookup(self, term):
        if term in self.term_to_file_position:
            (start, stop) = self.term_to_file_position[term]
            self.file.seek(int(start), 0)
            return marshal.loads(self.file.read(int(stop)-int(start)))
        
if (len(sys.argv) != 7):
    print ""
    print "usage: queryIndex <index> <stopwords> <titleindex> <kgramIndex> <outgoingLinks> <pageRank>"
    print ""
    sys.exit()

for i in range(1, 7):
    if not os.path.exists(sys.argv[i]):
        print ""
        print "File " + sys.argv[i] + " does not exist."
        print ""
        sys.exit()

# Load the index:
indexFile = open(sys.argv[1], 'r')
term_to_file_position_start = int(indexFile.readlines()[-1])
term_to_file_position_end = indexFile.tell()
indexFile.seek(term_to_file_position_start, 0)
term_to_file_position = marshal.loads(indexFile.read(term_to_file_position_start - term_to_file_position_end))
index = QuerySideIndex(indexFile, term_to_file_position)

# Load the k-gram index
kgramFile = open(sys.argv[4])
k_gram = KGramIndex(marshal.loads(kgramFile.read()))
kgramFile.close()

# Load the page rank:
pageRankFile = open(sys.argv[6])
docIDToPageRank = {}
currDocID = 0
for line in pageRankFile:
    line = line.rstrip('\n')
    docIDToPageRank[currDocID] = float(line)
    currDocID += 1
pageRankFile.close()

# Load the outgoing links
outgoingLinksFile = open(sys.argv[5])
docIDToOutgoingLinks = {}
currDocID = 0
for line in outgoingLinksFile:
    line = line.rstrip('\n')
    docIDToOutgoingLinks[currDocID] = line
    currDocID += 1
outgoingLinksFile.close()

# Read total number of documents in collection. 
titleIndexFile = open(sys.argv[3])
documents_in_collection = 0
docIDToTitle = {}
for line in titleIndexFile:
    line = line.rstrip("\n")
    docID = int(line.split(" ")[0])
    title = " ".join(line.split(' ')[1:])
    docIDToTitle[docID] = title.lower()
    documents_in_collection += 1
titleIndexFile.close()

# Read in the stop words
stopWordsFile = open(sys.argv[2], "r")
stopWords = []
for stop in stopWordsFile.readlines():
    word = stop.rstrip("\n")
    stopWords.append(word)
stopWords = set(stopWords)

# Build the Porter Stemmer
stemmer = PorterStemmer()

def score_matching_docs(setOfDocIDs, term_to_idf, term_to_postings_list):
    scores = [0.0] * len(setOfDocIDs)
    currDoc = 0
    for docID in setOfDocIDs:
        score = 0.0
        for term in term_to_idf:
            idf = term_to_idf[term]
            if idf == 0:
                # Search term does not occur in corpus
                continue
            result = term_to_postings_list[term]
            if result != None and docID in result:
                weight = result[docID][-1]
                score += (weight * idf)
                 
        scores[currDoc] = ((score, docID))
        currDoc += 1
    
    return scores

def ranked_results(setOfDocIDs, term_to_idf, num_top_docs):
    # Cache term postings list to avoid hitting index.
    term_to_postings_list = {}
    for term in term_to_idf:
        term_to_postings_list[term] = index.lookup(term)
    
    scores = score_matching_docs(setOfDocIDs, term_to_idf, term_to_postings_list)
    
    # Sorted by score, with ties broken by docID.
    scores.sort(reverse = True)

    upper_bound = num_top_docs * 3 
    # Consider three times the desired set size
    if (len(scores) < 3 * num_top_docs):
        upper_bound = len(scores)
    
    scores = [scores[i] for i in range(0, upper_bound)]
    
    # Find the highest score and find the highest
    # page rank value. Scale up the page rank values
    # to be a fraction of the tf-idf weightings.
    max_tf_idf = 0
    max_page_rank = 0
    for score_tuple in scores:
        score = score_tuple[0]
        docID = int(score_tuple[1])
        if score > max_tf_idf:
            max_tf_idf = score
        if docIDToPageRank[docID] > max_page_rank:
            max_page_rank = docIDToPageRank[docID]
            
    # Avoid divide-by-zero errors
    if max_page_rank == 0:
        max_page_rank = 1
        
    page_rank_factor = max_tf_idf / max_page_rank
    
    for i in range(0, len(scores)):
        docID = scores[i][1]
        added_value = 0.0
        for term in term_to_idf:
            idf = term_to_idf[term]
            tf_idf_weight = 0
            if idf == 0:
                # Search term does not occur in corpus
                continue
            result = term_to_postings_list[term]
            if result != None and docID in result:
                weight = result[docID][-1]
                tf_idf_weight = weight * idf

            if term in docIDToTitle[int(docID)]:
                # If the term is in the title of the document,
                # upweight accordingly:
                print term + " in " + docIDToTitle[int(docID)]
                added_value += tf_idf_weight * 4
               
            if term in docIDToOutgoingLinks[int(docID)]:
                added_value += tf_idf_weight
                
        print "adding " + str(page_rank_factor * docIDToPageRank[int(docID)]) + " for page rank."
        print "adding " + str(added_value) + " added value"
        scores[i] = (scores[i][0] + page_rank_factor * docIDToPageRank[int(docID)] + added_value, scores[i][1])
    
    scores.sort(reverse = True)
    upper_bound = num_top_docs
    if (len(scores) < num_top_docs):
        upper_bound = len(scores)
    
    # Return the doc IDs
    return [scores[i][1] for i in range(0, upper_bound)]

def wildcard_ranked_results(matchingDocIDs, queryTermToDocIDToWildcardWeight, term_to_idf):
    scores = []
    for docID in matchingDocIDs:
        score = 0.0
        for term in term_to_idf:
            weight = queryTermToDocIDToWildcardWeight[term][docID]
            score += weight * term_to_idf[term]
        scores.append((score, docID))

    scores.sort(reverse = True)
    upper_bound = K_TOP_DOCUMENTS
    if (len(scores) < K_TOP_DOCUMENTS):
        upper_bound = len(scores)    
    #return [scores[i][1] for i in range(0, len(scores))]
    return [scores[i][1] for i in range(0, upper_bound)]

def wildcard_weight(docIDs, terms):
    # Cache term postings list to avoid hitting index.
    term_to_postings_list = {}
    for term in terms:
        term_to_postings_list[term] = index.lookup(term)
    
    docIDToWildcardWeight = {}
    bestIDF = 0.0
    # First find the largest IDF of all the
    # terms that match the wildcard word.
    for term in terms:
        term_idf = calculate_idf_for_term(term)
        if term_idf > bestIDF:
            bestIDF = term_idf

    # Then, for each document, find the weight
    # of the wildcard word for the document by
    # finding the maxmial weight in the matching set.
    for docID in docIDs:
        best_weight = 0.0
        for term in terms:
            if docID in term_to_postings_list[term]:
                weight = term_to_postings_list[term][docID][-1]
                if weight > best_weight:
                    best_weight = weight
        docIDToWildcardWeight[docID] = best_weight

    # This returns the mapping of document ID to its
    # corresponding weight for this particular query
    # term. bestIDF is the weight of this query term.
    # This function should be called for each term
    # in a phrase query. Then, a dictionary of
    # query term -> bestIDF should be created to
    # be passed into wildcard_ranked_results.
    return docIDToWildcardWeight, bestIDF

def print_docIDs(topDocuments):
    if len(topDocuments) > 0:
        for id in topDocuments[0:-1]:
            sys.stdout.write(docIDToTitle[int(id)] + ", ")
            #sys.stdout.write(id + " ")
        sys.stdout.write(docIDToTitle[int(topDocuments[-1])])
        #sys.stdout.write(topDocuments[-1])
    sys.stdout.write('\n')

# Print the results to stdout
def print_ranked_results(setOfDocIDs, term_to_idf):
    print_docIDs(ranked_results(setOfDocIDs, term_to_idf, K_TOP_DOCUMENTS))
    

# For processing one word queries.
# Simply look up the word in the
# dictionary, and print the postings
# list of document IDs.

def processOWQ_private(query):
    docIDs = []
    docIDToPositions = index.lookup(query)
    if docIDToPositions != None:
        docIDs = docIDToPositions.keys()
    return set(docIDs)

def processOWQ(query, term_to_idf):
    print_ranked_results(processOWQ_private(query), term_to_idf)

# For processing phrase queries.
# Each term in the keyword list
# must occur within a single
# document, so first we take
# the intersection of documents
# from the postings lists associated
# with each term. Then, once we have
# our candidate documents, we check
# the positional indices to make sure
# the phrase appears as specified
# in the query.

def docs_containing_all_terms_in_list(keywordList):
    candidateDocs = None
    wordToDocList = {}
    for word in keywordList:
        docIDToPositions = index.lookup(word)
        if docIDToPositions != None:
            # Cache the postings list for each word.
            wordToDocList[word] = docIDToPositions
            docIDs = docIDToPositions.keys()
            # Initialize the set of candidate docs.
            if candidateDocs == None:
                candidateDocs = set(docIDs)
            candidateDocs = candidateDocs.intersection(set(docIDs))
        else:
            return None, None
    return candidateDocs, wordToDocList

def docs_containing_all_terms_in_order(keywordList, candidateDocs, wordToDocList):
    if candidateDocs == None:
        return set([])
    # Candidate documents contain every word in the phrase.
    successfulDocuments = []
    for document in candidateDocs:
        positionsOfWordPrior = None
        for word in keywordList:
            positionsOfWord = wordToDocList[word][document]
            # First word in the query
            if positionsOfWordPrior == None:
                positionsOfWordPrior = positionsOfWord
            else:
                newPositionsOfWordPrior = []
                for position in positionsOfWord:
                    if position-1 in positionsOfWordPrior:
                        newPositionsOfWordPrior.append(position)
                positionsOfWordPrior = newPositionsOfWordPrior
                if len(positionsOfWordPrior) == 0:
                    break
        # If we made it through the full phrase with the last
        # term succesfully matched up with a prior term, we
        # know the document contained the entire phrase.
        if len(positionsOfWordPrior) > 0:
            successfulDocuments.append(document)
    return successfulDocuments

def processPQ_private(keywordList, term_to_idf):
    candidateDocs, wordToDocList = docs_containing_all_terms_in_list(keywordList)
    if candidateDocs == None:
        return None
    return docs_containing_all_terms_in_order(keywordList, candidateDocs, wordToDocList)
    
def processPQ(keywordList, term_to_idf):
    successfulDocuments = processPQ_private(keywordList, term_to_idf)
    if successfulDocuments == None:
        sys.stdout.write('\n')
        return
    
    # Print results
    print_ranked_results(successfulDocuments, term_to_idf)

# For processing free text queries.
# Simply look up each word in the
# dictionary, and print the union
# of documents from the associated
# postings lists.

def processFTQ(keywordList, term_to_idf):

    ranked_results_list = []
    find_more_docs_count = K_TOP_DOCUMENTS
    
    # Incorporate proximity weighting. First
    # run the entire query as a phrase query.
    successfulDocuments = processPQ_private(keywordList, term_to_idf)
    if successfulDocuments != None:
        ranked_results_list = ranked_results(successfulDocuments, term_to_idf, K_TOP_DOCUMENTS)
        find_more_docs_count -= len(ranked_results_list)
        
    # TODO: If that didn't give us enough results,
    # try 4-word phrases, 3-word phrases, etc.
    if find_more_docs_count > 0:
        pass
    
    if find_more_docs_count > 0:
        # There weren't enough documents with immediate proximity.
        # Fall back on documents that contain any of the terms.
        resultDocs = set([])
        for word in keywordList:
            docIDToPositions = index.lookup(word)
            if docIDToPositions != None:
                docIDs = docIDToPositions.keys()
                resultDocs = resultDocs.union(set(docIDs))
        fallback_docs = (ranked_results(resultDocs, term_to_idf, K_TOP_DOCUMENTS))
        for doc in fallback_docs:
            if doc not in ranked_results_list and find_more_docs_count > 0:
                ranked_results_list.append(doc)
                find_more_docs_count -= 1

    print_docIDs(ranked_results_list)

# For processing boolean queries.
# The AST generated by the TA
# support code will be passed in.
# The first element of the AST is
# always the operation. The subsequent
# items may be stings (single word
# base case) or tuples, which require
# recursive evaluation.

def processBQ_private(boolean_ast):
    results = None
    operation = boolean_ast[0]
    for operand in boolean_ast[1]:
        matches = set([])
        # Tuples require further parsing
        if isinstance(operand, tuple):
            matches = processBQ_private(operand)
        else:
            stemmed = stemmedQuery(operand)
            if not len(stemmed) < 1:
                # Word is not a stop word.
                matches = processOWQ_private(stemmed[0])
        if results == None:
            results = matches
        if operation == "OR":
            results = results.union(matches)
        elif operation == "AND":
            results = results.intersection(matches)
    return results

def processBQ(boolean_ast, term_to_idf):
    results = processBQ_private(boolean_ast)
    print_ranked_results(results, term_to_idf)


def terms_matching_wildcard_query(possible_terms, query):
    regex = re.compile("^" + query.replace('*', '(.*)') + "$")
    matches = []
    for term in possible_terms:
        if len(regex.findall(term)) > 0:
            matches.append(term)
    return matches

# For processing single word wildcard queries.
def processWQ(query, term_to_idf):
    query = stemmer.stem(query, 0, len(query)-1)
    possible = k_gram.terms_from_wildcard(query)
    results = terms_matching_wildcard_query(possible, query)
    # First, find docs that match.
    matchingDocIDs = set([])
    for word in results:
        docIDToPositions = index.lookup(word)
        if docIDToPositions != None:
            docIDs = docIDToPositions.keys()
            matchingDocIDs = matchingDocIDs.union(set(docIDs))

    queryTermToDocIDToWildcardWeight = {}
    docIDToWildcardWeight, bestIDF = wildcard_weight(matchingDocIDs, results)
    queryTermToDocIDToWildcardWeight[query] = docIDToWildcardWeight
    term_to_idf = {}
    term_to_idf[query] = bestIDF
    
    print_docIDs(wildcard_ranked_results(matchingDocIDs, queryTermToDocIDToWildcardWeight, term_to_idf))

wildcardPhraseResults = set([])

def removeOperatorsFromString(string, operators):
    for op in operators:
        string = string.replace(op, "")
    return string

def stemmedQuery(query):
    stemmed = removeOperatorsFromString(query, ["AND", "OR", "(", ")", "\""])
    stemmed = stemmed.lower()
    stemmed = re.compile(r'\b[a-z0-9]+\b').findall(stemmed)
    outputStream = []
    for word in stemmed:
        if word not in stopWords:
            outputStream.append(stemmer.stem(word, 0, len(word)-1))
    return outputStream

def calculate_idf_for_term(term):
    if index.lookup(term) != None:
        doc_frequency = len(index.lookup(term)) + 0.0
        return math.log(documents_in_collection/doc_frequency, 10)
    return 0

def processQuery(query):
    term_to_idf = {}
    stemmed = stemmedQuery(query)
    for term in stemmed:
       term_to_idf[term] = calculate_idf_for_term(term)

    tmpquery = query.replace('*', '')
    term_count = len(re.compile(r'\b\w+\b').findall(tmpquery))
    
    if query.find('*') != -1:
        # Must be dealing with a wildcard query,
        # since a * exists in the query.
        if term_count == 1:
            # Single word wildcard query.
            processWQ(query, term_to_idf)
            return
        else:
            # We're not handling wildcard phrase queries
            sys.stdout.write("\n")
            return     
    if len(stemmedQuery(query)) < 1:
        # Search query has zero terms!
        sys.stdout.write("\n")
        return
    
    if term_count == 1:
        # Single word query:
        processOWQ(stemmed[0], term_to_idf)
        return
    elif query.find("\"") != -1:
        processPQ(stemmed, term_to_idf)
        return
    elif query != bool_expr_ast(query):
        # We have a bool AST; must be a BQ
        processBQ(bool_expr_ast(query), term_to_idf)
        return
    else:
        processFTQ(stemmed, term_to_idf)
        return

# Main run loop.
# Read input from stdin and process
# each incoming query.
while True:
    try:
        query = raw_input()
        processQuery(query.rstrip('\n'))
    except EOFError:
        break
