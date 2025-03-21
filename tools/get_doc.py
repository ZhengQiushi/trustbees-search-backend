from elasticsearch import Elasticsearch
import pandas as pd
import sys, os

# 将项目根目录添加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

name = "zqs_test"

# 初始化 Elasticsearch 客户端
client = Elasticsearch(
    config.ELASTICSEARCH_URL,
    api_key=config.ELASTICSEARCH_API_KEY
)

# 获取索引的映射
mapping = client.indices.get_mapping(index=name)
properties = mapping[name]['mappings']['properties']

# 动态提取所有字段
fields = list(properties.keys())

# 查询所有数据
response = client.search(
    index=name,
    body={
        "query": {
                "match": {
                    "businessID": "3"
                }
        },
        "_source": {
            "excludes": ["*Embeddings"]
        },
        "size": 2000  # 你可以根据需要调整这个大小
    }
)

# 提取数据
data = []
for hit in response['hits']['hits']:
    source = hit['_source']
    row = {}
    for field in fields:
        value = source.get(field, None)
        # 如果值是字典并且包含 'text' 键，则只保留 'text' 的值
        if "Embed" in field:
            continue
        if isinstance(value, dict) and 'text' in value:
            row[field] = value['text']
        else:
            row[field] = value
    data.append(row)

# 将数据转换为 DataFrame
df = pd.DataFrame(data)

# 保存为 CSV 文件
df.to_csv(f"{name}.csv", index=False)

print(f"数据已成功保存为 {name}.csv")