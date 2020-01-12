# technical_indicator_calculator

使用tushare获取A股给定股票代码的K线数据，使用futu获取港股，使用yfinance获取美股给定代码的K线数据（需先配置好[Futu OpenD](https://github.com/FutunnOpen/py-futu-api)）。可以计算给定参数的MA、MACD、RSI、KDJ、MTM、CCI等指标，使用方法见demo.py文件

# 运行环境:

* Python 3 (3.7+ recommeded)
* numpy 1.11.2+
* pandas 0.19.2+
* matplotlib
* tushare 0.8.2+
* yfinance (for US market)
* numba (tested with 0.45)
