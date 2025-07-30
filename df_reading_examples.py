"""
Python DataFrame 读取示例
演示如何使用 pandas 读取不同格式的数据
"""

import pandas as pd
import json
import numpy as np
from pathlib import Path

def read_csv_example():
    """读取 CSV 文件"""
    print("=== CSV 文件读取 ===")
    
    # 基本读取
    # df = pd.read_csv('data.csv')
    
    # 带参数的读取
    # df = pd.read_csv(
    #     'data.csv',
    #     encoding='utf-8',      # 指定编码
    #     sep=',',               # 分隔符
    #     header=0,              # 表头行
    #     index_col=0,           # 索引列
    #     na_values=['', 'NULL'] # 空值标识
    # )
    
    # 创建示例数据演示
    sample_data = {
        'name': ['张三', '李四', '王五'],
        'age': [25, 30, 35],
        'city': ['北京', '上海', '广州']
    }
    df = pd.DataFrame(sample_data)
    print("示例 CSV 数据:")
    print(df)
    print()

def read_excel_example():
    """读取 Excel 文件"""
    print("=== Excel 文件读取 ===")
    
    # 基本读取
    # df = pd.read_excel('data.xlsx')
    
    # 指定工作表
    # df = pd.read_excel('data.xlsx', sheet_name='Sheet1')
    # df = pd.read_excel('data.xlsx', sheet_name=0)  # 第一个工作表
    
    # 读取多个工作表
    # dfs = pd.read_excel('data.xlsx', sheet_name=None)  # 返回字典
    
    # 创建示例数据演示
    sample_data = {
        'product': ['手机', '电脑', '平板'],
        'price': [3000, 8000, 2000],
        'stock': [100, 50, 80]
    }
    df = pd.DataFrame(sample_data)
    print("示例 Excel 数据:")
    print(df)
    print()

def read_json_example():
    """读取 JSON 文件"""
    print("=== JSON 文件读取 ===")
    
    # 基本读取
    # df = pd.read_json('data.json')
    
    # 指定方向
    # df = pd.read_json('data.json', orient='records')
    # df = pd.read_json('data.json', orient='index')
    
    # 从现有的 JSON 文件读取
    try:
        if Path('data/train_embedding.json').exists():
            # 读取实际的 JSON 文件
            with open('data/train_embedding.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 如果是列表，直接转换
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data[:5])  # 只显示前5行
                print("从 train_embedding.json 读取的数据 (前5行):")
                print(df.head())
            else:
                print("JSON 格式需要特殊处理")
    except Exception as e:
        print(f"读取 JSON 文件时出错: {e}")
    
    # 创建示例数据演示
    sample_json_data = [
        {'id': 1, 'name': '产品A', 'category': '电子'},
        {'id': 2, 'name': '产品B', 'category': '服装'},
        {'id': 3, 'name': '产品C', 'category': '食品'}
    ]
    df = pd.DataFrame(sample_json_data)
    print("\n示例 JSON 数据:")
    print(df)
    print()

def read_sql_example():
    """读取 SQL 数据库"""
    print("=== SQL 数据库读取 ===")
    
    # 需要安装相应的数据库驱动
    # pip install sqlalchemy pymysql psycopg2-binary
    
    print("SQL 读取示例代码:")
    print("""
    import sqlalchemy as sa
    
    # 创建数据库连接
    engine = sa.create_engine('mysql+pymysql://user:password@host:port/database')
    
    # 读取整个表
    df = pd.read_sql_table('table_name', engine)
    
    # 执行 SQL 查询
    df = pd.read_sql_query('SELECT * FROM table_name WHERE condition', engine)
    
    # 或者使用简化的方法
    df = pd.read_sql('SELECT * FROM table_name', engine)
    """)
    print()

def read_other_formats():
    """读取其他格式的文件"""
    print("=== 其他格式文件读取 ===")
    
    print("1. Parquet 文件:")
    print("df = pd.read_parquet('data.parquet')")
    
    print("\n2. HDF5 文件:")
    print("df = pd.read_hdf('data.h5', key='data')")
    
    print("\n3. Feather 文件:")
    print("df = pd.read_feather('data.feather')")
    
    print("\n4. Pickle 文件:")
    print("df = pd.read_pickle('data.pkl')")
    
    print("\n5. 固定宽度文件:")
    print("df = pd.read_fwf('data.txt', widths=[10, 10, 10])")
    
    print("\n6. 剪贴板数据:")
    print("df = pd.read_clipboard()")
    print()

def advanced_reading_options():
    """高级读取选项"""
    print("=== 高级读取选项 ===")
    
    print("1. 处理大文件 - 分块读取:")
    print("""
    chunk_size = 1000
    for chunk in pd.read_csv('large_file.csv', chunksize=chunk_size):
        # 处理每个数据块
        process_chunk(chunk)
    """)
    
    print("\n2. 指定数据类型:")
    print("""
    dtypes = {
        'col1': 'int64',
        'col2': 'float64',
        'col3': 'category'
    }
    df = pd.read_csv('data.csv', dtype=dtypes)
    """)
    
    print("\n3. 解析日期:")
    print("""
    df = pd.read_csv('data.csv', 
                     parse_dates=['date_column'],
                     date_parser=pd.to_datetime)
    """)
    
    print("\n4. 处理缺失值:")
    print("""
    df = pd.read_csv('data.csv',
                     na_values=['N/A', 'NULL', ''],
                     keep_default_na=False)
    """)
    print()

def data_inspection():
    """数据检查和基本信息"""
    print("=== 数据检查 ===")
    
    # 创建示例数据
    data = {
        'A': [1, 2, 3, 4, 5],
        'B': [10.1, 20.2, 30.3, 40.4, 50.5],
        'C': ['a', 'b', 'c', 'd', 'e'],
        'D': pd.date_range('2024-01-01', periods=5)
    }
    df = pd.DataFrame(data)
    
    print("示例数据:")
    print(df)
    print()
    
    print("数据基本信息:")
    print("形状 (shape):", df.shape)
    print("列名 (columns):", df.columns.tolist())
    print("数据类型 (dtypes):")
    print(df.dtypes)
    print()
    
    print("前几行 (head):")
    print(df.head(3))
    print()
    
    print("后几行 (tail):")
    print(df.tail(3))
    print()
    
    print("统计信息 (describe):")
    print(df.describe())
    print()
    
    print("缺失值检查 (isnull):")
    print(df.isnull().sum())
    print()

def main():
    """主函数"""
    print("Python pandas DataFrame 读取示例")
    print("=" * 50)
    print()
    
    # 检查是否安装了 pandas
    try:
        import pandas as pd
        print(f"pandas 版本: {pd.__version__}")
        print()
    except ImportError:
        print("错误: 未安装 pandas")
        print("请运行: pip install pandas")
        return
    
    # 运行各种示例
    read_csv_example()
    read_excel_example()
    read_json_example()
    read_sql_example()
    read_other_formats()
    advanced_reading_options()
    data_inspection()
    
    print("更多信息请查看 pandas 官方文档:")
    print("https://pandas.pydata.org/docs/user_guide/io.html")

if __name__ == "__main__":
    main()