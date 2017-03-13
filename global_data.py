#!/usr/bin/python3
# -*- encoding: utf8 -*-

import os
import pickle
import pandas as pd
import tushare as ts   # reference: http://tushare.org/trading.html

ROOT_DIR_PATH = os.path.split(os.path.realpath(__file__))[0]  # 保证是global_data.py所在的目录

DB_PATH = ROOT_DIR_PATH + '/database.bin'
if os.path.exists(DB_PATH):
    with open(DB_PATH, 'rb') as f:
        stocks = pickle.load(f)
else:
    stocks = {}

def add_data(stock, start='2016-01-01'):  # 格式:1月必须写作01
    """ 添加对应股票的从给定日期开始的全部K线数据 """
    global stocks
    new_df = ts.get_k_data(stock, start).set_index('date')  # tushare返回的是以数字作为索引 改成日期索引
    stocks[stock] = pd.concat([stocks.get(stock) , new_df])  # 注意原stocks[stock]可能为空 用concat合并数据
    stocks[stock].drop_duplicates(subset=['close', 'volume'], inplace=True) # 用收盘价和成交量去掉重复数据(默认全部会导致对新数据去重失效) 而日期是索引不能用
    stocks[stock].sort_index(inplace=True, kind='mergesort')  # 确保添加后时间有序
    return stocks[stock]

def get_data(stock):
    """ 若有返回对应的dataframe 若无返回None """
    return stocks.get(stock)

def add_column(stock, column, data):
    """ 增加一列 注意data的长度要和原表格的行数相等 """
    global stocks
    stocks[stock][column] = data
    return stocks[stock] 

def save_database(filename=DB_PATH):
    """ 保存当前数据到文件中 """
    with open('%s' % filename, 'wb') as f:
        pickle.dump(stocks, f, pickle.HIGHEST_PROTOCOL)

def update_data(stock):
    """ 更新给定股票的K线信息至最新 与add_data不同之处是它会按当前的数据更新 减少下载量 """
    global stocks
    # print('before update\n' + str(stocks[stock].tail()))
    last_date = stocks[stock].index[-1]  # 日期为index
    new_df = ts.get_k_data(stock, last_date).set_index('date')
    stocks[stock] = pd.concat([stocks[stock] , new_df])
    stocks[stock].drop_duplicates(subset=['close', 'volume'], inplace=True)  # last_date数据重复
    # print('after update\n' + str(stocks[stock].tail()))
    return stocks[stock]
