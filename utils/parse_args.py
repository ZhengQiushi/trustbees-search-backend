import re
from utils.utils import *
import sys, os
# 将项目根目录添加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

class BaseSearchParams:
    def __init__(self, request_args):
        # 提取 page_offset 和 page_len，并确保它们是数字
        self.page_offset = {
            "prePageLastScore": self._ensure_number(request_args.get("prePageLastScore", 0), "prePageLastScore"),
            "prePageLastBusinessID": request_args.get("prePageLastBusinessID", None)
         }

        # self.page_offset = self._ensure_number(request_args.get("pageOffset", 0), "pageOffset")

        self.page_len = self._ensure_number(request_args.get("pageLen", 15), "pageLen")

    @staticmethod
    def _ensure_number(value, param_name):
        """确保值是数字，否则抛出异常"""
        try:
            # 尝试将值转换为整数或浮点数
            return int(value) if str(value).isdigit() else float(value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid {param_name}: '{value}', expected a number.")

    @staticmethod
    def _is_number(value):
        """检查值是否为数字"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False


class SearchBusinessIDParams(BaseSearchParams):
    def __init__(self, request_args):
        super().__init__(request_args)
        self.business_id = request_args.get("businessID")

        # 校验 business_id 是必填项
        if not self.business_id:
            raise ValueError("Invalid parameters: businessID is required.")


class SearchBusinessNameParams(BaseSearchParams):
    def __init__(self, request_args):
        super().__init__(request_args)
        self.business_name = request_args.get("businessFullName")

        # 校验 business_name 是必填项
        if not self.business_name:
            raise ValueError("Invalid parameters: businessFullName is required.")


class SearchOfferingParams(BaseSearchParams):
    VALID_CAMP_TYPES = {"AnyType", "FullDayCamp", "HalfDayCamp", "SleepawayCamp"}
    VALID_CAMP_OPTIONS = {"Indoor", "Outdoor", "Lunch", "EarlyDropoff", "Transportation", "LatePickup"}

    def __init__(self, request_args):
        super().__init__(request_args)
        self.search = request_args.get("search")
        self.zip_code = request_args.get("zipCode")
        self.radius = request_args.get("radius")
        self.ages = request_args.getlist("age")
        self.camp_types = request_args.getlist("campType")
        self.camp_options = request_args.getlist("campOptions")
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

        # 4. age（如果有）必须是数字
        for age in self.ages:
            if age is not None and not self._is_number(age):
                raise ValueError(f"Invalid age: '{age}', expected an integer.")

        # 5. camp_types 只能包含指定值
        for camp_type in self.camp_types:
            if camp_type not in self.VALID_CAMP_TYPES:
                raise ValueError(f"Invalid camp_type: '{camp_type}', expected one of {self.VALID_CAMP_TYPES}.")

        # 6. camp_options 只能包含指定值
        for camp_option in self.camp_options:
            if camp_option not in self.VALID_CAMP_OPTIONS:
                raise ValueError(f"Invalid camp_option: '{camp_option}', expected one of {self.VALID_CAMP_OPTIONS}.")

        # 将邮编转换为经纬度
        try:
            self.lat, self.lon = get_lat_lon_from_zip(self.zip_code)
        except Exception as e:
            raise ValueError(f"Invalid zipcode: '{self.zip_code}', failed to parse to lat and lon. {str(e)}")
        
        if not self.lat or not self.lon:
            raise ValueError(f"Invalid zipcode: '{self.zip_code}', failed to parse to lat and lon.")