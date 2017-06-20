#!/usr/bin/python3
# -*- encoding: utf-8 -*-

# convert database.bin to csv files for analysing

import os
import pickle

DB_FILE = 'database.bin'
if os.path.exists(DB_FILE):
    with open(DB_FILE, 'rb') as f:
        stocks = pickle.load(f)
        for k in stocks:
            stocks[k].to_csv('z:/%s.csv' % k)
