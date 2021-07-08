#!/bin/sh
# copyright: GeoDS Lab, University of Wisconsin-Madison
# authors: Yuhao Kang, Song Gao, Jinmeng Rao

START=$2
END=$3
for i in $(seq $START $END); 
do python POI_visits_daily.py --month $1 --day $i; 
done