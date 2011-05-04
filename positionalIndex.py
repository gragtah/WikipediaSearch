#! /usr/bin/python
#
# Stephen Poletto (spoletto)
# CSCI1580 - Web Search
# Spring 2011 - Brown University
#
# For storing the index created
# by createIndex.py. Each node
# represents a particular keyword
# and has a dictionary 
# (docID->positions).

class PositionalIndex:
        
    def __init__(self, dict=None):
        if dict != None:
            self.dict = dict
        else:
            self.dict = {}
             
    def insert(self, keyword, docID, position):
        existingDocIDs = self.dict.setdefault(keyword, {})
        existingDocIDs.setdefault(docID, []).append(position)
        
    def lookup(self, keyword):        
        if keyword in self.dict:
            return self.dict[keyword]
        else:
            return None
