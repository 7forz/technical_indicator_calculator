#!/usr/bin/python3
# -*- encoding: utf-8 -*-

from indexes import *
import global_data


def main(stock='000001', date=global_data.NEWEST_TRADE_DATE, p_MA=5, p_MACD=(12,26,9),
         p_RSI=6, p_KDJ=(9,3), p_MTM=(12,6)):
    """
        Example
        date: str, '2017-08-18'
        p_MA: int, 5
        p_MACD: tuple, (12,26,9)
        p_RSI: int, 6
        p_KDJ: tuple, (9,3)
        p_MTM: tuple, (12,6)
    """

    rsi = RSI(stock)
    ma = MA(stock)
    macd = MACD(stock)
    mtm = MTM(stock)
    kdj = KDJ(stock)

    global_data.add_data(stock)  # download data to database

    print(stock, date)
    print('MA%s' % str(p_MA), ma.get_ma(date, p_MA))
    print('MACD%s' % str(p_MACD), macd.get_macd(date, *p_MACD))
    print('RSI%s' % str(p_RSI), rsi.get_rsi(date, p_RSI))
    print('KDJ%s' % str(p_KDJ), kdj.get_kdj(date, *p_KDJ))
    print('MTM%s' % str(p_MTM), mtm.get_mtm(date, *p_MTM))

    global_data.save_database(global_data.DB_FILE)

if __name__ == '__main__':
    main()
