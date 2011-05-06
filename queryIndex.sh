#!/bin/bash

MAIN="queryIndex.py"
STOPWORDS="myStopWords.dat"
TITLEINDEX="titleIndex.out"
KGRAMINDEX="kgramIndex.out"
OUTGOINGLINKS="outgoingLinks.out"
PAGERANK="pageRank.dat"
FEATURES="features.dat"
VECREP="vecrep.out"
TRAINING="training.dat"

# $1 = index file name
python2.6 $MAIN $1 $STOPWORDS $TITLEINDEX $KGRAMINDEX $OUTGOINGLINKS $PAGERANK $FEATURES $VECREP $TRAINING
