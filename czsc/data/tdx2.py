from pytdx.exhq import *
from pytdx.hq import *

# 创建TdxHq_API对象并连接服务器
api = TdxExHq_API()
api.connect('119.147.212.81', 7709)

# 查询支持的市场列表
markets = api.get_markets()

# 输出支持的市场列表
print(markets)

# 关闭连接
api.disconnect()