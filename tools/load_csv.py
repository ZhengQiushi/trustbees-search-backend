import pandas as pd
import sys, os
from elasticsearch import Elasticsearch, helpers
import json, ast, csv
from elasticsearch.helpers import streaming_bulk
from concurrent.futures import ThreadPoolExecutor
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
csv_file = '/Users/lion/Project/trustbees-search-backend/merged_test_data_20250309_115450.csv'

df = pd.read_csv(csv_file)

# 将 NaN 替换为 None
df = df.where(pd.notnull(df), None)

# 定义 safe_literal_eval 函数
def safe_literal_eval(value, field_name=None):
    if value is None or value == '' or pd.isna(value):  # 处理 NaN 值
        return None
    try:
        # 特判处理 ageGroup、location 和 schedule 字段
        if field_name in ['ageGroup', 'location', 'schedule']:
            if isinstance(value, str):
                # 修复单引号问题
                value = value.replace("'", '"')
                # 修复 None -> null
                value = value.replace("None", "null")
                return json.loads(value)  # 尝试将字符串 JSON 转换为字典
            
        return ast.literal_eval(value)  # 尝试将字符串 JSON 转换为字典
    except (ValueError, SyntaxError):
        return value  # 如果转换失败，返回原始值

# 对每一列应用 safe_literal_eval
for col in df.columns:
    df[col] = df[col].apply(lambda x: safe_literal_eval(x, field_name=col))

# 将 DataFrame 转换为字典列表
records = df.to_dict(orient='records')

# 定义 Elasticsearch 索引名称
index_name = 'offerings_v2'

# 读取CSV文件并生成数据的函数
def gendata(offset, limit):
    for i, row in enumerate(records):
        if i < offset:
            continue
        if i >= offset + limit:
            break
        yield {
            '_index': index_name,
            '_source': row
        }

# 每个线程的任务函数
def insert_data(offset, limit=1000):
    try:
        success_count = 0
        for ok, response in streaming_bulk(client, gendata(offset, limit), chunk_size=1000):
            if not ok:
                print(f"文档插入失败: {response}")
            else:
                success_count += 1
        print(f"线程 {offset} 成功导入 {success_count} 条数据！")
    except Exception as e:
        print(f"线程 {offset} 数据导入失败: {e}")
        if hasattr(e, 'errors'):
            for error in e.errors:
                print(f"错误详情: {error}")

# 主函数
def main():
    # 假设CSV文件有10000行数据
    total_rows = 10000
    chunk_size = 1000
    threads = []

    # 使用ThreadPoolExecutor来管理线程池
    with ThreadPoolExecutor(max_workers=5) as executor:
        for offset in range(0, total_rows, chunk_size):
            # 提交任务到线程池
            future = executor.submit(insert_data, offset, chunk_size)
            threads.append(future)

        # 等待所有线程完成
        for future in threads:
            future.result()

if __name__ == "__main__":
    main()