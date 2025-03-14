from elasticsearch import Elasticsearch
import pandas as pd
import sys, os

# 将项目根目录添加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

name = "web_content"

# 初始化 Elasticsearch 客户端
client = Elasticsearch(
    config.ELASTICSEARCH_URL,
    api_key=config.ELASTICSEARCH_API_KEY
)

# 定义要提取的字段
fields = [
    "businessFullName",
    "contactPhone",
    "franchise",
    "googleReview",
    "googleReviewCount",
    "googleReviewRating",
    "interest",
    "locationType",
    "mainOfferingAddress",
    "website"
]

# 查询所有数据
response = client.search(
    index=name,
    body={
        "query": {
            "match_all": {}
        },
        "_source": fields,
        "size": 10000  # 你可以根据需要调整这个大小
    }
)

# 提取数据
data = []
for hit in response['hits']['hits']:
    source = hit['_source']
    row = {field: source.get(field, None) for field in fields}
    data.append(row)

# 将数据转换为 DataFrame
df = pd.DataFrame(data)

# 保存为 CSV 文件
df.to_csv(f"{name}.csv", index=False)

print(f"数据已成功保存为 {name}.csv")