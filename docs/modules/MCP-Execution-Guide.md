# MCP 代码执行指南

## 概述

本文档指导 LLM 在何时和如何生成代码，以便通过 MCP (Model Context Protocol) 代码执行引擎安全执行。

## 一、何时生成代码？

### ✅ 应该生成代码的场景

#### 1. 数据查询与筛选
**触发条件**：用户要求从数据中提取特定信息

```
用户：「在 data.csv 中查找状态为 'Active' 的用户数」
生成：
import pandas as pd
df = pd.read_csv('data.csv')
count = (df['status'] == 'Active').sum()
print(count)
```

**关键词**：query, select, filter, search, find, extract, match

#### 2. 数据格式转换
**触发条件**：用户需要在不同格式间转换数据

```
用户：「将 XML 转换为 JSON 格式」
生成：
import json
import xml.etree.ElementTree as ET
tree = ET.parse('data.xml')
root = tree.getroot()
data = xml_to_dict(root)
json.dump(data, open('output.json', 'w'))
```

**关键词**：convert, transform, parse, format, serialize

#### 3. 数据聚合与统计
**触发条件**：用户需要汇总或统计数据

```
用户：「计算每个月的销售总额」
生成：
import pandas as pd
df = pd.read_csv('sales.csv')
monthly = df.groupby('month')['amount'].sum()
print(monthly)
```

**关键词**：calculate, aggregate, sum, count, average, statistics, analyze

#### 4. 数据处理与清洗
**触发条件**：用户需要处理原始或脏数据

```
用户：「清除数据中的重复项和空值」
生成：
import pandas as pd
df = pd.read_csv('raw_data.csv')
df = df.drop_duplicates()
df = df.dropna()
df.to_csv('clean_data.csv', index=False)
```

**关键词**：clean, process, filter, transform, deduplicate

#### 5. 代码验证与测试
**触发条件**：用户明确要求测试代码逻辑

```
用户：「验证这个算法是否正确」
生成：
def verify_algorithm(input_data):
    result = algorithm(input_data)
    assert result == expected_output
    print("Algorithm verified!")
```

**关键词**：verify, test, validate, check, assert

### ❌ 不应该生成代码的场景

#### 1. 纯思考和分析
```
用户：「讨论 AI 的伦理问题」
不生成代码 → 直接进行 LLM 推理
```

#### 2. 创意写作和内容生成
```
用户：「写一篇关于机器学习的文章」
不生成代码 → 使用 LLM 文本生成能力
```

#### 3. 概念解释
```
用户：「解释什么是递归」
不生成代码 → 文字说明和概念描述
```

#### 4. 开放式建议
```
用户：「给我一些项目管理的建议」
不生成代码 → 知识性推理和建议生成
```

## 二、代码质量约束

### 必须遵守的规则

#### 1. 安全性约束

```python
# ❌ 禁止：系统访问
import os
os.system('rm -rf /')

# ❌ 禁止：动态执行
eval(user_input)
exec(code_string)

# ❌ 禁止：文件系统写操作（除了输出文件）
with open('/etc/passwd', 'w') as f:
    f.write('malicious')
```

#### 2. 资源限制意识

```python
# ❌ 不好：无限循环或长时间执行
while True:
    process_data()

# ✅ 好：有明确的停止条件和超时
for i in range(1000):  # 明确的迭代次数
    process_data()

# ✅ 好：分批处理
for chunk in pd.read_csv('huge_file.csv', chunksize=1000):
    process_chunk(chunk)
```

#### 3. 错误处理

```python
# ❌ 不好：忽略错误
df = pd.read_csv('file.csv')

# ✅ 好：显式错误处理
try:
    df = pd.read_csv('file.csv')
except FileNotFoundError:
    print("File not found")
except Exception as e:
    print(f"Error: {e}")
```

#### 4. 输出清晰性

```python
# ❌ 不好：输出混乱
result = df.describe()
print(result)

# ✅ 好：结构化输出
result = df.describe()
print("=== Data Summary ===")
print(f"Total rows: {len(df)}")
print(f"Null values: {df.isnull().sum().sum()}")
print(result)
```

## 三、沙箱 API 参考

### 可用的库

#### 数据处理
```python
import pandas as pd          # 数据框操作
import numpy as np           # 数值计算
```

#### Web 请求
```python
import requests              # HTTP 请求
import json                  # JSON 解析
```

#### 日期时间
```python
from datetime import datetime, timedelta
import time
```

#### 文件格式
```python
import csv                   # CSV 处理
import json                  # JSON 处理
import xml.etree.ElementTree # XML 处理
import yaml                  # YAML 处理（可选）
```

#### 数学与统计
```python
import math                  # 数学函数
from statistics import mean, median, stdev
import random
```

### 不可用的库

```python
# ❌ 系统操作
import os
import subprocess
import sys

# ❌ 文件操作（危险的）
# 注意：只能读取，不能写到系统目录

# ❌ 网络操作（受限）
import socket
import paramiko

# ❌ 动态执行
import importlib
__import__
eval
exec
```

## 四、代码模板

### 模板 1：数据查询
```python
import pandas as pd

# 读取数据
df = pd.read_csv('path/to/file.csv')

# 筛选数据
filtered = df[df['column'] == 'value']

# 统计结果
result = filtered.groupby('category').size()

# 输出结果
print(result)
```

### 模板 2：数据转换
```python
import pandas as pd
import json

# 读取源数据
df = pd.read_csv('input.csv')

# 转换格式
data_dict = df.to_dict(orient='records')

# 输出目标格式
with open('output.json', 'w') as f:
    json.dump(data_dict, f, indent=2)

print("Conversion completed")
```

### 模板 3：数据验证
```python
import pandas as pd

# 读取数据
df = pd.read_csv('data.csv')

# 执行验证
is_valid = True
if df.isnull().sum().sum() > 0:
    print("⚠️ Contains null values")
    is_valid = False

if len(df) == 0:
    print("⚠️ Empty dataframe")
    is_valid = False

# 输出结果
print("✅ Data is valid" if is_valid else "❌ Data validation failed")
```

### 模板 4：API 调用与处理
```python
import requests
import json

# 构建请求
url = "https://api.example.com/data"
params = {'key': 'value'}

try:
    # 发送请求
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    
    # 解析响应
    data = response.json()
    
    # 处理数据
    result = [item for item in data if item['status'] == 'active']
    
    # 输出结果
    print(f"Found {len(result)} active items")
    print(json.dumps(result, indent=2))
    
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
```

## 五、常见错误排查

### 错误 1：ImportError
```
错误：ModuleNotFoundError: No module named 'scipy'
原因：库不在沙箱环境中
解决：使用备选库或重新设计逻辑
```

### 错误 2：超时 (Timeout)
```
错误：Code execution timeout after 30 seconds
原因：代码执行耗时过长
解决：
- 减少数据量
- 优化算法
- 添加进度输出
```

### 错误 3：内存溢出
```
错误：MemoryError or ResourceExceeded
原因：处理数据过大
解决：
- 分批处理
- 使用 chunking
- 优化数据结构
```

### 错误 4：文件不存在
```
错误：FileNotFoundError: [Errno 2] No such file
原因：文件路径错误
解决：
- 检查文件名
- 提供完整路径
- 验证文件存在
```

## 六、LLM 提示词模板

将以下内容添加到系统 Prompt：

### 路由决策提示
```
当用户请求以下操作时，使用代码执行（MCP）：
- 数据查询或筛选
- 格式转换
- 数据聚合或统计
- 复杂计算
- 数据验证

当用户请求以下操作时，使用纯推理（LLM）：
- 解释概念
- 提供建议
- 创意写作
- 思考分析
- 开放式讨论
```

### 代码生成提示
```
生成代码时，必须遵守：
1. 安全性：禁止系统操作、动态执行、恶意操作
2. 清晰性：添加注释，结构化输出
3. 鲁棒性：错误处理，边界条件检查
4. 效率：考虑性能和资源限制
5. 可测试性：代码应该可验证
```

### 降级提示
```
如果代码执行失败，自动降级到纯 LLM 推理：
- 如果代码运行超时，改用逐步说明
- 如果库不可用，改用备选方案讲解
- 如果权限不足，改用理论分析
```

## 七、执行流程图

```
用户输入
  ↓
ExecutionRouter.route()
  ├─ 匹配 Skill？
  │   └─ 是 (高置信度) → Skill 执行
  │       ├─ 成功 → 返回结果
  │       └─ 失败 → 降级
  │
  ├─ 结构化任务？
  │   └─ 是 → MCP 代码生成 & 执行
  │       ├─ 成功 → 返回结果
  │       └─ 失败 (超时/错误) → 降级
  │
  └─ 否 → LLM 推理执行
      └─ 直接使用 LLM 推理能力
```

## 八、最佳实践清单

- [ ] 代码包含适当的注释
- [ ] 使用了异常处理
- [ ] 避免了禁止的库/操作
- [ ] 考虑了性能和资源
- [ ] 输出格式清晰
- [ ] 代码可以在 30 秒内完成
- [ ] 没有无限循环
- [ ] 变量名有意义
- [ ] 包含了进度反馈
- [ ] 能够优雅地处理边界情况

## 九、示例对话

### 例子 1：成功的代码执行路径
```
用户：「在 sales.csv 中找出销售额超过 1000 的订单数」

LLM 决策：检测到「查询」和「CSV」关键词 → MCP 代码执行

生成代码：
import pandas as pd
df = pd.read_csv('sales.csv')
count = (df['amount'] > 1000).sum()
print(f"Found {count} orders with sales > 1000")

执行结果：Found 42 orders with sales > 1000

返回给用户：
✅ 找到 42 笔销售额超过 1000 的订单。

下一步：可以继续分析这些订单的其他属性。
```

### 例子 2：降级到 LLM 推理
```
用户：「我想了解机器学习的基本原理」

LLM 决策：这是一个概念解释问题 → LLM 推理

响应：
机器学习是一种人工智能的分支...
[详细的文字解释]
```

## 十、常见 Q&A

**Q: 为什么有时候我的代码没有生成？**
A: ExecutionRouter 可能判断这是一个非结构化任务。如果你确实需要代码，可以明确说「用 Python 写...」。

**Q: 代码执行超时了怎么办？**
A: 检查代码的效率。如果处理大量数据，使用分批处理（chunking）。

**Q: 能否执行网络请求？**
A: 可以，但仅限于使用 requests 库的 HTTP 请求。WebSocket 和其他协议不支持。

**Q: 生成的代码有错误怎么办？**
A: 系统会自动降级到 LLM 推理模式。你可以询问 LLM 手动修复代码。

**Q: 我能读取系统文件吗？**
A: 不能。只能读取在沙箱环境中的文件或通过 requests 获取的数据。
