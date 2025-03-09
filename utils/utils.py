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