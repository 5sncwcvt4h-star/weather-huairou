import requests
import json
import re
import csv
import os
from datetime import datetime

CITY_ID = "101010500"
URL = f"https://www.weather.com.cn/weather1d/{CITY_ID}.shtml"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.weather.com.cn/",
}

def get_hourly_data():
    """从页面script中提取小时数据"""
    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        response.encoding = "utf-8"
        html = response.text
        print(f"✓ 成功访问: {URL}")
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return None

    pattern = r'var\s+[a-zA-Z0-9_]+\s*=\s*(\{"od":.*?\});'
    matches = re.findall(pattern, html, re.DOTALL)
    
    if matches:
        json_str = matches[-1]
        try:
            data = json.loads(json_str)
            return data
        except json.JSONDecodeError as e:
            print(f"✗ JSON解析失败: {e}")
            return None
    
    print("✗ 未在页面中找到天气数据JSON")
    return None

def parse_hourly_data(json_data, data_type="all"):
    """解析JSON，提取小时级别数据"""
    if not json_data or "od" not in json_data:
        return []
    
    od_data = json_data["od"]
    data_time_str = od_data.get("od0", "")
    if len(data_time_str) >= 8:
        data_date = data_time_str[:8]
    else:
        data_date = datetime.now().strftime("%Y%m%d")
    
    location = od_data.get("od1", "怀柔")
    hour_list = od_data.get("od2", [])
    
    if not hour_list:
        print("✗ 未找到小时数据")
        return []
    
    all_records = []
    for hour_data in hour_list:
        hour_value = hour_data.get("od21", "")
        if hour_value:
            hour_str = f"{int(hour_value):02d}:00"
        else:
            hour_str = "00:00"
        
        record = {
            "地点": location,
            "日期": data_date,
            "小时": hour_str,
            "温度(℃)": hour_data.get("od22", ""),
            "风向": hour_data.get("od24", ""),
            "风力(级)": hour_data.get("od25", ""),
            "降水量(mm)": hour_data.get("od26", ""),
            "相对湿度(%)": hour_data.get("od27", ""),
            "空气质量指数": hour_data.get("od28", ""),
        }
        all_records.append(record)
    
    # 按时间正序排序
    sorted_records = sorted(all_records, key=lambda x: x["小时"])
    
    # 去重
    unique_records = []
    seen_hours = set()
    for record in sorted_records:
        if record["小时"] not in seen_hours:
            seen_hours.add(record["小时"])
            unique_records.append(record)
    
    current_hour = datetime.now().hour
    if data_type == "past":
        result = [r for r in unique_records if int(r["小时"][:2]) < current_hour]
    elif data_type == "future":
        result = [r for r in unique_records if int(r["小时"][:2]) >= current_hour]
    else:
        result = unique_records
    
    return result

def save_to_csv(data, filename=None):
    """保存数据到CSV"""
    if not data:
        print("✗ 无数据可保存")
        return False
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"weather_huairou_{timestamp}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    print(f"✓ 数据已保存到: {filename}")
    return True

def main():
    """自动运行模式：按日期命名文件"""
    print("=" * 60)
    print("北京市怀柔区 - 自动获取24小时天气数据")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    json_data = get_hourly_data()
    if not json_data:
        return False
    
    hourly_data = parse_hourly_data(json_data, data_type="all")
    
    if hourly_data:
        today = datetime.now().strftime("%Y%m%d")
        filename = f"data/weather_huairou_{today}.csv"
        
        # 创建 data 目录（如果不存在）
        import os
        os.makedirs("data", exist_ok=True)
        
        success = save_to_csv(hourly_data, filename)
        if success:
            print(f"\n✓ 今日数据已保存: {filename}")
            print(f"  共 {len(hourly_data)} 条记录")
        return success
    else:
        print("✗ 获取数据失败")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)