#!/usr/bin/python3
# -*- encoding: utf8 -*-

# convert database.bin to csv files for analysing

import os
import pickle

db_path = 'database.bin'
if os.path.exists(db_path):
    with open(db_path, 'rb') as f:
        stocks = pickle.load(f)
        for k in stocks:
            stocks[k].to_csv('%s.csv' % k)
