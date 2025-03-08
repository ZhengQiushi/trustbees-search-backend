from elasticsearch import Elasticsearch
import pandas as pd
import sys, os

# 将项目根目录添加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

# 连接到 Elasticsearch
es = Elasticsearch(
    config.ELASTICSEARCH_URL,
    api_key=config.ELASTICSEARCH_API_KEY
)

# 定义索引名称
index_name = "offerings"
# 更新 mapping，添加新的 activity_text 字段，并使用 copy_to
mapping_update = {
    "properties": {
        "activity": {
            "type": "semantic_text",
            "inference_id": "my-inference-endpoint",
            "model_settings": {
                "task_type": "text_embedding",
                "dimensions": 1536,
                "similarity": "dot_product",
                "element_type": "float"
            },
            "copy_to": "activity_text"  # 将 activity 的值复制到 activity_text
        },
        "activity_text": {  # 新的字段
            "type": "text"
        }
    }
}

# 更新 mapping
try:
    es.indices.put_mapping(index=index_name, body=mapping_update)
    print("Mapping 更新成功！")
except Exception as e:
    print(f"Mapping 更新失败: {e}")
    exit()

# 重新索引数据
try:
    es.update_by_query(index=index_name, conflicts="proceed")
    print("数据重新索引成功！")
except Exception as e:
    print(f"数据重新索引失败: {e}")