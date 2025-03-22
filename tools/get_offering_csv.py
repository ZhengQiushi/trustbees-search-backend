from elasticsearch import Elasticsearch
import pandas as pd
import sys, os

# 将项目根目录添加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

import global_vars

global_vars.init_globals("/Users/lion/Project/trustbees-search-backend/config_prod.env")

name = "provider_prod"

# 初始化 Elasticsearch 客户端
client = Elasticsearch(
    global_vars.config['ES_HOST'],
    api_key=global_vars.config['ES_API_KEY']
)

# 获取索引的映射
mapping = client.indices.get_mapping(index=name)
properties = mapping[name]['mappings']['properties']

# 动态提取所有字段
fields = list(properties.keys())

# 初始化变量
all_data = []
batch_size = 2000
from_record = 0

while True:
    # 查询数据
    response = client.search(
        index=name,
        body={
            "query": {
                "match_all": {}
            },
            "_source": {
                "excludes": ["*Embeddings", "pages"]
            },
            "from": from_record,
            "size": batch_size
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

    # 将当前批次的数据添加到总数据中
    all_data.extend(data)

    # 如果没有更多数据，退出循环
    if len(response['hits']['hits']) < batch_size:
        break

    # 更新 from_record 以获取下一批次的数据
    from_record += batch_size
    print(from_record)

# 将数据转换为 DataFrame
df = pd.DataFrame(all_data)

# 保存为 CSV 文件
df.to_csv(f"{name}.csv", index=False)

print(f"数据已成功保存为 {name}.csv")