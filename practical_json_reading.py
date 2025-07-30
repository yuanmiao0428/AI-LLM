"""
实用的 JSON 数据读取示例
演示如何读取工作空间中的实际 JSON 文件
"""

import pandas as pd
import json
from pathlib import Path

def read_train_embedding_json():
    """读取 train_embedding.json 文件"""
    print("=== 读取 train_embedding.json ===")
    
    file_path = 'data/train_embedding.json'
    
    try:
        # 方法1: 逐行读取JSON Lines格式
        data_list = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():  # 跳过空行
                    data_list.append(json.loads(line))
        
        # 转换为DataFrame
        df = pd.DataFrame(data_list)
        
        print(f"数据形状: {df.shape}")
        print(f"列名: {df.columns.tolist()}")
        print("\n前5行数据:")
        print(df.head())
        
        print("\n数据类型:")
        print(df.dtypes)
        
        # 展开 pos 列（如果是列表）
        if 'pos' in df.columns:
            print(f"\npos 列第一个元素的类型: {type(df['pos'].iloc[0])}")
            print(f"pos 列第一个元素: {df['pos'].iloc[0]}")
            
            # 如果 pos 是列表，可以展开
            if isinstance(df['pos'].iloc[0], list):
                df_expanded = df.explode('pos')
                print(f"\n展开后的数据形状: {df_expanded.shape}")
                print("展开后的前5行:")
                print(df_expanded.head())
        
        return df
        
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return None

def read_zh_seed_tasks_json():
    """读取 zh_seed_tasks.json 文件"""
    print("\n=== 读取 zh_seed_tasks.json ===")
    
    file_path = 'data/zh_seed_tasks.json'
    
    try:
        # 逐行读取
        data_list = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data_list.append(json.loads(line))
        
        df = pd.DataFrame(data_list)
        
        print(f"数据形状: {df.shape}")
        print(f"列名: {df.columns.tolist()}")
        print("\n前3行数据:")
        print(df.head(3))
        
        return df
        
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return None

def read_large_json_file():
    """读取大型 JSON 文件的策略"""
    print("\n=== 读取大型 JSON 文件 (qa_train.json) ===")
    
    file_path = 'data/qa_train.json'
    
    try:
        # 获取文件大小
        file_size = Path(file_path).stat().st_size
        print(f"文件大小: {file_size / (1024*1024):.2f} MB")
        
        # 方法1: 分批读取（推荐用于大文件）
        print("\n使用分批读取:")
        batch_size = 10
        data_batch = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= batch_size:  # 只读取前10行作为示例
                    break
                if line.strip():
                    data_batch.append(json.loads(line))
        
        if data_batch:
            df_sample = pd.DataFrame(data_batch)
            print(f"示例数据形状: {df_sample.shape}")
            print(f"列名: {df_sample.columns.tolist()}")
            print("\n前3行数据:")
            print(df_sample.head(3))
        
        return df_sample if data_batch else None
        
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return None

def json_reading_best_practices():
    """JSON 读取最佳实践"""
    print("\n=== JSON 读取最佳实践 ===")
    
    practices = [
        "1. 确定 JSON 格式:",
        "   - JSON Lines (.jsonl): 每行一个JSON对象",
        "   - 标准 JSON: 整个文件是一个JSON数组或对象",
        "",
        "2. 处理大文件:",
        "   - 使用分批读取避免内存溢出",
        "   - 考虑使用生成器处理数据",
        "",
        "3. 错误处理:",
        "   - 使用 try-except 处理格式错误",
        "   - 检查文件编码（通常是 utf-8）",
        "",
        "4. 数据验证:",
        "   - 检查数据类型和结构",
        "   - 处理缺失值和异常值",
        "",
        "5. 性能优化:",
        "   - 只读取需要的列",
        "   - 使用适当的数据类型"
    ]
    
    for practice in practices:
        print(practice)

def main():
    """主函数"""
    print("Python pandas 实用 JSON 读取示例")
    print("=" * 50)
    
    # 读取各种 JSON 文件
    df1 = read_train_embedding_json()
    df2 = read_zh_seed_tasks_json()
    df3 = read_large_json_file()
    
    # 最佳实践
    json_reading_best_practices()
    
    print(f"\n总结:")
    print(f"- train_embedding.json: {'成功读取' if df1 is not None else '读取失败'}")
    print(f"- zh_seed_tasks.json: {'成功读取' if df2 is not None else '读取失败'}")
    print(f"- qa_train.json (示例): {'成功读取' if df3 is not None else '读取失败'}")

if __name__ == "__main__":
    main()