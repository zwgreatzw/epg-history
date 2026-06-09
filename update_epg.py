import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os

# 只针对你需要保留历史的那个日本源
URL = "https://animenosekai.github.io/japanterebi-xmltv/guide.xml"
FILE_NAME = "guide_history.xml"
DAYS_TO_KEEP = 7 # 保留天数

def fetch_xml():
    req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0 CF-EPG'})
    with urllib.request.urlopen(req) as response:
        return ET.fromstring(response.read())

def parse_time(time_str):
    # XMLTV 时间格式通常是 "20260609140000 +0900"，我们提取前14位数字
    try:
        return datetime.strptime(time_str[:14], "%Y%m%d%H%M%S")
    except:
        return datetime.now()

def main():
    print("正在拉取最新 EPG 数据...")
    current_tree = fetch_xml()

    if os.path.exists(FILE_NAME):
        print("发现历史 EPG 文件，准备合并...")
        history_tree = ET.parse(FILE_NAME).getroot()
    else:
        print("未找到历史文件，将创建新文件...")
        history_tree = ET.Element("tv", current_tree.attrib)

    channels = {}
    programmes = {}

    # 1. 提取历史数据存入字典
    for ch in history_tree.findall('channel'):
        channels[ch.get('id')] = ch
    for prog in history_tree.findall('programme'):
        key = (prog.get('channel'), prog.get('start'), prog.get('stop'))
        programmes[key] = prog

    # 2. 提取最新数据（字典会自动去重并用最新数据覆盖老数据）
    for ch in current_tree.findall('channel'):
        channels[ch.get('id')] = ch
    for prog in current_tree.findall('programme'):
        key = (prog.get('channel'), prog.get('start'), prog.get('stop'))
        programmes[key] = prog

    # 3. 过滤过期数据 (保留最近 7 天)
    cutoff_date = datetime.now() - timedelta(days=DAYS_TO_KEEP)
    
    new_root = ET.Element("tv", current_tree.attrib)
    
    # 重新装载频道
    for ch_id in sorted(channels.keys()):
        new_root.append(channels[ch_id])
        
    # 重新装载节目并过滤时间
    valid_count = 0
    for key in sorted(programmes.keys()):
        prog = programmes[key]
        stop_time_str = prog.get('stop')
        if stop_time_str:
            stop_time = parse_time(stop_time_str)
            if stop_time >= cutoff_date:
                new_root.append(prog)
                valid_count += 1
                
    print(f"合并完成！共保留了 {valid_count} 个节目预告。")
    
    # 4. 保存为 XML 文件
    tree = ET.ElementTree(new_root)
    if hasattr(ET, 'indent'):
        ET.indent(tree, space="\t", level=0)
    tree.write(FILE_NAME, encoding="UTF-8", xml_declaration=True)

if __name__ == "__main__":
    main()
