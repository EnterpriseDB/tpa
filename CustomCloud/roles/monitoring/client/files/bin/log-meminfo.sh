#!/bin/bash

LOG=~/logs/meminfo.`date -I`.log
for i in `seq 1 12`; do
  echo "---------------------------" >> $LOG
  date "+%Y-%m-%d %H:%M:%S" >> $LOG
  echo "---------------------------" >> $LOG
  cat /proc/meminfo >> $LOG
  sleep 5
done

