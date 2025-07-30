"""
Pandas DataFrame 读取速查表
Quick reference for reading data into pandas DataFrames
"""

import pandas as pd

# ====================================
# 1. 常用文件格式读取
# ====================================

# CSV 文件
# df = pd.read_csv('file.csv')
# df = pd.read_csv('file.csv', 
#                  encoding='utf-8',     # 编码
#                  sep=',',              # 分隔符
#                  header=0,             # 表头行
#                  index_col=0,          # 索引列
#                  na_values=['NULL'])   # 空值标识

# Excel 文件
# df = pd.read_excel('file.xlsx')
# df = pd.read_excel('file.xlsx', sheet_name='Sheet1')  # 指定工作表
# df = pd.read_excel('file.xlsx', sheet_name=None)      # 所有工作表

# JSON 文件
# df = pd.read_json('file.json')
# df = pd.read_json('file.json', orient='records')     # 指定格式

# JSON Lines (每行一个JSON对象)
# import json
# data = []
# with open('file.jsonl', 'r') as f:
#     for line in f:
#         data.append(json.loads(line))
# df = pd.DataFrame(data)

# ====================================
# 2. 数据库读取
# ====================================

# 需要先安装: pip install sqlalchemy
# df = pd.read_sql('SELECT * FROM table', connection)
# df = pd.read_sql_table('table_name', connection)
# df = pd.read_sql_query('SQL_QUERY', connection)

# ====================================
# 3. 其他格式
# ====================================

# Parquet
# df = pd.read_parquet('file.parquet')

# Pickle
# df = pd.read_pickle('file.pkl')

# 固定宽度文件
# df = pd.read_fwf('file.txt', widths=[10, 10, 10])

# 剪贴板
# df = pd.read_clipboard()

# ====================================
# 4. 高级选项
# ====================================

# 分块读取大文件
# for chunk in pd.read_csv('large_file.csv', chunksize=1000):
#     process(chunk)

# 指定数据类型
# dtypes = {'col1': 'int64', 'col2': 'category'}
# df = pd.read_csv('file.csv', dtype=dtypes)

# 解析日期
# df = pd.read_csv('file.csv', parse_dates=['date_col'])

# ====================================
# 5. 数据检查常用方法
# ====================================

def inspect_dataframe(df):
    """快速检查DataFrame"""
    print("形状:", df.shape)
    print("列名:", df.columns.tolist())
    print("数据类型:\n", df.dtypes)
    print("前5行:\n", df.head())
    print("缺失值:\n", df.isnull().sum())
    print("基本统计:\n", df.describe())

# ====================================
# 6. 常见问题解决
# ====================================

# 编码问题
# df = pd.read_csv('file.csv', encoding='gbk')  # 尝试不同编码

# 分隔符问题
# df = pd.read_csv('file.csv', sep='\t')        # Tab分隔
# df = pd.read_csv('file.csv', sep='|')         # 管道分隔

# 无表头
# df = pd.read_csv('file.csv', header=None)

# 跳过行
# df = pd.read_csv('file.csv', skiprows=1)      # 跳过第一行

# 只读取特定列
# df = pd.read_csv('file.csv', usecols=['col1', 'col2'])

# 处理缺失值
# df = pd.read_csv('file.csv', na_values=['N/A', 'NULL', ''])

if __name__ == "__main__":
    print("Pandas DataFrame 读取速查表")
    print("请参考代码中的注释了解各种读取方法")
    print("运行 python3 df_reading_examples.py 查看完整示例")
    print("运行 python3 practical_json_reading.py 查看实际文件读取示例")