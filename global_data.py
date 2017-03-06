#!/usr/bin/python3
# -*- encoding: utf8 -*-

import os
import pickle
import pandas as pd
import tushare as ts   # reference: http://tushare.org/trading.html

if os.path.exists('database.bin'):
    with open('database.bin', 'rb') as f:
        stocks = pickle.load(f)
else:
    stocks = {}

def add_data(stock, start='2016-01-01'):  # 格式:1月必须写作01
    """ 传入日期 添加对应股票的从给定日期开始的全部K线数据 """
    global stocks
    new_df = ts.get_k_data(stock, start).set_index('date')  # tushare返回的是以数字作为索引 改成日期索引
    stocks[stock] = pd.concat([stocks.get(stock) , new_df])  # 注意原stocks[stock]可能为空 用concat合并数据
    stocks[stock].drop_duplicates(inplace=True)  # 去掉重复数据
    stocks[stock].sort_index(inplace=True, kind='mergesort')  # 确保添加后时间有序

def get_data(stock):
    """ 若有返回对应的dataframe 若无返回None """
    return stocks.get(stock)

def add_column(stock, column, data):
    """ 增加一列 注意data的长度要和原表格的行数相等 """
    global stocks
    stocks[stock][column] = data

def save_database():
    """ 保存当前数据到文件中 """
    with open('database.bin', 'wb') as f:
        pickle.dump(stocks, f, pickle.HIGHEST_PROTOCOL)
