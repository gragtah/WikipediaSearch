#!/bin/bash

MAIN="createIndex.py"
STOPWORDS="myStopWords.dat"
TITLEINDEX="titleIndex.out"
KGRAMINDEX="kgramIndex.out"

# $1 = full collection file name
# $2 = index file name
python2.6 $MAIN $1 $2 $STOPWORDS $TITLEINDEX $KGRAMINDEX
