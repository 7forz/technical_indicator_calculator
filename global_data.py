#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import configparser
import datetime
import functools
import logging
import os
import pickle
import socket
import time
from typing import Dict, List, Set

import futu
import numpy as np
import pandas as pd
import requests
import tushare as ts  # reference: https://tushare.pro/
import yfinance as yf
from numba.typed.typedlist import List as NumbaList

from dto_enum import OHLCV
from util import bin_search

logging.disable(30)  # 屏蔽futu OpenQuoteContext初始化时的log


class GlobalData:

    print('getting newest trade date..')
    _trade_calendar = ts.pro_api().trade_cal(is_open=1, start_date='20220101', end_date=time.strftime('%Y%m%d'))
    _newest_trade_date_8: str = _trade_calendar.iloc[-1]['cal_date']  # '20200101'
    NEWEST_TRADE_DATE = f'{_newest_trade_date_8[:4]}-{_newest_trade_date_8[4:6]}-{_newest_trade_date_8[-2:]}'  # '2020-01-01'

    _conf = configparser.ConfigParser()
    _conf.read('config.ini')
    START_DECISION_DATE = _conf['Config']['start_decision_date']
    START_DOWNLOAD_DATE = _conf['Config']['start_download_date']

    def __init__(self):
        self._basic_info: Dict[str, pd.DataFrame] = {}
        self._futu_enabled = self._conf['Config'].getboolean('futu_enabled')
        self._futu_host = self._conf['Config']['futu_hostname'] if self._futu_enabled else None
        self._futu_port = 11111

        # 尝试载入本地的database.bin原始数据
        self.db_file_path = os.path.join(self._conf['Config']['save_result_dir'], 'database.bin')
        if os.path.exists(self.db_file_path):
            print('WILL READ FROM SAVED DATABASE FILE!')
            with open(self.db_file_path, 'rb') as f:
                d = pickle.load(f)
                self._symbol_to_dataframe = d['_symbol_to_dataframe']
                self.symbol_to_date_list = d['symbol_to_date_list']
                self.symbol_to_date_set = d['symbol_to_date_set']
        else:
            self._symbol_to_dataframe: Dict[str, pd.DataFrame] = {}
            self.symbol_to_date_list: Dict[str, List[str]] = {}  # 保存各symbol的日期list
            self.symbol_to_date_set: Dict[str, Set[str]] = {}  # 保存各symbol的日期set


    def load_basic_info(self):
        try:
            print('Getting basic F10 info for CN..')
            stock_basic = ts.pro_api().stock_basic(list_status='L', fields='ts_code,symbol,name')  # L是正在上市股票
            self._basic_info['CN'] = stock_basic.set_index('symbol')  # 以symbol('000001')为索引，有ts_code('000001.SZ'), name(中文名)两列
        except BaseException as e:
            self._basic_info['CN'] = pd.DataFrame()
            print(f'Warning: Get stock F10 info from tushare failed: {e}')

        if self._futu_enabled:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                test_socket.connect((self._futu_host, self._futu_port))
                test_socket.close()
            except socket.error as e:
                raise RuntimeError(f'{self._futu_host}:self._futu_port connect failed') from e

            quote_ctx = futu.OpenQuoteContext(host=self._futu_host, port=self._futu_port)
            print('Getting basic F10 info for HK..')
            return_code, data_df = quote_ctx.get_stock_basicinfo(futu.Market.HK, stock_type=futu.SecurityType.STOCK)
            if return_code == 0:
                self._basic_info['HK'] = data_df.set_index('code')
            else:
                self._basic_info['HK'] = pd.DataFrame()
                print(f'get data from futu error: {data_df}')

            print('Getting basic F10 info for US..')
            return_code, data_df = quote_ctx.get_stock_basicinfo(futu.Market.US, stock_type=futu.SecurityType.STOCK)
            if return_code == 0:
                self._basic_info['US'] = data_df.set_index('code')
            else:
                self._basic_info['US'] = pd.DataFrame()
                print(f'get data from futu error: {data_df}')
            quote_ctx.close()

    def add_data(self, symbol: str, start: str) -> pd.DataFrame:
        """ 添加对应股票的从给定日期开始的全部K线数据到self._symbol_to_dataframe, 并返回该股票的数据。
            参数start的格式: 1月必须写作01, 如2019-01-01

            返回dataframe格式
                            open   close    high     low     volume 
            date (字符串)
            2016-11-14     8.883   8.941   8.970    8.883    975078
        """
        print(f'downloading data of {symbol}')
        if symbol.isdigit():  # 如果是纯数字 则调用tushare的沪深数据接口
            raise RuntimeError(f'not supported yet: {symbol}')
            df = get_data_from_tushare(symbol, start)
        elif symbol.endswith('.SH') or symbol.endswith('.SZ'):  # 调用tushare pro  需要先设置其token
            raise RuntimeError(f'not supported yet: {symbol}')
            df = get_data_from_tushare_pro(symbol, start)
        elif symbol.startswith('SH.') or symbol.startswith('SZ.') or symbol.startswith('HK.'):
            df = self._get_data_from_futu_opend(symbol, start)
        elif symbol.startswith('US.'):
            df = self._get_data_from_yfinance(symbol, start)
        elif symbol.startswith('LB-'):
            raise RuntimeError(f'not supported yet: {symbol}')
            df = get_data_from_longbridge(symbol, start)
        else:
            raise RuntimeError(f'Unknown symbol: {symbol}')

        self._symbol_to_dataframe[symbol] = df
        self.symbol_to_date_list[symbol] = list(df.index)
        self.symbol_to_date_set[symbol] = set(df.index)
        return df

    def _get_dataframe(self, symbol: str) -> pd.DataFrame:
        """ 返回对应的dataframe, 若未下载则马上下载数据后返回 """
        df = self._symbol_to_dataframe.get(symbol)
        if df is not None:
            return df
        else:
            return self.add_data(symbol, self.START_DOWNLOAD_DATE)

    @functools.cache
    def find_date_offset(self, symbol: str, date: str) -> int:
        """ 找到给定symbol的给定日期的数组偏移量, 这个偏移量是相对于当前数据的起始日期(START_DOWNLOAD_DATE) """
        dates = self.symbol_to_date_list[symbol]
        if date >= dates[-1]:
            return len(dates) - 1
        elif date <= dates[-0]:
            return 0
        else:  # 以上均是快捷返回，其实作用与bin_search是一样的，但是实际使用时大部分都属于date >= dates[-1]的情况，可以直接返回不需要搜索
            return bin_search(self.symbol_to_date_list[symbol], date)

    @functools.cache
    def get_dates_since_date(self, symbol: str, date: str) -> List[str]:
        """
            提取从给定日期开始的交易日列表，加入缓存机制。
            注意: 这里的date允许传入一个非交易日(即在数据的日期列表中不存在)
        """
        offset = self.find_date_offset(symbol, date)
        result = self.symbol_to_date_list[symbol][offset:]
        return NumbaList(result)

    @functools.cache
    def get_array_since_date(self, symbol: str, column: OHLCV, date: str) -> np.ndarray:
        """
            从df中提取从给定日期开始的给定的列array, 由于df提取series转array很慢, 所以加入缓存机制。
            注意: 这里的date允许传入一个非交易日(即在数据的日期列表中不存在)
        """
        df = self._get_dataframe(symbol)
        if column == OHLCV.OPEN:
            array = df['open'].to_numpy()
        elif column == OHLCV.HIGH:
            array = df['high'].to_numpy()
        elif column == OHLCV.LOW:
            array = df['low'].to_numpy()
        elif column == OHLCV.CLOSE:
            array = df['close'].to_numpy()
        elif column == OHLCV.VOLUME:
            array = df['volume'].to_numpy()
        else:
            raise NameError

        offset = self.find_date_offset(symbol, date)
        result = array[offset:]
        return result

    def _get_data_from_futu_opend(self, symbol: str, start: str) -> pd.DataFrame:
        quote_ctx = futu.OpenQuoteContext(host=self._futu_host, port=self._futu_port)
        today_date = time.strftime('%Y-%m-%d')  # 以现在时间为准 NEWEST_TRADE_DATE只适用于中国市场
        return_code, df, _ = quote_ctx.request_history_kline(symbol, start=start, end=today_date)
        if return_code != 0:  # 最多重试一次
            time.sleep(1)
            return_code, df, _ = quote_ctx.request_history_kline(symbol, start=start, end=today_date)
        if return_code != 0:
            quote_ctx.close()  # 使线程退出 不阻塞主进程
            raise RuntimeError(f'get data from futu error: {df}')

        # 返回的日期格式为'yyyy-mm-dd 00:00:00' 把后面的去掉 日期格式保持统一
        df['time_key'] = df['time_key'].apply(lambda s: s.split(' ')[0])
        df.set_index('time_key', inplace=True)  # 改成按日期索引
        quote_ctx.close()
        time.sleep(0.5)
        return df

    def _get_data_from_yfinance(self, symbol: str, start: str) -> pd.DataFrame:
        ticker = yf.Ticker(symbol.replace('US.', ''))
        try:
            df = ticker.history(start=start, back_adjust=True)
        except:
            time.sleep(1)
            df = ticker.history(start=start, back_adjust=True)
        df.columns = ['open', 'high', 'low', 'close', 'volume', 'Dividends', 'Stock Splits']  # 改为小写以统一

        # 返回的日期格式为DatetimeIndex对象 转换为字符串
        py_datetime_index = df.index.to_pydatetime()
        date_list = list(map(lambda x: x.strftime('%Y-%m-%d'), py_datetime_index))
        df.index = date_list
        time.sleep(0.5)
        return df

    def save_database(self):
        """ 保存当前数据到文件中 """
        d = {}
        d['_symbol_to_dataframe'] = self._symbol_to_dataframe
        d['symbol_to_date_list'] = self.symbol_to_date_list
        d['symbol_to_date_set'] = self.symbol_to_date_set
        with open(self.db_file_path, 'wb') as f:
            pickle.dump(d, f)

    def get_chinese_name(self, symbol: str) -> str:
        """ 获取对应代码的中文名称 """
        symbol = symbol.replace('LB-', '', 1)
        if symbol.isdigit() and symbol in self._basic_info['CN'].index:  # 有些ETF基金会没有F10数据
            return self._basic_info['CN'].loc[symbol]['name']
        elif (symbol.endswith('.SH') or symbol.endswith('.SZ')) and symbol[:-3] in self._basic_info['CN'].index:
            symbol = symbol[:-3]
            return self._basic_info['CN'].loc[symbol]['name']
        elif (symbol.startswith('SH.') or symbol.startswith('SZ.')) and symbol[3:] in self._basic_info['CN'].index:
            symbol = symbol[3:]
            return self._basic_info['CN'].loc[symbol]['name']
        elif symbol.startswith('HK') and 'HK' in self._basic_info and symbol in self._basic_info['HK'].index:
            return self._basic_info['HK'].loc[symbol]['name']
        elif symbol.startswith('US') and 'US' in self._basic_info and symbol in self._basic_info['US'].index:
            return self._basic_info['US'].loc[symbol]['name']
        else:
            return ''


# 没有用到，先放一边
# def get_data_from_tushare(stock: str, start: str) -> pd.DataFrame:
#     df = ts.get_k_data(stock, start).set_index('date')  # tushare返回的是以数字作为索引 改成按日期索引

#     # 坑爹数据源 如果传入了start 就会获取不到今天的数据 解决方法：另外不传入start获取一次 再拼接最后一天的数据
#     df_without_start_param = ts.get_k_data(stock).set_index('date')

#     latest_date_df = df.index[-1]  # str
#     latest_date_df_without_start_param = df_without_start_param.index[-1]  # str
#     if latest_date_df != latest_date_df_without_start_param:
#         assert df.index[-1] == df_without_start_param.index[-2]  # 确认只少了最新的一天
#         latest_row = df_without_start_param.iloc[-1]
#         df = df.append(latest_row)
#     return df


# 没有用到，先放一边
# def get_data_from_tushare_pro(stock: str, start: str) -> pd.DataFrame:
#     start_yyyymmdd = start.replace('-', '')
#     df: pd.DataFrame = ts.pro_bar(ts_code=stock, adj='qfq', start_date=start_yyyymmdd)
#     df.rename(columns={'vol': 'volume'}, inplace=True)
#     df.sort_values(by='trade_date', inplace=True)  # ts pro的日期是反序的
#     df['trade_date'] = df['trade_date'].apply(lambda s: f'{s[:4]}-{s[4:6]}-{s[6:8]}')
#     df.set_index('trade_date', inplace=True)  # 改成按日期索引
#     return df


# 没有用到，先放一边
# def get_data_from_longbridge(stock: str, start: str) -> pd.DataFrame:
#     """ 传入的stock以`LB-`开头，例如`LB-HK.00700` """
#     assert stock.startswith('LB-'), f'should start with "LB-", but got {stock}'
#     region, code = stock.replace('LB-', '', 1).split('.')
#     if region == 'HK':
#         code = code.lstrip('0')
#     symbol = f'ST/{region}/{code}'  # e.g ST/HK/700  不过固定ST开头也不对的，也有ETF开头

#     today_date = datetime.date.today()
#     start_date = datetime.date.fromisoformat(start)
#     days_num = (today_date - start_date).days  # 大概计算需要请求多少天的K线，懒得算上交易日

#     params = {'line_num': days_num, 'line_type': 1000, 'counter_id': symbol, 'adjust_type': 1}
#     headers = {'authority': 'm.lbkrs.com', 'x-application-version': 'master', 'accept-language': 'zh-CN',
#                'sec-ch-ua-mobile': '?0', 'x-platform': 'web', 'accept': 'application/json, text/plain',
#                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
#                'x-bridge-token': 'none', 'sec-ch-ua-platform': '"Windows"', 'origin': 'https://longbridgeapp.com',
#                'sec-fetch-site': 'cross-site', 'sec-fetch-mode': 'cors', 'sec-fetch-dest': 'empty', 'referer': 'https://longbridgeapp.com/'}
#     r = requests.get('https://m.lbkrs.com/api/forward/v2/quote/kline', params=params, headers=headers)
#     assert r.status_code == 200, f'http get {symbol} data error: {r.status_code}'

#     data_dict = r.json()
#     assert data_dict['code'] == 0, f'error code = {data_dict["code"]}, error msg = {data_dict["message"]}'
#     data_list = data_dict['data']['klines']
#     assert data_list, f'data list is empty'
#     df = pd.DataFrame(data_list)
#     df = df.apply(functools.partial(pd.to_numeric, errors='ignore'), axis=0)  # 对每列尝试转为数字
#     df.rename(columns={'amount': 'volume'}, inplace=True)  # 成交量，手
#     datetimes = list(map(datetime.date.fromtimestamp, df['timestamp']))
#     df['date'] = list(map(lambda d: d.isoformat(), datetimes))  # python的map好像不能链式做..
#     df.set_index('date', inplace=True)

#     # 不知道这个factor_b是什么，但是加上就准了（测了几只股票）
#     df['open'] += df['factor_b']
#     df['high'] += df['factor_b']
#     df['low'] += df['factor_b']
#     df['close'] += df['factor_b']

#     return df.loc[start:]


# def add_column(stock, column, data) -> pd.DataFrame:
#     """ 增加一列 注意data的长度要和原表格的行数相等 """
#     stocks[stock][column] = data
#     return stocks[stock]


global_data_instance = GlobalData()


if __name__ == '__main__':
    global_data_instance.load_basic_info()
    print(global_data_instance.add_data('HK.00700', '2022-01-01'))
    print(global_data_instance.add_data('US.NVDA', '2022-01-01'))
    print(global_data_instance.get_chinese_name('000001.SZ'))
    print(global_data_instance.get_array_since_date('HK.00700', OHLCV.CLOSE, '2022-03-20'))
    print(global_data_instance.get_array_since_date('HK.00700', OHLCV.CLOSE, '2022-03-20'))
    print(global_data_instance.get_array_since_date('HK.00700', OHLCV.CLOSE, '2022-03-21'))
