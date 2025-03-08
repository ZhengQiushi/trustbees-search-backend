from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
import logging
import config  # Import the config file
import argparse

import pandas as pd

app = Flask(__name__)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/query.log'),  # 日志写入文件
        # logging.StreamHandler()  # 日志输出到控制台
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
    # logger.info(f"GetBusinessFullName - businessFullName: {business_full_name}")

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
    # logger.info(f"GetQuery - query: {query_text}, conditions: {conditions}")

    # 解析筛选条件
    filter_conditions = []
    page_offset = 0  # 默认偏移量
    page_len = 15    # 默认每页长度

    if conditions:
        try:
            conditions = eval(conditions)  # 将字符串转换为字典
            if not isinstance(conditions, dict):
                return jsonify({"error": "conditions must be a JSON object"}), 400

            # 处理分页参数
            if "page_offset" in conditions:
                page_offset = int(conditions["page_offset"])
            if "page_len" in conditions:
                page_len = int(conditions["page_len"])

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
        "from": page_offset,  # 分页偏移量
        "size": page_len,      # 每页长度
        "_source": {
            "excludes": ["pages"]  # 排除 pages 字段
        }
    }
    # 执行查询
    response = es.search(index="web_content", body=query)
    return jsonify(response['hits']['hits'])


@app.route('/GetOfferingsTextQuery', methods=['GET'])
def get_offerings_text_query():
    # semantic 默认关闭
    query_text = request.args.get('query')
    conditions = request.args.get('conditions')  # 获取筛选条件
    if not query_text:
        return jsonify({"error": "query parameter is required"}), 400

    # 记录日志
    # logger.info(f"GetOfferingsTextQuery - query: {query_text}, conditions: {conditions}")

    # 解析筛选条件
    filter_conditions = []
    page_offset = 0  # 默认偏移量
    page_len = 15    # 默认每页长度
    has_semantic = False  # 默认关闭语义检索

    if conditions:
        try:
            conditions = eval(conditions)  # 将字符串转换为字典
            if not isinstance(conditions, dict):
                return jsonify({"error": "conditions must be a JSON object"}), 400

            # 处理分页参数
            if "page_offset" in conditions:
                page_offset = int(conditions["page_offset"])
            if "page_len" in conditions:
                page_len = int(conditions["page_len"])

            # 处理是否启用语义检索
            if "has_semantic" in conditions:
                has_semantic = bool(conditions["has_semantic"])

            # 处理地点经纬度 + 距离筛选
            if "location" in conditions and "distance" in conditions:
                lat, lon = conditions["location"].get("lat"), conditions["location"].get("lon")
                distance = conditions["distance"]
                if lat and lon and distance:
                    filter_conditions.append({
                        "geo_distance": {
                            "distance": distance,
                            "location.geo_info": {
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

    # 构建基础查询
    retrievers = [
        {
            "standard": {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "multi_match": {
                                    "query": query_text,
                                    "fields": [
                                        "activity^5",
                                        "activityCategory^5",
                                        "offeringName^3",
                                        "businessFullName^1",
                                        "offeringInsightSummary^1"
                                    ],
                                    "type": "most_fields"  # 改为 most_fields，提升性能
                                }
                            }
                        ],
                        "filter": filter_conditions  # 确保 filter 条件被缓存
                    }
                }
            }
        }
    ]

    # 如果启用语义检索，则添加 semantic retriever
    if has_semantic:
        retrievers.append({
            "standard": {
                "query": {
                    "bool": {
                        "should": [
                            {
                                "semantic": {
                                    "field": "activityEmbeddings",
                                    "query": query_text
                                }
                            }
                        ],
                        "minimum_should_match": 1,
                        "filter": filter_conditions  # 在 semantic retriever 中也应用相同的筛选条件
                    }
                }
            }
        })

    # 构建完整查询
    query = {
        "retriever": {
            "rrf": {
                "retrievers": retrievers,
                "rank_window_size": page_len  # 设置为大于或等于 size 的值
            }
        },
        "from": page_offset,  # 分页偏移量
        "size": page_len,     # 每页长度
        "_source": {
            "includes": ["activity", "activityCategory", "offeringName", "businessFullName", "offeringInsightSummary"]  # 只返回必要的字段
        }
    }

    # 执行查询
    response = es.search(index="offerings_v2", body=query)

    # 处理返回结果，
    data = []
    for hit in response['hits']['hits']:
        source = hit['_source']
        data.append(source)

    # 记录日志
    logger.info(f"GetOfferingsTextQuery - query: {query_text}, conditions: {conditions}, results: {len(data)}")

    return jsonify(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the server.')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to run the server on')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    args = parser.parse_args()

    print(f"Starting server on {args.host}:{args.port}")
    # Your server start logic here

    app.run(debug=True, port=args.port, host=args.host)