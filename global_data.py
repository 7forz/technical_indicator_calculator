#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import configparser
import os
import pickle
import subprocess
import time

import pandas as pd
import tushare as ts   # reference: http://tushare.org/trading.html

ROOT_DIR_PATH = os.path.split(os.path.realpath(__file__))[0]  # 保证是global_data.py所在的目录
DB_FILE = ROOT_DIR_PATH + '/database.bin'
if os.path.exists(DB_FILE):
    with open(DB_FILE, 'rb') as f:
        stocks = pickle.load(f)
else:
    stocks = {}

# 最新的交易日 即上证指数最近的日期
NEWEST_TRADE_DATE = ts.get_k_data('000001', index=True)['date'].iloc[-1]
# 获取所有F10数据 例如中文名称等
BASIC_INFO = ts.get_stock_basics()

# 是否启用futu的港股美股接口
conf = configparser.ConfigParser()
conf.read('config.ini')
futu_enabled = conf['Config'].getboolean('futu_enabled')
if futu_enabled:
    import futu
    opend_path = conf['Config']['futu_opend_path']
    login_account = conf['Config']['futu_login_account']
    login_pwd_md5 = conf['Config']['futu_login_pwd_md5']

    opend_basename = os.path.basename(opend_path)  # FutuOpenD.exe
    # 若没有运行futu daemon 则启动 这里只做了Windows系统的适配 否则会报错
    task_status = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq %s' % opend_basename],
                                 capture_output=True, check=True).stdout
    if opend_basename.encode() not in task_status:  # task_status是bytes opend_basename是str
        subprocess.Popen(
            [opend_path, '-login_account=%s' % login_account, '-login_pwd_md5=%s' % login_pwd_md5, '-log_level=warning']
        )
        print('Wait for FutuOpenD connection..')
        time.sleep(5)

def add_data(stock, start=''):  # 格式:1月必须写作01
    """ 添加对应股票的从给定日期开始的全部K线数据到全局变量stocks
        并返回该股票的数据
    """
    if stock.isdigit():  # 如果是纯数字 则调用tushare的沪深数据接口
        new_df = ts.get_k_data(stock, start).set_index('date')  # tushare返回的是以数字作为索引 改成按日期索引
    else:  # 若代码包含英文字符 则调用futu的接口
        quote_ctx = futu.OpenQuoteContext(host='127.0.0.1', port=11111)
        _return_code, new_df, _ = quote_ctx.request_history_kline(stock)
        # 返回的日期格式为'yyyy-mm-dd 00:00:00' 把后面的去掉 与tushare返回的格式保持统一
        new_df['time_key'] = new_df['time_key'].apply(lambda s: s.split(' ')[0])
        new_df.set_index('time_key', inplace=True)  # 改成按日期索引
        quote_ctx.close()

    global stocks
    stocks[stock] = pd.concat([stocks.get(stock), new_df])  # 注意原stocks[stock]可能为空 用concat合并数据
    stocks[stock].drop_duplicates(subset=['close', 'volume'], inplace=True) # 用收盘价和成交量去掉重复数据(默认全部会导致对新数据去重失效) 而日期是索引不能用
    stocks[stock].sort_index(inplace=True, kind='mergesort')  # 确保添加后时间有序
    return stocks[stock]

def get_data(stock):
    """ 若有返回对应的dataframe 若无则下载数据后返回对应的dataframe """
    result =  stocks.get(stock)
    if result is not None:
        return result
    else:
        return add_data(stock)

def add_column(stock, column, data):
    """ 增加一列 注意data的长度要和原表格的行数相等 """
    global stocks
    stocks[stock][column] = data
    return stocks[stock]

def save_database(filename=DB_FILE):
    """ 保存当前数据到文件中 """
    with open('%s' % filename, 'wb') as f:
        pickle.dump(stocks, f, pickle.HIGHEST_PROTOCOL)
