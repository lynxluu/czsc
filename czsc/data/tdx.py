from pytdx.exhq import *
from pytdx.hq import *

api_hq=None
api_exhq=None


from pytdx.hq import TdxHq_API

# 行情服务器设置
server1 = {'ip':'61.152.107.141', 'port':7727}
server2 = {'ip':'218.75.126.9', 'port':7709}

# 创建TdxHq_API对象并连接服务器
api = TdxHq_API()
with api.connect('218.75.126.9', 7709):
    # 获取上证指数实时行情
    # quotes = api.get_security_quotes([(0, '000001')])
    quotes = api.get_security_quotes([(0, '000001'), (1, '600300')])


api_ex = TdxExHq_API()
with api_ex.connect(server2['ip'], server2['port']):
    # ex行情
    # 获取市场
    markets = api_ex.get_markets()

    # 获取代码
    stocks = api_ex.get_instrument_info(0, 100)

    # 数量
    count = api_ex.get_instrument_count()

    # 行情
    # api_ex.get_instrument_quote(47, "IF1709")


# 输出上证指数的当前价格
# print(quotes[0]['price'])
print(quotes[1])
# print(markets)

# # 关闭连接
# api.disconnect()