import jqdatasdk as jq

# 登录聚宽账号
jq_user, jq_pass = '', ''
with open(r'..\data\auth.pwd', 'r') as f:
    lines = f.readlines()
    for line in lines:
        if line.startswith('jq_user='):
            jq_user = line.strip().split('=')[1]
        elif line.startswith('jq_pass='):
            jq_pass = line.strip().split('=')[1]

print(jq_user,jq_pass,len(jq_user),len(jq_pass))
jq.auth(jq_user, jq_pass)

jq.get_query_count()

# 设置查询日期范围
start_date = '2021-05-15'
end_date = '2021-07-04'

# 查询000001.SH的30分钟K线数据
df = jq.get_price('000001.XSHG', start_date=start_date, end_date=end_date, frequency='30m')

# 打印查询结果
print(df)