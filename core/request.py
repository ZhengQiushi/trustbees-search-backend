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
        return {}

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
            "total_hits": len(hits)
        }


class RequestBusinessFullName(AbstractRequest):
    def parse_args(self):
        return SearchBusinessNameParams(self.request_args)

    def build_query(self):
        query = {
            "query": {
                "match_phrase": {
                    "businessFullName": self.params.business_name
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
            "total_hits": len(hits)
        }

class RequestOfferingSearch(AbstractRequest):
    def __init__(self, request_args):
        super().__init__(request_args)
        self.distance_weight = 7
        self.google_review_weight = 3
        self.sum_weight = self.distance_weight + self.google_review_weight

    def parse_args(self):
        return SearchOfferingParams(self.request_args)

    def build_query(self):
        composite = {
                        "size": 1000,  # Number of buckets per page
                        "sources": [
                            {
                                "businessID": {
                                    "terms": {
                                        "field": "businessID"
                                    }
                                }
                            }
                        ],
                    }
    
        # if self.params.page_offset is not None:
        #     composite["after"] = {
        #                     "businessID": self.params.page_offset
        #                 }

        aggs = {
                "group_by_businessID": {
                    "composite": composite,
                    "aggs": {
                        "max_score": {
                            "max": {
                                "script": "_score"
                            }
                        },
                        "top_hits": {
                            "top_hits": {
                                "size": 1,  # Only return the top document per bucket
                                "sort": [
                                    {
                                        "_score": {
                                            "order": "desc"
                                        }
                                    }
                                ],
                                "_source": {
                                    "excludes": "*Emb*"
                                }
                            }
                        },
                        "bucket_sort": {
                            "bucket_sort": {
                                "sort": [
                                    {
                                        "max_score": {
                                            "order": "desc"
                                        }
                                    }
                                ],
                                "size": 50  # Number of buckets to return
                            }
                        }
                    }
                }
            }
       
        query = {
            "size": 1000,  
            "query": {
                "bool": {
                    "must": [],
                    "filter": [],
                    "should": []
                }
            },
            "_source": {"excludes": "*"},
            "aggs": aggs
        }

        query["query"]["bool"]["must"].append({
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": """
                        double platformAverageRating = 0;
                        double threshold = 20.0; // 评论数阈值

                        // 获取店铺评分和评论数
                        double rating = doc['googleReviewRating'].size() > 0 ? doc['googleReviewRating'].value : 0;
                        double count = doc['googleReviewCount'].size() > 0 ? doc['googleReviewCount'].value : 0;

                        // 计算置信度权重
                        double weight;
                        if (count < 10) {
                            weight = 0;
                        } else if (count < 30) {
                            double k = 0.1; // 控制增长速率的参数
                            double numerator = 1 - Math.exp(-k * (count - 10));
                            double denominator = 1 - Math.exp(-k * 20);
                            weight = numerator / denominator;
                        } else {
                            weight = 1;
                        }

                        // 计算可信度评分
                        double credibilityScore;
                        if (count == 0) {
                            credibilityScore = platformAverageRating;
                        } else {
                            credibilityScore = weight * rating + (1 - weight) * platformAverageRating;
                        }

                        // 将评分归一化到 0-1 范围
                        double normalizedCredibilityScore = credibilityScore / 5.0;

                        // 将评分映射到 3.5-5.0 范围
                        double finalScore = 3.5 + (normalizedCredibilityScore * 1.5);

                        // 返回最终评分
                        return finalScore * params.weight;
                    """,
                    "params": {
                        "weight": self.google_review_weight / self.sum_weight,
                    }
                }
            }
        })

        # 添加距离脚本
        if self.params.lat and self.params.lon:
            query["query"]["bool"]["must"].append({
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": """
                            double finalScore = 3.5;
                            if (doc['location.geo_info'].size() > 0 && params.lat != null && params.lon != null) {
                                double distance = doc['location.geo_info'].arcDistance(params.lat, params.lon) / 1609.34; // 距离转换为英里
                                double decayFactor = Math.exp(-0.1 * distance); // 使用指数衰减，k=0.1
                                double normalizedDecayFactor = decayFactor * 2.5; // 归一化到 0-2.5 范围
                                finalScore = 3.5 + (normalizedDecayFactor / 2.5) * 1.5; // 映射到 3.5-5.0 范围
                            }
                            return finalScore * params.weight;
                        """,
                        "params": {
                            "lat": self.params.lat,
                            "lon": self.params.lon,
                            "weight": self.distance_weight / self.sum_weight
                        }
                    }
                }
            })

        if self.params.search:
            # 增加完美匹配
            query["query"]["bool"]["should"].append({
                "bool": {
                    "should": [
                        {
                            "term": {
                                "businessFullName.keyword": {
                                    "value": self.params.search,
                                    "boost": 100
                                }
                            }
                        }
                    ]
                }
            })

        # 添加地理位置过滤条件
        if self.params.lat and self.params.lon and self.params.radius:
            query["query"]["bool"]["filter"].append({
                "bool": {
                    "should": [
                        {
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
                        },
                        {
                            "term": {
                                "locationType": "online"
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            })

        # 添加年龄过滤条件
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

        # 添加营地类型过滤条件
        if self.params.camp_types and "AnyType" not in self.params.camp_types:
            query["query"]["bool"]["filter"].append({
                "bool": {
                    "must": [
                        {"term": {"campSessionOptions": camp_type}} for camp_type in self.params.camp_types
                    ]
                }
            })

        # 添加营地选项过滤条件
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

        # 只筛两种情况：
        # 1. endDate 在今天之后；
        # 2. endDate 为null，durationSeason为Summer 2025
        query["query"]["bool"]["filter"].append({
            "nested": {
                "path": "schedule",
                "query": {
                    "bool": {
                        "should": [
                            {
                                "range": {
                                    "schedule.endDate": {
                                        "gt": "now/d"  # 今天的日期
                                    }
                                }
                            },
                            {
                                "bool": {
                                    "must": [
                                        {
                                            "script": {
                                                "script": {
                                                    "source": "doc['schedule.endDate'].size() == 0",
                                                    "lang": "painless"
                                                }
                                            }
                                        },
                                        {
                                            "term": {
                                                "schedule.durationSeason": {
                                                    "value": "Summer 2025"
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        ],
                        "minimum_should_match": 1
                    }
                }
            }
        })


        # 添加搜索条件
        if self.params.search:
            query["query"]["bool"]["must"].append({
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": self.params.search,
                                "fields": [
                                    "activity",
                                    "activityCategory",
                                    "offeringName",
                                    "businessFullName",
                                    "offeringInsightSummary"
                                ],
                                "type": "most_fields",
                                "fuzziness": "1",
                                "operator": "or",
                                "boost": 0
                            }
                        },
                        {
                            "semantic": {
                                "field": "activityEmbeddings",
                                "query": self.params.search,
                                "boost": 100
                            }
                        }
                    ],
                    # "minimum_should_match": 1  # 至少满足一个条件
                }
            })

        return query

    def request_query(self, query):
        return global_vars.es.search(index=global_vars.config['ELASTICSEARCH_OFFERING'], body=query)

    def postprocess(self, response):
        def offering_postprocess(response):
            hits = response['aggregations']['group_by_businessID']['buckets']
            processed_hits = []

            for bucket in hits:
                top_hit = bucket['top_hits']['hits']['hits'][0]
                source = top_hit['_source']

                # Process location and other fields as needed
                if 'location' in source:
                    source['location'] = parse_location(source['location'])
                if 'locationType' in source and source['locationType'] == 'online':
                    source['locationDisplayName'] = ''

                if 'teyaScore' not in source:
                    source['teyaScore'] = min(top_hit['_score'] / 100 * 5, 5)

                if 'distance' not in source and self.params.lat and self.params.lon:
                    source['distance'] = calculate_distance(self.params.lat, self.params.lon, source['location']['lat'], source['location']['lon'])

                processed_hits.append(source)

            return response

        return offering_postprocess(response)

    def merge_result(self, response):
        hits = response['aggregations']['group_by_businessID']['buckets']
        processed_hits = []
        
        offset = self.params.page_len * self.params.page_offset
        for idx, bucket in enumerate(hits):
            if idx < offset:
                continue
            top_hit = bucket['top_hits']['hits']['hits'][0]
            source = top_hit['_source']
            processed_hits.append(source)
            if len(processed_hits) >= self.params.page_len:
                break

        results = {
            "data": processed_hits,
            "total_hits": len(hits),
        }

        # if processed_hits:
        #     last_bucket = response['aggregations']['group_by_businessID']['buckets'][-1]
        #     results["page_offset"] = {
        #         "prePageLastBusinessID": last_bucket['key']['businessID'],
        #     }

        return results



def business_postprocess(response):
    """
    处理 Elasticsearch 查询结果中的字段转换。
    
    :param response: Elasticsearch 查询结果
    :return: 处理后的查询结果（只返回第一个匹配的 hit）
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

    if len(hits) > 0:  # 如果有匹配的 hit
        hit = hits[0]  # 只处理第一个 hit

        # 处理 interests 字段
        if 'interest' in hit['_source']:
            interests = hit['_source']['interest']
            hit['_source']['interest'] = transform_interests(interests)

        # 处理 contactPhone 字段
        if 'contactPhone' in hit['_source']:
            contact_phone = hit['_source']['contactPhone']
            hit['_source']['contactPhone'] = transform_contact_phone(contact_phone)

        if 'teyaScore' not in hit['_source']:
            hit['_source']['teyaScore'] = hit['_source']['_score']
        
        # 处理 mainOfferingAddress 字段
        if 'mainOfferingAddress' in hit['_source']:
            hit['_source']['mainOfferingAddress'] = parse_location(hit['_source']['mainOfferingAddress'])
        
        if 'additionalOfferingAddress' in hit['_source']:
            for i, _ in enumerate(hit['_source']['additionalOfferingAddress']):
                hit['_source']['additionalOfferingAddress'][i] = parse_location(hit['_source']['additionalOfferingAddress'][i])

        # 只返回第一个 hit
        response['hits']['hits'] = [hit]
        return response

    return response  # 如果没有匹配的 hit，返回原始 response