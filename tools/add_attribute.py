import csv
from elasticsearch import Elasticsearch, helpers
import logging

import sys, os

# 将项目根目录添加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import global_vars, argparse

global_vars.init_globals('config.env')

import sys, os

# 将项目根目录添加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# 配置Elasticsearch
es_config = {
    "hosts": global_vars.config.get("ES_HOST"),
    "api_key": global_vars.config.get("ES_API_KEY"),
    "timeout": 60,
    "max_retries": 3,
    "retry_on_timeout": True
}
index_name = "offering_dev"

es = Elasticsearch(**es_config)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ESUpdateProcess")

# CSV文件路径
csv_file_path = '/Users/lion/Project/trustbees-search-backend/merged_table_offering.csv'  # 替换为你的CSV文件路径

def update_es_documents(county, state, nums):
    try:
        with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            cnt = 0
            for row_number, row in enumerate(reader, start=0):  # 从0开始计数行号
                # if county and row.get('County') != county:
                #     continue

                # if state and row.get('State', '') != '' and row.get('State') != state:
                #     continue
                
                offering_id = row.get('offeringID')
                rating = row.get('Rating')
                rating_count = row.get('Rating Count')
                if not rating or not rating_count:
                    logger.warning(f"行号 {row_number} 的 Rating 或 Rating Count 为空，跳过更新")
                    continue
                
                # 构造更新脚本
                update_script = {
                    "script": {
                        "source": """
                            ctx._source.googleReviewRating = params.rating;
                            ctx._source.googleReviewCount = params.rating_count;
                        """,
                        "lang": "painless",
                        "params": {
                            "rating": float(rating),
                            "rating_count": int(float(rating_count)),
                        }
                    }
                }
                
                # 更新Elasticsearch文档
                try:
                    es.update(
                        index=index_name,
                        id=offering_id,
                        body=update_script
                    )
                    logger.info(f"成功更新文档 {offering_id}，Rating: {rating}, Rating Count: {rating_count}")
                    cnt += 1
                    if cnt >= nums:
                        break
                except Exception as e:
                    logger.error(f"更新文档 {offering_id} 失败: {str(e)}")
                    continue
                
    except Exception as e:
        logger.error(f"读取CSV文件或更新ES时发生错误: {str(e)}")

if __name__ == "__main__":
    update_es_documents("", "", 10000)