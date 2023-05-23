import tushare as ts

# # 基金持仓
# df = ts.fund_holdings(2022, 4)
# df = df.sort_values('amount', ascending=False)
# df = df[df['symbol'].str.startswith(('510', '1599', '1598', '512', '513', '515', '516', '518', '519', '511'))]
# df = df.head(50)
#
# print(df['symbol'])

# 龙虎榜
df = ts.top_list('2022-05-20')
df = df[df['type'] == 'industry']
df = df.groupby('industry')['code'].apply(list)
df = df.head(20)