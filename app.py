from flask import Flask, request
import logging
import argparse
import global_vars
from core.request import *

app = Flask(__name__)

@app.route('/GetBusinessID', methods=['GET'])
def get_business_id():
    logger.info(f"{request}")
    request_handler = RequestBusinessID(request.args)
    return request_handler.execute()


@app.route('/GetBusinessFullName', methods=['GET'])
def get_business_full_name():
    logger.info(f"{request}")
    request_handler = RequestBusinessFullName(request.args)
    return request_handler.execute()


@app.route('/GetOfferingsTextQuery', methods=['GET'])
def get_offerings_text_query():
    logger.info(f"{request}")
    request_handler = RequestOfferingSearch(request.args)
    return request_handler.execute()


if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Run the server.')
    parser.add_argument('--config', type=str, default='config.env', help='Path to the configuration file')
    args = parser.parse_args()
    # 初始化全局变量
    global_vars.init_globals(args.config)
    logger = logging.getLogger(__name__)
    # 启动服务
    app.run(debug=True, port=global_vars.config['PORT'], host=global_vars.config['HOST'])