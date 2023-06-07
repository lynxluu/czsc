def square(x):
    return x ** 2

# 循环测试函数的是否符合预期结果
for i in range(1, 6):
    assert square(i) == i ** 2, "square()函数计算错误"

#函数的输出符合预期结果，则打印出一条消息
print("square()函数测试通过")