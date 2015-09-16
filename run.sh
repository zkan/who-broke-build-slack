#!/bin/bash

for i in `seq 1`;
do
    nohup python who_broke_build.py &
done

