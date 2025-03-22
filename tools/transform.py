import json
import pandas as pd

# 读取 query.json 文件
with open('/Users/lion/Project/trustbees-search-backend/query.json', 'r') as f:
    data = json.load(f)

# 提取数据
records = []
for hit in data['hits']['hits']:
    if hit['_source'] is not None:
        records.append(hit['_source'])

# 转换为 DataFrame
df = pd.DataFrame(records)

# 导出为 CSV
df.to_csv('output.csv', index=False)

print("数据已导出到 output.csv")