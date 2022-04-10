#!/usr/bin/python3
# -*- encoding: utf-8 -*-

from global_data import global_data_instance
from indexes import *


def main(symbol='000001', date=global_data_instance.NEWEST_TRADE_DATE,
         p_MA=5, p_MACD=(12,26,9), p_RSI=6, p_KDJ=(9,3), p_MTM=(12,6),
         p_CCI=14, p_DMI=14):
    """
        Example
        symbol: str, '000001',
        date: str, '2017-08-18',
        p_MA: int, 5
        p_MACD: tuple, (12,26,9)
        p_RSI: int, 6
        p_KDJ: tuple, (9,3)
        p_MTM: tuple, (12,6)
        p_CCI: int, 14
        p_DMI: int, 14
    """

    print(f'MA{p_MA} on {date}', ma_instance.get_ma(symbol, date, p_MA))
    print(f'MACD{p_MACD} on {date}', macd_instance.get_macd(symbol, date, *p_MACD))
    print(f'RSI{p_RSI} on {date}', rsi_instance.get_rsi(symbol, date, p_RSI))
    print(f'KDJ{p_KDJ} on {date}', kdj_instance.get_kdj(symbol, date, *p_KDJ))
    print(f'MTM{p_MTM} on {date}', mtm_instance.get_mtm(symbol, date, *p_MTM))
    print(f'CCI{p_CCI} on {date}', cci_instance.get_cci(symbol, date, p_CCI))
    print(f'DMI{p_DMI} on {date}', dmi_instance.get_dmi(symbol, date, p_DMI))

    # global_data_instance.save_database()

if __name__ == '__main__':
    main(symbol='SZ.000001')
    # main(symbol='HK.00700')
