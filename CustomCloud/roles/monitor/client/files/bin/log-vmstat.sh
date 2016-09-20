#!/bin/bash

LOG=~/logs/vmstat.`date -I`.log
echo "---------------------------" >> $LOG
date "+%Y-%m-%d %H:%M:%S" >> $LOG
echo "---------------------------" >> $LOG
vmstat 1 60 >> $LOG
