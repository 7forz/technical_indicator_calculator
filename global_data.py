#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import configparser
import logging
import os
import pickle
import subprocess
import time

import futu
import numpy as np
import pandas as pd
import psutil
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

# 获取最新交易日的日期
trade_calendar = ts.pro_api().trade_cal(end_date=time.strftime('%Y%m%d'))
NEWEST_TRADE_DATE = trade_calendar[trade_calendar['is_open'] == 1].iloc[-1]['cal_date']  # '20200101'
NEWEST_TRADE_DATE = f'{NEWEST_TRADE_DATE[:4]}-{NEWEST_TRADE_DATE[4:6]}-{NEWEST_TRADE_DATE[-2:]}'  # '2020-01-01'

# 获取所有F10数据 例如中文名称等
BASIC_INFO = {}
try:
    print('Getting basic F10 info for CN..')
    stock_basic = ts.pro_api().stock_basic()
    stock_basic['ts_code'] = stock_basic['ts_code'].apply(lambda s: s[:-3])
    BASIC_INFO['CN'] = stock_basic.set_index('ts_code')
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
    opend_path = conf['Config']['futu_opend_path']
    login_account = conf['Config']['futu_login_account']
    login_pwd_md5 = conf['Config']['futu_login_pwd_md5']

    opend_basename = os.path.basename(opend_path)  # FutuOpenD.exe
    pids = psutil.pids()
    while True:
        try:
            process_names = set(psutil.Process(pid).name() for pid in pids)
        except psutil.NoSuchProcess:
            time.sleep(1)
        else:
            break

    if opend_basename not in process_names:
        subprocess.Popen(
            [opend_path, f'-login_account={login_account}', f'-login_pwd_md5={login_pwd_md5}', '-log_level=warning']
        )
        print('Wait for FutuOpenD connection..')
        time.sleep(10)
    # 等待daemon启动完成后 下载港股和美股的F10数据
    quote_ctx = futu.OpenQuoteContext(host='127.0.0.1', port=11111)
    print('Getting basic F10 info for HK..')
    return_code, data_df = quote_ctx.get_stock_basicinfo(futu.Market.HK, stock_type=futu.SecurityType.STOCK)
    assert return_code == 0, f'get data from futu error: {data_df}'
    BASIC_INFO['HK'] = data_df.set_index('code')

    print('Getting basic F10 info for US..')
    return_code, data_df = quote_ctx.get_stock_basicinfo(futu.Market.US, stock_type=futu.SecurityType.STOCK)
    assert return_code == 0, f'get data from futu error: {data_df}'
    BASIC_INFO['US'] = data_df.set_index('code')
    quote_ctx.close()


def get_data_from_tushare(stock: str, start: str) -> pd.DataFrame:
    df = ts.get_k_data(stock, start).set_index('date')  # tushare返回的是以数字作为索引 改成按日期索引

    # 坑爹数据源 如果传入了start 就会获取不到今天的数据 解决方法：另外不传入start获取一次 再拼接最后一天的数据
    df_without_start_param = ts.get_k_data(stock).set_index('date')

    latest_date_df = df.index[-1]  # str
    latest_date_df_without_start_param = df_without_start_param.index[-1]  # str
    if latest_date_df != latest_date_df_without_start_param:
        assert df.index[-1] == df_without_start_param.index[-2]  # 确认只少了最新的一天
        latest_row = df_without_start_param.iloc[-1]
        df = df.append(latest_row)
    return df

def get_data_from_tushare_pro(stock: str, start: str) -> pd.DataFrame:
    start_yyyymmdd = start.replace('-', '')
    df: pd.DataFrame = ts.pro_bar(ts_code=stock, adj='qfq', start_date=start_yyyymmdd)
    df.rename(columns={'vol': 'volume'}, inplace=True)
    df.sort_values(by='trade_date', inplace=True)  # ts pro的日期是反序的
    df['trade_date'] = df['trade_date'].apply(lambda s: f'{s[:4]}-{s[4:6]}-{s[6:8]}')
    df.set_index('trade_date', inplace=True)  # 改成按日期索引
    return df

def get_data_from_futu_opend(stock: str, start: str) -> pd.DataFrame:
    quote_ctx = futu.OpenQuoteContext(host='127.0.0.1', port=11111)
    today_date = time.strftime('%Y-%m-%d')  # 以现在时间为准 NEWEST_TRADE_DATE只适用于中国市场
    return_code, df, _ = quote_ctx.request_history_kline(stock, start=start, end=today_date)
    assert return_code == 0, f'get data from futu error: {df}'

    # 返回的日期格式为'yyyy-mm-dd 00:00:00' 把后面的去掉 与tushare返回的格式保持统一
    df['time_key'] = df['time_key'].apply(lambda s: s.split(' ')[0])
    df.set_index('time_key', inplace=True)  # 改成按日期索引
    quote_ctx.close()
    time.sleep(0.5)
    return df

def get_data_from_yfinance(stock: str, start: str) -> pd.DataFrame:
    ticker = yf.Ticker(stock[3:])  # remove 'US.'
    df = ticker.history(start=start)
    df.columns = ['open', 'high', 'low', 'close', 'volume', 'Dividends', 'Stock Splits']  # 改为小写以统一

    # 返回的日期格式为DatetimeIndex对象 转换为字符串
    py_datetime_index = df.index.to_pydatetime()
    datetime_to_str = np.vectorize(lambda s: s.strftime('%Y-%m-%d'))
    date_only_array = datetime_to_str(py_datetime_index)
    df.index = date_only_array
    return df


def add_data(stock: str, start: str) -> pd.DataFrame:  # 格式:1月必须写作01  2019-01-01
    """ 添加对应股票的从给定日期开始的全部K线数据到全局变量stocks
        并返回该股票的数据

        e.g.
                     code    open   close    high     low     volume 
        date (是字符串)
        2016-11-14  000001  8.883   8.941   8.970   8.883   975078.0
    """
    if stock.isdigit():  # 如果是纯数字 则调用tushare的沪深数据接口
        df = get_data_from_tushare(stock, start)
    elif stock.endswith('.SH') or stock.endswith('.SZ'):  # 调用tushare pro  需要先设置其token
        df = get_data_from_tushare_pro(stock, start)
    elif stock.startswith('SH.') or stock.startswith('SZ.') or stock.startswith('HK.'):
        df = get_data_from_futu_opend(stock, start)
    elif stock.startswith('US.'):
        df = get_data_from_yfinance(stock, start)
    else:
        raise RuntimeError('Unknown stock code: {}'.format(stock))

    global stocks
    stocks[stock] = pd.concat([stocks.get(stock), df])  # 注意原stocks[stock]可能为空 用concat合并数据
    stocks[stock].drop_duplicates(subset=['close', 'volume'], inplace=True) # 用收盘价和成交量去掉重复数据(默认全部会导致对新数据去重失效) 而日期是索引不能用
    stocks[stock].sort_index(inplace=True, kind='mergesort')  # 确保添加后时间有序
    return stocks[stock]

def get_data(stock: str) -> pd.DataFrame:
    """ 若有返回对应的dataframe 若无则下载数据后返回对应的dataframe """
    result =  stocks.get(stock)
    if result is not None:
        return result
    else:
        return add_data(stock, START_DOWNLOAD_DATE)

def add_column(stock, column, data) -> pd.DataFrame:
    """ 增加一列 注意data的长度要和原表格的行数相等 """
    global stocks
    stocks[stock][column] = data
    return stocks[stock]

def save_database(filename=DB_FILE):
    """ 保存当前数据到文件中 """
    with open(filename, 'wb') as f:
        pickle.dump(stocks, f, pickle.HIGHEST_PROTOCOL)

def get_name(stock: str) -> str:
    """ 获取对应代码的中文名称 """
    if stock.isdigit() and stock in BASIC_INFO['CN'].index:  # 有些ETF基金会没有F10数据
        return BASIC_INFO['CN'].loc[stock]['name']
    elif (stock.endswith('.SH') or stock.endswith('.SZ')) and stock[:-3] in BASIC_INFO['CN'].index:
        return BASIC_INFO['CN'].loc[stock[:-3]]['name']
    elif (stock.startswith('SH.') or stock.startswith('SZ.')) and stock[3:] in BASIC_INFO['CN'].index:
        return BASIC_INFO['CN'].loc[stock[3:]]['name']
    elif stock.startswith('HK') and 'HK' in BASIC_INFO and stock in BASIC_INFO['HK'].index:
        return BASIC_INFO['HK'].loc[stock]['name']
    elif stock.startswith('US') and 'US' in BASIC_INFO and stock in BASIC_INFO['US'].index:
        return BASIC_INFO['US'].loc[stock]['name']
    else:
        return ''
