#!/bin/bash

MAIN="queryIndex.py"
STOPWORDS="myStopWords.dat"
TITLEINDEX="titleIndex.out"
KGRAMINDEX="kgramIndex.out"

# $1 = index file name
python2.6 $MAIN $1 $STOPWORDS $TITLEINDEX $KGRAMINDEX