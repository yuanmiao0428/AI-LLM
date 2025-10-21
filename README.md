# 搜索引擎时效性自动化分析系统

## 📖 系统简介

本系统用于自动化分析搜索引擎test的时效性表现，通过与权威引擎（engine1、engine2）对比，找出时效性差的query，并诊断具体原因。

### 核心功能

✅ **自动化评估**：基于4个维度自动评估每个query的时效性得分  
✅ **原因诊断**：自动诊断3类原因（识别错误、打分公式、融合策略）  
✅ **报告生成**：自动生成JSON、CSV、HTML格式的分析报告  
✅ **可配置化**：所有阈值通过配置文件灵活调整  

---

## 🚀 快速开始

### 1. 环境准备

**Python版本要求**: Python 3.7+

**安装依赖**:
```bash
pip install pandas numpy pyyaml
```

### 2. 准备数据

数据格式为JSON，参考 `sample_data.json`：

```json
[
  {
    "query": "查询文本",
    "search_time": "2025-10-15T10:00:00",
    "engine1": {
      "docs": [
        {
          "url": "文档URL",
          "title": "文档标题",
          "publish_time": "发布时间"
        }
      ],
      "has_timeliness_card": true/false
    },
    "engine2": { ... },
    "test": {
      "docs": [
        {
          "url": "文档URL",
          "title": "文档标题", 
          "publish_time": "发布时间",
          "timeliness_score": 0.85
        }
      ],
      "query_timeliness_level": "高时效" / "其他时效"
    }
  }
]
```

### 3. 运行分析

```bash
# 使用示例数据运行
python main.py --input sample_data.json --output ./results

# 使用自定义配置
python main.py --input your_data.json --output ./output --config config.yaml
```

### 4. 查看结果

```
./results/
├── analysis_report.json    # 完整JSON报告（包含所有细节）
├── analysis_report.html    # 可视化HTML报告（在浏览器中打开）
└── poor_queries.csv        # 时效性差的query列表（Excel可打开）
```

---

## 📊 评估体系

### 时效性评分（0-100分）

系统基于4个维度计算综合得分：

| 维度 | 权重 | 说明 |
|-----|------|-----|
| 平均doc年龄 | 40% | 对比test与baseline的TOP5平均doc年龄 |
| 新鲜文档覆盖率 | 30% | 7天内文档占比 |
| 最新文档发现能力 | 20% | 能否找到最新的文档 |
| 时效卡召回 | 10% | 是否满足时效卡需求 |

**得分判定**：
- **≥70分**: 时效性良好 ✅
- **50-70分**: 时效性一般 ⚠️
- **<50分**: 时效性差 ❌ (需要诊断原因)

---

## 🔍 原因诊断

对于时效性差（<50分）的query，系统按优先级诊断3类原因：

### 原因1：Query时效性等级识别错误（P0）

**判定依据**：
- 两个权威引擎都有时效卡 → 应该是高时效
- 权威引擎平均doc年龄 ≤ 3天 + 新鲜文档占比 ≥ 80% → 应该是高时效

**示例**：
```
Query: "2025年诺贝尔奖获得者"
- engine1、engine2都有时效卡
- 平均doc年龄: 2.1天
- test判别: "其他时效" ❌
→ 诊断: 识别错误
```

### 原因2：Doc时效性打分公式不合理（P1）

**检查指标**：

| 指标 | 高时效阈值 | 其他时效阈值 |
|-----|-----------|-------------|
| doc年龄与打分相关系数 | -1.0 ~ -0.6 | -0.6 ~ -0.2 |
| 打分标准差 | ≥ 0.15 | ≥ 0.05 |
| 新旧文档打分差距 | ≥ 0.3 | ≥ 0.1 |

**示例**：
```
Query: "华为Mate70什么时候发布" (高时效)
- 相关系数: -0.2 (应该 ≤ -0.6) ❌
- 新旧文档打分差: 0.15 (应该 ≥ 0.3) ❌
→ 诊断: 打分公式不合理
```

### 原因3：融合策略不合理（P2）

**检查指标**：
- 理想排序提升潜力 > 30% → 时效性权重过低
- 新文档时效打分高，但排序靠后 → 被其他因素压制

**示例**：
```
Query: "今日新闻"
- 纯按时效性打分排序，平均doc年龄可从15天降至3天 (提升80%) ❌
→ 诊断: 融合权重过低
```

---

## ⚙️ 配置说明

所有阈值在 `config.yaml` 中配置：

```yaml
thresholds:
  # 时效性评估
  poor_score: 50      # 时效性差的阈值
  fair_score: 70      # 时效性一般的阈值
  
  # 评分权重
  weights:
    avg_age: 0.4      # 可调整各维度权重
    fresh_ratio: 0.3
    min_age: 0.2
    card: 0.1
  
  # 原因1：识别错误阈值
  recognition:
    fresh_age_strong: 3    # 强新鲜度: ≤3天
    fresh_ratio_high: 0.8  # 高集中度: ≥80%
  
  # 原因2：打分公式阈值
  scoring:
    high_timeliness:
      corr_min: -1.0       # 高时效的相关系数范围
      corr_max: -0.6
      std_min: 0.15        # 最小标准差
      gap_min: 0.3         # 新旧文档最小差距
  
  # 原因3：融合策略阈值
  fusion:
    improvement_potential: 0.3  # 提升潜力阈值
```

---

## 📋 输出报告说明

### 1. JSON报告 (`analysis_report.json`)

完整的结构化数据，包含：
- 总体统计
- 每个时效性差query的详细诊断
- 改进建议

### 2. HTML报告 (`analysis_report.html`)

可视化报告，包含：
- 📊 总体概况（总query数、时效性差占比）
- 🎯 原因分布（饼图/表格）
- 💡 改进建议（按优先级P0/P1/P2）

直接在浏览器中打开查看。

### 3. CSV报告 (`poor_queries.csv`)

时效性差的query列表，字段包括：
- query
- timeliness_score（时效性得分）
- primary_reason（主要原因）
- test_avg_age（test平均doc年龄）
- baseline_avg_age（baseline平均doc年龄）
- test_query_level（test判别的时效性等级）

可用Excel打开，方便筛选和排序。

---

## 🛠️ 使用示例

### 示例1：基础分析

```bash
python main.py --input data.json --output ./results
```

**输出**：
```
搜索引擎时效性分析系统
==================================================

[1/5] 数据加载与预处理...
✓ 成功加载 1000 个query

[2/5] 特征提取与时效性评估...
✓ 特征提取与评估完成

[3/5] 生成分析报告...
✓ 发现 156 个时效性差的query

[4/5] 导出结果...
✓ JSON报告: ./results/analysis_report.json
✓ HTML报告: ./results/analysis_report.html
✓ CSV报告: ./results/poor_queries.csv

[5/5] 分析完成
==================================================
总query数: 1000
时效性差: 156 (15.6%)

原因分布:
  原因1_识别错误: 78 (50.0%)
  原因2_打分公式: 52 (33.3%)
  原因3_融合策略: 26 (16.7%)
==================================================
```

### 示例2：自定义配置

创建 `my_config.yaml`，调整阈值：

```yaml
thresholds:
  poor_score: 40  # 更严格的标准
  weights:
    avg_age: 0.5  # 增加平均年龄权重
    fresh_ratio: 0.3
    min_age: 0.1
    card: 0.1
```

运行：
```bash
python main.py --input data.json --output ./results --config my_config.yaml
```

---

## 📈 高级功能

### 批量处理多个文件

```python
import glob
from main import TimelinessAnalysisSystem

system = TimelinessAnalysisSystem()

for data_file in glob.glob('data/*.json'):
    output_dir = f"output/{os.path.basename(data_file).replace('.json', '')}"
    system.run(input_file=data_file, output_dir=output_dir)
```

### 提取特定原因的query

```python
import json

with open('results/analysis_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

# 提取识别错误的query
recognition_errors = [
    q for q in report['poor_queries']
    if q.get('diagnosis', {}).get('reason') == '原因1_识别错误'
]

print(f"识别错误的query数量: {len(recognition_errors)}")
for q in recognition_errors[:10]:
    print(f"- {q['query']}")
```

---

## ❓ 常见问题

### Q1: 数据文件格式有误怎么办？

**A**: 检查JSON格式是否正确，确保：
- 时间格式为ISO 8601：`2025-10-15T10:00:00`
- 所有必需字段都存在
- 参考 `sample_data.json` 示例

### Q2: 分析结果中所有query都是"时效性良好"？

**A**: 可能阈值设置过低，调整 `config.yaml` 中的 `poor_score` 和 `fair_score`：
```yaml
thresholds:
  poor_score: 60  # 提高阈值
  fair_score: 80
```

### Q3: 想要更详细的日志信息？

**A**: 修改 `config.yaml` 中的日志级别：
```yaml
logging:
  level: DEBUG  # 改为DEBUG
  file: logs/analysis.log
```

### Q4: 如何只关注高时效query？

**A**: 在分析后过滤：
```python
high_timeliness_poor = [
    q for q in report['poor_queries']
    if q['features']['test_query_level'] == '高时效'
]
```

---

## 📝 数据字段说明

### 输入数据必需字段

| 字段路径 | 类型 | 说明 | 示例 |
|---------|------|-----|------|
| `query` | string | 查询文本 | "今日新闻" |
| `search_time` | string | 搜索时间 | "2025-10-15T10:00:00" |
| `engine1.docs` | array | 引擎1返回的文档列表 | [...] |
| `engine1.docs[].url` | string | 文档URL | "https://..." |
| `engine1.docs[].title` | string | 文档标题 | "新闻标题" |
| `engine1.docs[].publish_time` | string | 发布时间 | "2025-10-14T08:00:00" |
| `engine1.has_timeliness_card` | boolean | 是否有时效卡 | true |
| `engine2.*` | - | 同engine1 | - |
| `test.docs[].timeliness_score` | float | 时效性打分 | 0.85 |
| `test.query_timeliness_level` | string | 时效性等级 | "高时效" / "其他时效" |

---

## 🔧 系统架构

```
输入数据 (JSON/CSV)
    ↓
[数据预处理模块] → 计算doc年龄
    ↓
[特征提取模块] → 提取30+ 特征
    ↓
[时效性评估模块] → 4维度评分 (0-100)
    ↓
[原因诊断模块] → 3层诊断 (P0→P1→P2)
    ↓
[报告生成模块] → JSON/CSV/HTML
    ↓
输出结果
```

---

## 📄 许可证

本项目仅供内部使用。

---

## 📧 联系方式

如有问题或建议，请联系开发团队。

---

## 🎯 下一步

1. 📁 准备您的数据文件（参考 `sample_data.json`）
2. ⚙️ 根据需要调整 `config.yaml` 中的阈值
3. 🚀 运行 `python main.py --input your_data.json`
4. 📊 查看 `output/` 目录中的分析报告
5. 💡 根据改进建议优化搜索引擎

祝分析顺利！🎉
