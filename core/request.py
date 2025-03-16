from abc import ABC, abstractmethod
from flask import request, jsonify
import logging
from datetime import datetime
import pandas as pd
import sys, os
# 将项目根目录添加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from utils.parse_args import *
import global_vars

logger = logging.getLogger(__name__)

class AbstractRequest(ABC):
    def __init__(self, request_args):
        self.request_args = request_args
        self.params = self.parse_args()

    @abstractmethod
    def parse_args(self):
        """解析请求参数"""
        pass

    @abstractmethod
    def build_query(self):
        """构建 Elasticsearch 查询"""
        pass

    @abstractmethod
    def request_query(self):
        """执行 Elasticsearch 查询"""
        pass

    @abstractmethod
    def postprocess(self, response):
        """处理查询结果"""
        pass

    @abstractmethod
    def merge_result(self, response):
        """合并查询结果"""
        pass

    def common_query_params(self):
        """返回通用的查询参数"""
        return {
            "from": self.params.page_offset * self.params.page_len,
            "size": self.params.page_len,
            "_source": {
                "excludes": ["pages", "*Embeddings"]
            }
        }

    def execute(self):
        try:
            query = self.build_query()
            response = self.request_query(query)
            response = self.postprocess(response)
            result = self.merge_result(response)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Invalid request, request={request}, info={str(e)}")
            return jsonify({"error": f"Invalid request, request={request}, info={str(e)}"}), 400


class RequestBusinessID(AbstractRequest):
    def parse_args(self):
        return SearchBusinessIDParams(self.request_args)

    def build_query(self):
        query = {
            "query": {
                "term": {
                    "businessID": self.params.business_id
                }
            },
            **self.common_query_params()
        }
        return query

    def request_query(self, query):
        return global_vars.es.search(index=global_vars.config['ELASTICSEARCH_PROVIDER'], body=query)

    def postprocess(self, response):
        return business_postprocess(response)

    def merge_result(self, response):
        hits = [hit['_source'] for hit in response['hits']['hits']]
        total_hits = response['hits']['total']['value']
        return {
            "data": hits,
            "total_hits": total_hits
        }


class RequestBusinessFullName(AbstractRequest):
    def parse_args(self):
        return SearchBusinessNameParams(self.request_args)

    def build_query(self):
        query = {
            "query": {
                "multi_match": {
                    "query": self.params.business_name,
                    "fields": ["businessFullName"],
                    "type": "most_fields",
                    "fuzziness": "AUTO",
                    "operator": "or",
                    "minimum_should_match": "50%"
                }
            },
            **self.common_query_params()
        }
        return query

    def request_query(self, query):
        return global_vars.es.search(index=global_vars.config['ELASTICSEARCH_PROVIDER'], body=query)

    def postprocess(self, response):
        return business_postprocess(response)

    def merge_result(self, response):
        hits = [hit['_source'] for hit in response['hits']['hits']]
        total_hits = response['hits']['total']['value']
        return {
            "data": hits,
            "total_hits": total_hits
        }


class RequestOfferingSearch(AbstractRequest):
    def parse_args(self):
        return SearchOfferingParams(self.request_args)

    def build_query(self):
        query = {
            "query": {
                "bool": {
                    "must": [],
                    "filter": [],
                    "should": []
                }
            },
            **self.common_query_params(),
            "collapse": {
                "field": "businessID"
            },
            "aggs": {
                "unique_business_count": {
                    "cardinality": {
                        "field": "businessID"
                    }
                }
            }
        }

        if self.params.search:
            query["query"]["bool"]["must"].append({
                "multi_match": {
                    "query": self.params.search,
                    "fields": [
                        "activity^5",
                        "activityCategory^5",
                        "offeringName^3",
                        "businessFullName^1",
                        "offeringInsightSummary^1"
                    ],
                    "type": "most_fields",
                    "fuzziness": "1",
                    "operator": "or",
                    # "minimum_should_match": "50%"
                }
            })
        else:
            query["query"]["bool"]["must"].append({
                "match_all": {}
            })

        if self.params.lat and self.params.lon and self.params.radius:
            query["query"]["bool"]["should"].append({
                "bool": {
                    "must": [
                        {
                            "geo_distance": {
                                "distance": f"{self.params.radius}miles",
                                "location.geo_info": {
                                    "lat": self.params.lat,
                                    "lon": self.params.lon
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

        query["query"]["bool"]["should"].append({
            "term": {
                "locationType": "online"
            }
        })

        query["query"]["bool"]["minimum_should_match"] = 1

        if self.params.ages:
            for age in self.params.ages:
                query["query"]["bool"]["filter"].append({
                    "range": {
                        "ageGroup": {
                            "gte": age,
                            "lte": age
                        }
                    }
                })

        if self.params.camp_types and "AnyType" not in self.params.camp_types:
            query["query"]["bool"]["filter"].append({
                "bool": {
                    "must": [
                        {"term": {"campSessionOptions": camp_type}} for camp_type in self.params.camp_types
                    ]
                }
            })

        if self.params.camp_options:
            indoor_selected = "Indoor" in self.params.camp_options
            outdoor_selected = "Outdoor" in self.params.camp_options

            if indoor_selected and outdoor_selected:
                query["query"]["bool"]["filter"].append({
                    "term": {
                        "facility": "both"
                    }
                })
            elif indoor_selected:
                query["query"]["bool"]["filter"].append({
                    "terms": {
                        "facility": ["both", "indoor"]
                    }
                })
            elif outdoor_selected:
                query["query"]["bool"]["filter"].append({
                    "terms": {
                        "facility": ["both", "outdoor"]
                    }
                })

            for option in self.params.camp_options:
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

        query["query"]["bool"]["filter"].append({
            "nested": {
                "path": "schedule",
                "query": {
                    "range": {
                        "schedule.endDate": {
                            "gte": datetime.now().strftime("%Y-%m-%d")
                        }
                    }
                }
            }
        })

        return query

    def request_query(self, query):
        return global_vars.es.search(index=global_vars.config['ELASTICSEARCH_OFFERING'], body=query)

    def postprocess(self, response):
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
                    hit['_source']['location'] = parse_location(hit['_source']['location'])
            return response
        return offering_postprocess(response)

    def merge_result(self, response):
        hits = [hit['_source'] for hit in response['hits']['hits']]
        unique_business_count = response['aggregations']['unique_business_count']['value']
        return {
            "data": hits,
            "total_hits": unique_business_count
        }
    


def business_postprocess(response):
    """
    处理 Elasticsearch 查询结果中的字段转换。
    
    :param response: Elasticsearch 查询结果
    :return: 处理后的查询结果
    """
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

        # todo 临时处理
        if 'teyaScore' not in hit['_source']:
            hit['_source']['teyaScore'] = 0
        
        # 处理 mainOfferingAddress 字段
        if 'mainOfferingAddress' in hit['_source']:
            hit['_source']['mainOfferingAddress'] = parse_location(hit['_source']['mainOfferingAddress'])
        
        if 'additionalOfferingAddress' in hit['_source']:
            for i, _ in enumerate(hit['_source']['additionalOfferingAddress']):
                hit['_source']['additionalOfferingAddress'][i] = parse_location(hit['_source']['additionalOfferingAddress'][i])

    return response