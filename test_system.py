#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统测试脚本
快速验证系统是否正常工作
"""

import os
import sys
from main import TimelinessAnalysisSystem


def test_system():
    """测试系统"""
    print("=" * 60)
    print("搜索引擎时效性分析系统 - 快速测试")
    print("=" * 60)
    
    # 检查文件是否存在
    required_files = ['config.yaml', 'sample_data.json', 'main.py']
    
    print("\n[检查1] 检查必需文件...")
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} 不存在")
            return False
    
    # 检查依赖
    print("\n[检查2] 检查依赖包...")
    try:
        import pandas
        print("  ✓ pandas")
    except ImportError:
        print("  ✗ pandas 未安装，请运行: pip install pandas")
        return False
    
    try:
        import numpy
        print("  ✓ numpy")
    except ImportError:
        print("  ✗ numpy 未安装，请运行: pip install numpy")
        return False
    
    try:
        import yaml
        print("  ✓ yaml")
    except ImportError:
        print("  ✗ pyyaml 未安装，请运行: pip install pyyaml")
        return False
    
    # 运行测试分析
    print("\n[检查3] 运行示例分析...")
    try:
        system = TimelinessAnalysisSystem(config_path='config.yaml')
        report = system.run(input_file='sample_data.json', output_dir='./test_output')
        print("  ✓ 分析完成")
    except Exception as e:
        print(f"  ✗ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 检查输出文件
    print("\n[检查4] 检查输出文件...")
    output_files = [
        'test_output/analysis_report.json',
        'test_output/analysis_report.html',
        'test_output/poor_queries.csv'
    ]
    
    for file in output_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"  ✓ {file} ({size} bytes)")
        else:
            print(f"  ✗ {file} 未生成")
            return False
    
    # 验证结果
    print("\n[检查5] 验证分析结果...")
    summary = report['summary']
    print(f"  总query数: {summary['total_queries']}")
    print(f"  时效性差: {summary['poor_timeliness_queries']}")
    
    if summary['total_queries'] != 5:
        print("  ✗ 预期处理5个query")
        return False
    
    if summary['poor_timeliness_queries'] < 1:
        print("  ✗ 预期至少有1个时效性差的query")
        return False
    
    print("  ✓ 结果验证通过")
    
    # 显示示例结果
    print("\n[结果预览]")
    print(f"原因分布:")
    for reason, stats in summary['reason_distribution'].items():
        if stats['count'] > 0:
            print(f"  - {reason}: {stats['count']} 个query")
    
    print("\n" + "=" * 60)
    print("✅ 所有检查通过！系统工作正常。")
    print("=" * 60)
    print(f"\n📁 测试报告已生成在: ./test_output/")
    print(f"📄 打开 test_output/analysis_report.html 查看详细报告")
    print("\n💡 下一步：")
    print("  1. 准备您的数据文件")
    print("  2. 运行: python main.py --input your_data.json --output ./results")
    print("=" * 60)
    
    return True


if __name__ == '__main__':
    success = test_system()
    sys.exit(0 if success else 1)
