#!/usr/bin/env bash

# run all scripts for processing full text up till csv

LOGDIR=$MEGAMOUTH_HOME/local/log

mkdir -p $LOGDIR

for fn in $MEGAMOUTH_HOME/scripts/full/*/*.py;
do
	 nohup $fn run-all 2>&1 >$LOGDIR/${fn##*/}.log &
done
