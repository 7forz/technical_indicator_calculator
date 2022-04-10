# technical_indicator_calculator

使用tushare、futu获取A股、使用futu获取港股K线数据（需先配置好[Futu OpenD](https://github.com/FutunnOpen/py-futu-api)），使用yfinance获取美股给定代码的K线数据。可以计算给定参数的MA、MACD、RSI、KDJ、MTM、CCI等指标，使用方法见demo.py文件

## 运行环境

* Python 3.9+
* numpy
* pandas
* matplotlib
* tushare (for CN market)
* futu-api (for HK/CN market)
* yfinance (for US market)
* numba
