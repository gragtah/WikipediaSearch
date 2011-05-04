#! /usr/bin/python
#
# Stephen Poletto (spoletto)
# CSCI1580 - Web Search
# Spring 2011 - Brown University
#
import string

class KGramIndex:
        
    def __init__(self, dict=None):
        if dict != None:
            self.dict = dict
        else:
            self.dict = {}
             
    def append_to_dict(self, key, value):
        self.dict.setdefault(key,[]).append(value)
                  
    def insert(self, keyword):
        assert(len(keyword) > 0)
        # For the beginning of the word.
        # i.e. $a -> april
        self.append_to_dict('$' + keyword[0], keyword)
        
        for i in range(1, len(keyword)):
            self.append_to_dict(keyword[i-1] + keyword[i], keyword)
        
        # For the end of the word.
        # i.e. l$ -> april
        self.append_to_dict(keyword[-1] + '$', keyword)
        
        
    def terms_from_wildcard(self, wildcard):
        assert(len(wildcard) > 0)
          
        # Build k-grams out of the wildcard
        if not wildcard.startswith('*'):
            wildcard = '$' + wildcard
        if not wildcard.endswith('*'):
            wildcard = wildcard + '$'
    
        wcgrams = None
        
        for i in range(1, len(wildcard)):
            if '*' == wildcard[i-1] or '*' == wildcard[i]:
                continue
            if wildcard[i-1] + wildcard[i] in self.dict:
                if wcgrams == None:      
                    wcgrams = set(self.dict[wildcard[i-1] + wildcard[i]])
                wcgrams = wcgrams.intersection(set(self.dict[wildcard[i-1] + wildcard[i]]))
            else:
                return set([])
        return wcgrams
