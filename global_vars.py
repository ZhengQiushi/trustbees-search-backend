import datetime
import os
import json
import logging
from elasticsearch import Elasticsearch
from dotenv import dotenv_values

# 全局变量
config = None
producer = None
eslogger = None
es = None

# 自定义 Elasticsearch 处理程序
class ElasticsearchHandler(logging.Handler):
    def __init__(self, index):
        super().__init__()
        self.index = index

    def emit(self, record):
        try:
            log_data = {
                "@timestamp": datetime.datetime.utcfromtimestamp(record.created).isoformat() + "Z",
                "log_level": record.levelname,  # 日志级别
                "message": record.getMessage(),  # 日志消息
                "logger_name": record.name,  # 日志器名称
                "module": record.module,  # 模块名称
                "file": f"{record.filename}:{record.lineno}"
            }
            eslogger.index(index=self.index, body=log_data)
        except Exception as e:
            raise(e)
            
def init_globals(config_file):
    """
    初始化全局变量：加载配置、设置日志、创建 Kafka Producer 实例
    """
    global eslogger, config, es
    
    config = dotenv_values(config_file)

    es_config = {
        "hosts": [config.get("ES_HOST")],
        "api_key": config.get("ES_API_KEY"),
        # 其他可选配置
        "timeout": 30,
        "max_retries": 3,
        "retry_on_timeout": True
    }

    try:
        eslogger = Elasticsearch(**es_config)
        # 测试连接
        if not eslogger.ping():
            raise ValueError("无法连接到 Elasticsearch")
        print("成功连接到 Elasticsearch")
    except Exception as e:
        print(f"Elasticsearch 连接错误: {e}")
    except ValueError as e:
        print(e)
    
    # 为 ES 客户端创建独立的 Logger
    es_logger = logging.getLogger("elasticsearch")
    es_logger.propagate = False  # 禁止传播到根 Logger

    # 创建 Elasticsearch 日志处理器
    es_handler = ElasticsearchHandler(config.get("ES_LOGGER_INDEX_NAME"))
    
    # 配置日志输出
    log_dir = config.get("ES_LOGGER_LEVEL")
    log_file = config.get("ES_LOGGER_PATH")

    logging.basicConfig(
        level=config.get("ES_LOGGER_LEVEL"),
        format='%(asctime)s [%(name)s] [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
            es_handler  # 添加 Elasticsearch 处理器
        ]
    )

    logging.getLogger("requests").setLevel(config.get("OTHERS_LOGGER_LEVEL"))
    logging.getLogger("scrapy").setLevel(config.get("OTHERS_LOGGER_LEVEL"))
    logging.getLogger("urllib3").setLevel(config.get("OTHERS_LOGGER_LEVEL"))

    # 关闭 elastic_transport 的日志
    logging.getLogger('elastic_transport').setLevel(config.get("OTHERS_LOGGER_LEVEL"))

    # 如果你使用的是旧版本的 elasticsearch 客户端（<8.0），可能需要关闭 elasticsearch 的日志
    logging.getLogger('elasticsearch').setLevel(config.get("OTHERS_LOGGER_LEVEL"))

    # 连接到 Elasticsearch
    es_config = {
        "hosts": [config.get("ES_HOST")],
        "api_key": config.get("ES_API_KEY"),
        # 其他可选配置
        "max_retries": 3,
        "retry_on_timeout": True
    }

    try:
        es = Elasticsearch(**es_config)
        # 测试连接
        if not es.ping():
            raise ValueError("无法连接到 Elasticsearch")
        print("成功连接到 Elasticsearch")
    except Exception as e:
        print(f"Elasticsearch 连接错误: {e}")
    except ValueError as e:
        print(e)