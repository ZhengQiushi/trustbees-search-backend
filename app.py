from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
import logging
import argparse
from dotenv import dotenv_values
import utils
import pandas as pd
from utils.utils import *
from datetime import datetime  # 导入 datetime 模块

app = Flask(__name__)

# 解析命令行参数
parser = argparse.ArgumentParser(description='Run the server.')
parser.add_argument('--config', type=str, default='config.env', help='Path to the configuration file')
args = parser.parse_args()

# 加载配置文件
config = dotenv_values(args.config)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config['LOG_FILE']),  # 日志写入文件
        # logging.StreamHandler()  # 日志输出到控制台
    ]
)
logger = logging.getLogger(__name__)



# 连接到 Elasticsearch
es = Elasticsearch(
    config['ELASTICSEARCH_URL'],
    api_key=config['ELASTICSEARCH_API_KEY']
)

def business_postprocess(response):
    """
    处理 Elasticsearch 查询结果中的字段转换。
    
    :param response: Elasticsearch 查询结果
    :return: 处理后的查询结果
    """
    hits = response['hits']['hits']

    for hit in hits:  # 遍历所有记录
        # 处理 interests 字段
        if 'interest' in hit['_source']:
            interests = hit['_source']['interest']
            hit['_source']['interest'] = transform_interests(interests)

        # 处理 contactPhone 字段
        if 'contactPhone' in hit['_source']:
            contact_phone = hit['_source']['contactPhone']
            hit['_source']['contactPhone'] = transform_contact_phone(contact_phone)

        # 临时处理
        if 'teyaScore' not in hit['_source']:
            hit['_source']['teyaScore'] = 0
        
        # 处理 mainOfferingAddress.location 字段
        if 'mainOfferingAddress' in hit['_source']:
            main_offering_address = hit['_source']['mainOfferingAddress']
            # 检查并设置 zipCode
            if 'zipCode' not in main_offering_address:
                main_offering_address['zipCode'] = ""  # 默认值为空字符串

    return response

def transform_contact_phone(contact_phone):
    """
    转换 contactPhone 字段的逻辑。
    
    :param contact_phone: 原始的 contactPhone 字段
    :return: 转换后的 contactPhone 字段（数组形式）
    """
    if isinstance(contact_phone, str):  # 如果是字符串，转换为数组
        return [contact_phone]
    elif isinstance(contact_phone, list):  # 如果已经是数组，直接返回
        return contact_phone
    else:  # 其他情况（如 None 或其他类型），返回空数组
        return []

def merge_result(response):
    """
    将 Elasticsearch 查询结果中的各个 _source 提取出来，合并成一个新的数组。
    
    :param response: Elasticsearch 查询结果
    :return: 包含所有 _source 的数组
    """
    hits = response['hits']['hits']
    return [hit['_source'] for hit in hits]

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
    response = es.search(index=config['ELASTICSEARCH_PROVIDER'], body=query)
    # 处理 interests 字段

    response = business_postprocess(response)

    hits = merge_result(response)

    return jsonify(hits)



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
    response = es.search(index=config['ELASTICSEARCH_PROVIDER'], body=query)
    return jsonify(response['hits']['hits'])


def build_es_query(search, lat, lon, radius, page_offset, page_len, is_detail_search, age, camp_types, camp_options):
    """构建 Elasticsearch 查询"""
    query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": search,
                            "fields": [
                                "activity^5",
                                "activityCategory^5",
                                "offeringName^3",
                                "businessFullName^1",
                                "offeringInsightSummary^1"
                            ],
                            "type": "most_fields"
                        }
                    }
                ],
                "filter": [],
                "should": []  # 用于处理 online 课程
            },
        },
        "from": page_offset,  # 分页偏移量
        "size": page_len,      # 每页长度
        "_source": {
            "excludes": ["*Embeddings"]  # 排除 Embeddings 字段
        },
        # 新增：按商家 ID 去重
        # "collapse": {
        #     "field": "businessFullName.keyword"  # 假设商家 ID 存储在 businessFullName 字段中
        # }
    }

    # 距离筛选（仅适用于 locationType 为 in_person）
    if lat and lon and radius:
        query["query"]["bool"]["should"].append({
            "bool": {
                "must": [
                    {
                        "geo_distance": {
                            "distance": f"{radius}miles",
                            "location.geo_info": {
                                "lat": lat,
                                "lon": lon
                            }
                        }
                    },
                    {
                        "term": {
                            "locationType": "in_person"
                        }
                    }
                ]
            }
        })

    # 添加 online 课程的筛选条件
    query["query"]["bool"]["should"].append({
        "term": {
            "locationType": "online"
        }
    })

    # 设置 minimum_should_match，确保至少满足一个 should 条件
    query["query"]["bool"]["minimum_should_match"] = 1

    # 详细筛选（仅当 is_detail_search 为 true 时）
    if is_detail_search:
        # 年龄筛选
        if age:
            query["query"]["bool"]["filter"].append({
                "range": {
                    "ageGroup": {
                        "gte": age,  # ageGroup 的下限小于等于传入的 age
                        "lte": age   # ageGroup 的上限大于等于传入的 age
                    }
                }
            })
        # Camp Type 筛选
        if camp_types:
            if "Anytype" not in camp_types:
                # 将 camp_types 中的值转换为小写，以匹配 ES 中的存储格式
                lower_camp_types = [camp_type.lower() for camp_type in camp_types]
                
                # 添加 terms 查询
                query["query"]["bool"]["filter"].append({
                    "terms": {
                        "campSessionOptions": lower_camp_types
                    }
                })

        # Camp Options 筛选
        if camp_options:
            # 处理 Indoor 和 Outdoor 选项
            indoor_selected = "Indoor" in camp_options
            outdoor_selected = "Outdoor" in camp_options

            if indoor_selected and outdoor_selected:
                # 如果同时选择了 Indoor 和 Outdoor，只返回 facility 为 Both 的文档
                query["query"]["bool"]["filter"].append({
                    "term": {
                        "facility": "both"
                    }
                })
            elif indoor_selected:
                # 如果只选择了 Indoor，返回 facility 为 Both 或 Indoor 的文档
                query["query"]["bool"]["filter"].append({
                    "terms": {
                        "facility": ["both", "indoor"]
                    }
                })
            elif outdoor_selected:
                # 如果只选择了 Outdoor，返回 facility 为 Both 或 Outdoor 的文档
                query["query"]["bool"]["filter"].append({
                    "terms": {
                        "facility": ["both", "outdoor"]
                    }
                })

        if camp_options:
            for option in camp_options:
                if option == "Lunch":
                    query["query"]["bool"]["filter"].append({
                        "term": {
                            "lunchIncluded": "yes"
                        }
                    })
                elif option == "EarlyDropoff":
                    query["query"]["bool"]["filter"].append({
                        "term": {
                            "earlyDropOff": "yes"
                        }
                    })
                elif option == "Transportation":
                    query["query"]["bool"]["filter"].append({
                        "term": {
                            "transportation": "yes"
                        }
                    })
                elif option == "LatePickup":
                    query["query"]["bool"]["filter"].append({
                        "term": {
                            "LatePickup": "yes"
                        }
                    })

    # 筛选 schedule 中的 endDate，排除已过期的课程
    today = datetime.now().strftime("%Y-%m-%d")  # 获取当前日期
    query["query"]["bool"]["filter"].append({
        "nested": {
            "path": "schedule",  # 嵌套字段路径
            "query": {
                "range": {
                    "schedule.endDate": {
                        "gte": today  # endDate 必须大于等于今天
                    }
                }
            }
        }
    })

    return query

@app.route('/GetOfferingsTextQuery', methods=['GET'])
def get_offerings_text_query():
    # 获取请求参数
    search = request.args.get('search')
    zip_code = request.args.get('zipCode')
    radius = request.args.get('radius')
    is_detail_search = request.args.get('isDetailSearch', 'false').lower() == 'true'
    age = request.args.get('age', type=int)
    camp_types = request.args.getlist('campType')
    camp_options = request.args.getlist('campOptions')
    # 分页参数
    page_offset = request.args.get('pageOffset', '0')
    page_len = request.args.get('pageLen', '15')
    # 校验必须参数
    if not search or not zip_code or not radius:
        return jsonify({"error": "search, zipCode, and radius are required parameters"}), 400


    try:
        # 将邮编转换为经纬度
        lat, lon = get_lat_lon_from_zip(zip_code)
    except Exception as e:
        logger.error(f"Error getting lat/lon from zip code: {str(e)}")
        return jsonify({f"error": "Invalid zipCode. str{e}"}), 400
    
    if not lat or not lon:
        return jsonify({"error": "Invalid zipCode"}), 400

    # 构建 Elasticsearch 查询
    query = build_es_query(search, lat, lon, radius, page_offset, page_len, is_detail_search, age, camp_types, camp_options)

    # 执行查询
    try:
        response = es.search(index=config['ELASTICSEARCH_OFFERING'], body=query)
    except Exception as e:
        return jsonify({"error": f"Invalid search.{str(e)}"}), 400

    # 处理返回结果
    response = offering_postprocess(response)

    # data = [hit['_source'] for hit in response['hits']['hits']]

    # # 将数据转换为 DataFrame
    # df = pd.DataFrame(data)

    # # 保存为 CSV 文件
    # df.to_csv(f"debug.csv", index=False)
    hits = merge_result(response)

    return jsonify(hits)

def offering_postprocess(response):
    """
    处理 Elasticsearch 查询结果中的字段转换。
    
    :param response: Elasticsearch 查询结果
    :return: 处理后的查询结果
    """
    hits = response['hits']['hits']

    for hit in hits:  # 遍历所有记录
        # 处理 location 字段
        if 'location' in hit['_source']:
            location = hit['_source']['location']
            if 'geo_info' in location:
                # 检查是否存在 zipCode，如果不存在则设置为空字符串
                zip_code = location.get('zipCode', "")
                hit['_source']['location'] = {
                    'lat': location['geo_info']['lat'],
                    'lon': location['geo_info']['lon'],
                    'name': location['name'],
                    'zipCode': zip_code  # 使用获取到的 zipCode 或空字符串
                }

    return response

if __name__ == '__main__':
    print(f"Starting server on {config['HOST']}:{config['PORT']}")
    app.run(debug=True, port=config['PORT'], host=config['HOST'])