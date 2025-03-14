from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
import logging
import argparse
from dotenv import dotenv_values
import utils
import pandas as pd
from utils.utils import *
from datetime import datetime  # 导入 datetime 模块
import re
from flask import request, jsonify


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


class SearchParams:
    VALID_CAMP_TYPES = {"Anytype", "Full Day", "Half Day", "Sleepaway"}
    VALID_CAMP_OPTIONS = {"Indoor", "Outdoor", "Lunch", "EarlyDropoff", "Transportation", "LatePickup"}

    def __init__(self, request_args):
        self.search = request_args.get("search")
        self.zip_code = request_args.get("zipCode")
        self.radius = request_args.get("radius")
        self.ages = request_args.getlist("age")
        self.camp_types = request_args.getlist("campType")
        self.camp_options = request_args.getlist("campOptions")
        self.page_offset = request_args.get("pageOffset", "0")
        self.page_len = request_args.get("pageLen", "15")
        self.lat = None
        self.lon = None

        # 1. 必填参数校验
        if not self.zip_code or not self.radius:
            raise ValueError("Invalid parameters: zipCode, and radius are required.")

        # 2. zip_code 必须是 5 位数字
        if not re.fullmatch(r"\d{5}", self.zip_code):
            raise ValueError(f"Invalid zip_code: '{self.zip_code}', expected a 5-digit string.")

        # 3. radius 必须是数字
        if not self._is_number(self.radius):
            raise ValueError(f"Invalid radius: '{self.radius}', expected a number.")

        # 5. age（如果有）必须是数字
        for age in self.ages:
            if age is not None and not self._is_number(age):
                raise ValueError(f"Invalid age: '{age}', expected an integer.")

        # 6. camp_types 只能包含指定值
        for camp_type in self.camp_types:
            if camp_type not in self.VALID_CAMP_TYPES:
                raise ValueError(f"Invalid camp_type: '{camp_type}', expected one of {self.VALID_CAMP_TYPES}.")

        # 7. camp_options 只能包含指定值
        for camp_option in self.camp_options:
            if camp_option not in self.VALID_CAMP_OPTIONS:
                raise ValueError(f"Invalid camp_option: '{camp_option}', expected one of {self.VALID_CAMP_OPTIONS}.")

        # 8. page_offset 和 page_len 必须是数字
        if not self._is_number(self.page_offset):
            raise ValueError(f"Invalid page_offset: '{self.page_offset}', expected a number.")

        if not self._is_number(self.page_len):
            raise ValueError(f"Invalid page_len: '{self.page_len}', expected a number.")
        
        # 将邮编转换为经纬度
        try:
            self.lat, self.lon = get_lat_lon_from_zip(self.zip_code)
        except Exception as e:
            raise ValueError(f"Invalid zipcode: '{self.zip_code}', failed to parse to lat and lon. {str(e)}")
        
        if not self.lat or not self.lon:
            raise ValueError(f"Invalid zipcode: '{self.zip_code}', failed to parse to lat and lon.")


    @staticmethod
    def _is_number(value):
        """检查值是否为数字"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False


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
            if 'zipcode' not in main_offering_address:
                main_offering_address['zipcode'] = ""  # 默认值为空字符串

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
            "multi_match": {
                "query": business_full_name,
                "fields": ["businessFullName"],  # 可以指定多个字段
                "type": "most_fields",  # 使用 most_fields 类型
                "fuzziness": "AUTO",  # 允许单复数变化、拼写误差
                "operator": "or",
                "minimum_should_match": "50%"  # 增强匹配宽容度
            }
        },
        "_source": {
            "excludes": ["pages", "*Embeddings"]  # 排除 pages 字段
        }
    }

    # 执行查询
    response = es.search(index=config['ELASTICSEARCH_PROVIDER'], body=query)
    # 处理 interests 字段

    response = business_postprocess(response)

    hits = merge_result(response)

    return jsonify(hits)


@app.route('/GetBusinessID', methods=['GET'])
def get_business_id():
    business_id = request.args.get('businessID')
    if not business_id:
        return jsonify({"error": "businessID parameter is required"}), 400

    # 构建 Elasticsearch 查询
    query = {
        "query": {
            "term": {
                "businessID": business_id
            }
        },
        "_source": {
            "excludes": ["pages", "*Embeddings"]
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


def build_es_query(params, has_semantic=False):
    """构建 Elasticsearch 查询"""
    query = {
        "query": {
            "bool": {
                "must": [],  # 初始化为空，根据 search 参数决定是否添加 multi_match
                "filter": [],
                "should": []  # 用于处理 online 课程
            },
        },
        "from": params.page_offset,  # 分页偏移量
        "size": params.page_len,      # 每页长度
        "_source": {
            "excludes": ["*Embeddings"]  # 排除 Embeddings 字段
        },
        "collapse": {
            "field": "businessID"
        }
    }

    # 如果 search 参数不为空，添加 multi_match 查询
    if params.search:
        query["query"]["bool"]["must"].append({
            "multi_match": {
                "query": params.search,
                "fields": [
                    "activity^5",
                    "activityCategory^5",
                    "offeringName^3",
                    "businessFullName^1",
                    "offeringInsightSummary^1"
                ],
                "type": "most_fields",
                "fuzziness": "AUTO",  # 允许单复数变化、拼写误差
                "operator": "or",
                "minimum_should_match": "50%"  # 增强匹配宽容度
            }
        })
    else:
        # 如果 search 参数为空，添加 match_all 查询
        query["query"]["bool"]["must"].append({
            "match_all": {}
        })

    # 距离筛选（仅适用于 locationType 为 in_person）
    if params.lat and params.lon and params.radius:
        query["query"]["bool"]["should"].append({
            "bool": {
                "must": [
                    {
                        "geo_distance": {
                            "distance": f"{params.radius}miles",
                            "location.geo_info": {
                                "lat": params.lat,
                                "lon": params.lon
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

    # 语义检索部分
    if has_semantic:
        query["query"]["bool"]["should"].extend([
            {
                "semantic": {
                    "field": "businessFullNameEmbeddings",
                    "query": params.search
                }
            },
            # {
            #     "semantic": {
            #         "field": "offeringInsightSummaryEmbeddings",
            #         "query": params.search
            #     }
            # },
            {
                "semantic": {
                    "field": "offeringNameEmbeddings",
                    "query": params.search
                }
            }
        ])
    
    if True:
        # 年龄筛选
        if params.ages:
            for age in params.ages:
                query["query"]["bool"]["filter"].append({
                    "range": {
                        "ageGroup": {
                            "gte": age,  # ageGroup 的下限小于等于传入的 age
                            "lte": age   # ageGroup 的上限大于等于传入的 age
                        }
                    }
                })
        # Camp Type 筛选
        if params.camp_types:
            if "Anytype" not in params.camp_types:
                # 将 camp_types 中的值转换为小写，以匹配 ES 中的存储格式
                lower_camp_types = [camp_type.lower() for camp_type in params.camp_types]
                
                # 添加 terms 查询
                query["query"]["bool"]["filter"].append({
                    "terms": {
                        "campSessionOptions": lower_camp_types
                    }
                })

        # Camp Options 筛选
        if params.camp_options:
            # 处理 Indoor 和 Outdoor 选项
            indoor_selected = "Indoor" in params.camp_options
            outdoor_selected = "Outdoor" in params.camp_options

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

        if params.camp_options:
            for option in params.camp_options:
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
                            "latePickup": "yes"
                        }
                    })

    # 筛选 schedule 中的 endDate，排除已过期的课程
    today = datetime.now().strftime("%Y-%m-%d")  # 获取当前日期
    if config['ELASTICSEARCH_OFFERING'] == 'offerings_v2':
        today = "1978-01-01"  # 仅用于测试，将 endDate 限制在 2022 年 1 月 1 日之后

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
    params = None
    try:
        params = SearchParams(request.args)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # 构建 Elasticsearch 查询
    query = build_es_query(params)

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
                if location['geo_info'] is None:
                    # 处理 geo_info 为 None 的情况
                    hit['_source']['location'] = {
                        'lat': None,
                        'lon': None,
                        'name': location.get('name', ''),
                        'zipcode': location.get('zipcode', '')  # 使用获取到的 zipCode 或空字符串
                    }
                else:
                    hit['_source']['location'] = {
                        'lat': location['geo_info'].get('lat',""),
                        'lon': location['geo_info'].get('lon',""),
                        'name': location.get('name', ''),
                        'zipcode': location.get('zipcode', '')  # 使用获取到的 zipCode 或空字符串
                    }

    return response

if __name__ == '__main__':
    print(f"Starting server on {config['HOST']}:{config['PORT']}")
    app.run(debug=True, port=config['PORT'], host=config['HOST'])