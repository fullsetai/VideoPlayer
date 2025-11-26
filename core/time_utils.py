import re
from datetime import datetime, timedelta
import pytz

class TimeUtils:
    @staticmethod
    def parse_datetime_from_filename(filename):
        """从文件名解析日期时间"""
        # 匹配 cety_2025-11-25 16-51-25_mer 这种格式
        pattern = r'cety_(\d{4}-\d{2}-\d{2})[_\s](\d{2}-\d{2}-\d{2})'
        match = re.search(pattern, filename)
        
        if match:
            date_str = match.group(1)  # 2025-11-25
            time_str = match.group(2).replace('-', ':')  # 16:51:25
            
            try:
                datetime_str = f"{date_str} {time_str}"
                return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
        
        # 如果上面没匹配到，尝试其他格式
        patterns = [
            r'(\d{4}-\d{2}-\d{2}[_\s]\d{2}-\d{2}-\d{2})',
            r'(\d{8}[_\s]\d{6})',
            r'(\d{4}\d{2}\d{2}[_\s]\d{2}\d{2}\d{2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                datetime_str = match.group(1).replace('_', ' ').replace('-', '')
                try:
                    # 尝试不同格式
                    for fmt in ["%Y-%m-%d %H%M%S", "%Y%m%d %H%M%S", "%Y-%m-%d %H-%M-%S"]:
                        try:
                            return datetime.strptime(datetime_str, fmt)
                        except ValueError:
                            continue
                except:
                    continue
        
        return None

    @staticmethod
    def calculate_seconds_difference(time1, time2):
        """计算两个时间字符串的秒数差"""
        def parse_time(time_str):
            hours = int(time_str[:2])
            minutes = int(time_str[2:4])
            seconds = int(time_str[4:6])
            return hours * 3600 + minutes * 60 + seconds
        
        time1_seconds = parse_time(time1)
        time2_seconds = parse_time(time2)
        
        return time2_seconds - time1_seconds

    @staticmethod
    def calculate_absolute_time(base_datetime, video_time_seconds):
        """计算绝对时间（基于视频文件名中的时间）并转换为美东时间"""
        if base_datetime:
            absolute_time = base_datetime + timedelta(seconds=video_time_seconds)
            
            # 转换为美东时间
            eastern = pytz.timezone('US/Eastern')
            eastern_time = absolute_time.astimezone(eastern)
            
            return eastern_time.strftime("%Y-%m-%d %H:%M:%S %Z%z")
        return "时间未解析"