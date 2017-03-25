#!/usr/bin/python3
# -*- encoding: utf8 -*-

# convert database.bin to csv files for analysing

import os
import pickle

DB_PATH = 'database.bin'
if os.path.exists(DB_PATH):
    with open(DB_PATH, 'rb') as f:
        stocks = pickle.load(f)
        for k in stocks:
            stocks[k].to_csv('z:/%s.csv' % k)
