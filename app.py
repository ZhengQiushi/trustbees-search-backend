from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
import logging
import config  # Import the config file
import argparse

app = Flask(__name__)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/query.log'),  # 日志写入文件
        logging.StreamHandler()  # 日志输出到控制台
    ]
)
logger = logging.getLogger(__name__)

# 连接到 Elasticsearch
es = Elasticsearch(
        config.ELASTICSEARCH_URL,
        api_key=config.ELASTICSEARCH_API_KEY
    )

# 接口1: 精确匹配 businessFullName
@app.route('/GetBusinessFullName', methods=['GET'])
def get_business_full_name():
    business_full_name = request.args.get('businessFullName')
    if not business_full_name:
        return jsonify({"error": "businessFullName parameter is required"}), 400

    # 记录日志
    logger.info(f"GetBusinessFullName - businessFullName: {business_full_name}")

    # 构建 Elasticsearch 查询
    query = {
        "query": {
            "term": {
                "businessFullName.keyword": business_full_name
            }
        },
        "_source": {
            "excludes": ["pages"]  # 排除 pages 字段
        }
    }

    # 执行查询
    response = es.search(index="web_content", body=query)
    return jsonify(response['hits']['hits'])

# 接口2: 模糊匹配，支持筛选条件
@app.route('/GetQuery', methods=['GET'])
def get_query():
    query_text = request.args.get('query')
    conditions = request.args.get('conditions')  # 获取筛选条件
    if not query_text:
        return jsonify({"error": "query parameter is required"}), 400

    # 记录日志
    logger.info(f"GetQuery - query: {query_text}, conditions: {conditions}")

    # 解析筛选条件
    filter_conditions = []
    if conditions:
        try:
            conditions = eval(conditions)  # 将字符串转换为字典
            if not isinstance(conditions, dict):
                return jsonify({"error": "conditions must be a JSON object"}), 400

            # 处理地点经纬度 + 距离筛选
            if "location" in conditions and "distance" in conditions:
                lat, lon = conditions["location"].get("lat"), conditions["location"].get("lon")
                distance = conditions["distance"]
                if lat and lon and distance:
                    filter_conditions.append({
                        "geo_distance": {
                            "distance": distance,
                            "mainOfferingAddress.location": {
                                "lat": lat,
                                "lon": lon
                            }
                        }
                    })

            # 处理评价等级筛选
            if "min_rating" in conditions:
                min_rating = float(conditions["min_rating"])
                filter_conditions.append({
                    "range": {
                        "googleReviewRating": {
                            "gte": min_rating
                        }
                    }
                })

        except Exception as e:
            return jsonify({"error": f"Invalid conditions format: {str(e)}"}), 400

    # 构建 Elasticsearch 查询
    query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query_text,
                            "fields": [
                                "businessFullName",
                                "contactPhone",
                                "franchise",
                                "googleReview",
                                "interest",
                                "locationType",
                                "mainOfferingAddress.name",
                                # "pages.content",
                                # "pages.title",
                                "website"
                            ]
                        }
                    }
                ],
                "filter": filter_conditions,  # 添加筛选条件
            }
        },
        "size": 100,  # 指定返回的记录数量
        "_source": {
            "excludes": ["pages"]  # 排除 pages 字段
        }
    }
    # 执行查询
    response = es.search(index="web_content", body=query)
    return jsonify(response['hits']['hits'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the server.')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to run the server on')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    args = parser.parse_args()

    print(f"Starting server on {args.host}:{args.port}")
    # Your server start logic here

    app.run(debug=True, port=args.port, host=args.host)