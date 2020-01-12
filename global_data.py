#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import configparser
import logging
import os
import pickle
import subprocess
import time

import numpy as np
import pandas as pd
import tushare as ts  # reference: http://tushare.org/trading.html
import yfinance as yf

logging.disable(30)  # 屏蔽futu OpenQuoteContext初始化时的log

ROOT_DIR_PATH = os.path.split(os.path.realpath(__file__))[0]  # 保证是global_data.py所在的目录
DB_FILE = ROOT_DIR_PATH + '/database.bin'
if os.path.exists(DB_FILE):
    print('WILL READ FROM SAVED DATABASE FILE!')
    with open(DB_FILE, 'rb') as f:
        stocks = pickle.load(f)
else:
    stocks = {}

# 最新的交易日 即上证指数最近的日期
NEWEST_TRADE_DATE = ts.get_k_data('000001', index=True)['date'].iloc[-1]
# 获取所有F10数据 例如中文名称等
BASIC_INFO = {}
try:
    print('Getting basic F10 info for CN..')
    BASIC_INFO['CN'] = ts.get_stock_basics()
except:
    BASIC_INFO['CN'] = pd.DataFrame()
    print('Warning: Get stock F10 info from tushare failed')

conf = configparser.ConfigParser()
conf.read('config.ini')
START_DECISION_DATE = conf['Config']['start_decision_date']
START_DOWNLOAD_DATE = conf['Config']['start_download_date']

# 是否启用futu的港股美股接口
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
        time.sleep(10)
    # 等待daemon启动完成后 下载港股和美股的F10数据
    quote_ctx = futu.OpenQuoteContext(host='127.0.0.1', port=11111)
    print('Getting basic F10 info for HK..')
    return_code, data_df = quote_ctx.get_stock_basicinfo(futu.Market.HK, stock_type=futu.SecurityType.STOCK)
    assert return_code == 0, 'get data from futu error: %s' % data_df
    BASIC_INFO['HK'] = data_df.set_index('code')

    print('Getting basic F10 info for US..')
    return_code, data_df = quote_ctx.get_stock_basicinfo(futu.Market.US, stock_type=futu.SecurityType.STOCK)
    assert return_code == 0, 'get data from futu error: %s' % data_df
    BASIC_INFO['US'] = data_df.set_index('code')
    quote_ctx.close()


def add_data(stock, start='') -> pd.DataFrame:  # 格式:1月必须写作01  2019-01-01
    """ 添加对应股票的从给定日期开始的全部K线数据到全局变量stocks
        并返回该股票的数据

        e.g.
                     code    open   close    high     low     volume 
        date (是字符串)
        2016-11-14  000001  8.883   8.941   8.970   8.883   975078.0
    """
    if stock.isdigit():  # 如果是纯数字 则调用tushare的沪深数据接口
        new_df = ts.get_k_data(stock, start).set_index('date')  # tushare返回的是以数字作为索引 改成按日期索引

        # 坑爹数据源 如果传入了start 就会获取不到今天的数据 解决方法：另外不传入start获取一次 再拼接最后一天的数据
        new_df_without_start_param = ts.get_k_data(stock).set_index('date')

        latest_date_new_df = new_df.index[-1]  # str
        latest_date_new_df_without_start_param = new_df_without_start_param.index[-1]  # str
        if latest_date_new_df != latest_date_new_df_without_start_param:
            assert new_df.index[-1] == new_df_without_start_param.index[-2]  # 确认只少了最新的一天
            latest_row = new_df_without_start_param.iloc[-1]
            new_df = new_df.append(latest_row)
    elif stock.startswith('HK.'):  # 若代码包含英文字符 则调用futu的接口
        quote_ctx = futu.OpenQuoteContext(host='127.0.0.1', port=11111)
        now_date = time.strftime('%Y-%m-%d')  # 以现在时间为准 NEWEST_TRADE_DATE只适用于中国市场
        return_code, new_df, _ = quote_ctx.request_history_kline(stock, start=start, end=now_date)
        assert return_code == 0, 'get data from futu error: %s' % new_df

        # 返回的日期格式为'yyyy-mm-dd 00:00:00' 把后面的去掉 与tushare返回的格式保持统一
        new_df['time_key'] = new_df['time_key'].apply(lambda s: s.split(' ')[0])
        new_df.set_index('time_key', inplace=True)  # 改成按日期索引
        quote_ctx.close()
    elif stock.startswith('US.'):
        ticker = yf.Ticker(stock[3:])  # remove 'US.'
        new_df = ticker.history(start=START_DOWNLOAD_DATE)
        new_df.columns = ['open', 'high', 'low', 'close', 'volume', 'Dividends', 'Stock Splits']  # 改为小写以统一

        # 返回的日期格式为DatetimeIndex对象 转换为字符串
        py_datetime_index = new_df.index.to_pydatetime()
        datetime_to_str = np.vectorize(lambda s: s.strftime('%Y-%m-%d'))
        date_only_array = datetime_to_str(py_datetime_index)
        new_df.index = date_only_array
    else:
        raise RuntimeError('Unknown stock code: {}'.format(stock))

    global stocks
    stocks[stock] = pd.concat([stocks.get(stock), new_df])  # 注意原stocks[stock]可能为空 用concat合并数据
    stocks[stock].drop_duplicates(subset=['close', 'volume'], inplace=True) # 用收盘价和成交量去掉重复数据(默认全部会导致对新数据去重失效) 而日期是索引不能用
    stocks[stock].sort_index(inplace=True, kind='mergesort')  # 确保添加后时间有序
    return stocks[stock]

def get_data(stock: str) -> pd.DataFrame:
    """ 若有返回对应的dataframe 若无则下载数据后返回对应的dataframe """
    result =  stocks.get(stock)
    if result is not None:
        return result
    else:
        # print('%s data does not exist, will download start from %s' % (stock, START_DOWNLOAD_DATE))
        return add_data(stock, START_DOWNLOAD_DATE)

def add_column(stock, column, data) -> pd.DataFrame:
    """ 增加一列 注意data的长度要和原表格的行数相等 """
    global stocks
    stocks[stock][column] = data
    return stocks[stock]

def save_database(filename=DB_FILE):
    """ 保存当前数据到文件中 """
    with open('%s' % filename, 'wb') as f:
        pickle.dump(stocks, f, pickle.HIGHEST_PROTOCOL)

def get_name(stock: str) -> str:
    """ 获取对应代码的中文名称 """
    if stock.isdigit() and stock in BASIC_INFO['CN'].index:  # 有些ETF基金会没有F10数据
        return BASIC_INFO['CN'].loc[stock]['name']
    elif stock.startswith('HK') and 'HK' in BASIC_INFO and stock in BASIC_INFO['HK'].index:
        return BASIC_INFO['HK'].loc[stock]['name']
    elif stock.startswith('US') and 'US' in BASIC_INFO and stock in BASIC_INFO['US'].index:
        return BASIC_INFO['US'].loc[stock]['name']
    else:
        return ''
