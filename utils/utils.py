from pyzipcode import ZipCodeDatabase

def transform_interests(interests):
    """将 interests 列表转换为指定的字典格式
    ['Sports: Esports, Basketball', "Arts: Drawing", "Study: "]
    应该被转成如下：
    {
    "Sports": ["Esports", "Basketball"],
    "Arts": ["Drawing"],
    "Study": []
    }
    """
    interests_dict = {}
    for interest in interests:
        if ':' in interest:
            category, items = interest.split(':', 1)
            category = category.strip()
            items = [item.strip() for item in items.split(',') if item.strip()]
            interests_dict[category] = items
        else:
            category = interest.strip()
            interests_dict[category] = []
    return interests_dict

def get_lat_lon_from_zip(zip_code):
    """将美国邮编转换为经纬度"""
    zcdb = ZipCodeDatabase()
    zip_info = zcdb[zip_code]  # 查询邮编信息
    if zip_info:
        return zip_info.latitude, zip_info.longitude  # 返回纬度和经度
    return None, None

def parse_location(location_data):
    """
    解析地点信息，将 geo_info 摊平为 lat 和 lon。
    
    :param location_data: 包含地点信息的字典，通常包括 name, zipcode, geo_info
    :return: 解析后的地点信息字典，包含 name, zipcode, lat, lon
    """
    if not location_data:
        return {
            'name': '',
            'zipcode': '',
            'lat': None,
            'lon': None
        }

    geo_info = location_data.get('geo_info', {})
    if geo_info is None:
        geo_info = {}

    return {
        'name': location_data.get('name', ''),
        'zipcode': location_data.get('zipcode', ''),
        'lat': geo_info.get('lat', ''),
        'lon': geo_info.get('lon', '')
    }