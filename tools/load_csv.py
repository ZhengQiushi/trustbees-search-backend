import pandas as pd
import sys, os
from elasticsearch import Elasticsearch, helpers
import ast
from elasticsearch.helpers import streaming_bulk

# 将项目根目录添加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

# 初始化 Elasticsearch 客户端
client = Elasticsearch(
    config.ELASTICSEARCH_URL,
    api_key=config.ELASTICSEARCH_API_KEY
)

# 读取 CSV 文件
csv_file = '/Users/lion/Project/trustbees-search-backend/tools/offerings.csv'


df = pd.read_csv(csv_file)

# 将 NaN 替换为 None
df = df.where(pd.notnull(df), None)

# 定义 safe_literal_eval 函数
def safe_literal_eval(value):
    if value is None or value == '' or pd.isna(value):  # 处理 NaN 值
        return None
    try:
        return ast.literal_eval(value)  # 尝试将字符串 JSON 转换为字典
    except (ValueError, SyntaxError):
        return value  # 如果转换失败，返回原始值

# 对每一列应用 safe_literal_eval
for col in df.columns:
    df[col] = df[col].apply(safe_literal_eval)


# 将 DataFrame 转换为字典列表
records = df.to_dict(orient='records')

# 定义 Elasticsearch 索引名称
index_name = 'offerings_v2'

# 准备批量插入的数据
# 准备批量插入的数据
actions = [
    {
        "_index": index_name,
        "_source": record
    }
    for record in records
]

# 分批次插入数据
def gendata():
    for record in records:
        yield {
            "_index": index_name,
            "_source": record
        }

# 使用 streaming_bulk 进行分批次插入
try:
    success_count = 0
    for ok, response in streaming_bulk(client, gendata(), chunk_size=1000):  # 每批次 500 条
        if not ok:
            print(f"文档插入失败: {response}")
        else:
            success_count += 1
    print(f"成功导入 {success_count} 条数据！")
except Exception as e:
    print(f"数据导入失败: {e}")
    if hasattr(e, 'errors'):
        for error in e.errors:
            print(f"错误详情: {error}")


# # 使用 helpers.bulk 进行批量插入
# try:
#     response = helpers.bulk(client, actions)
#     print(f"成功导入 {response[0]} 条数据！")
# except Exception as e:
#     print(f"数据导入失败: {e}")
#     # 打印详细的错误信息
#     if hasattr(e, 'errors'):
#         for error in e.errors:
#             print(f"错误详情: {error}")