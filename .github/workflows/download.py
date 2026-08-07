import os
import re
import requests
import json
from datetime import datetime

USER_URL = os.getenv('USER_URL', '')

def get_downloaded():
    """读取已下载列表"""
    try:
        with open('downloaded.txt', 'r') as f:
            return set(f.read().strip().split('\n'))
    except:
        return set()

def save_downloaded(video_id):
    """保存下载记录"""
    with open('downloaded.txt', 'a') as f:
        f.write(f"{video_id}\n")

def clean_filename(text):
    """清理文件名非法字符"""
    return re.sub(r'[\\/:*?"<>|]', '', text)[:50]

def download_video_simple(video_id, video_url, title):
    """简单下载方法"""
    os.makedirs('videos', exist_ok=True)
    
    clean_title = clean_filename(title) or video_id
    filename = f"videos/{video_id}_{clean_title}.mp4"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
        'Referer': 'https://www.douyin.com/'
    }
    
    print(f"正在下载: {title}")
    
    try:
        response = requests.get(video_url, headers=headers, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
        
        print(f"✓ 下载完成: {filename}")
        save_downloaded(video_id)
        return True
        
    except Exception as e:
        print(f"✗ 下载失败: {e}")
        return False

def get_videos_from_share_url():
    """从分享链接获取视频信息"""
    
    # 第一步：解析短链接
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
    }
    
    try:
        # 跟随重定向获取真实URL
        resp = requests.get(USER_URL, headers=headers, allow_redirects=True, timeout=10)
        real_url = resp.url
        
        # 从URL中提取用户ID
        match = re.search(r'user/([^/?]+)', real_url)
        if not match:
            print("无法解析用户ID")
            return []
        
        sec_uid = match.group(1)
        print(f"用户ID: {sec_uid}")
        
        # 调用抖音API（简化版，可能需要Cookie）
        api_url = f"https://www.douyin.com/aweme/v1/web/aweme/post/"
        params = {
            'sec_user_id': sec_uid,
            'count': 10,
            'max_cursor': 0
        }
        
        api_resp = requests.get(api_url, params=params, headers=headers, timeout=10)
        data = api_resp.json()
        
        videos = []
        for item in data.get('aweme_list', [])[:3]:  # 只取最新3个
            video_info = {
                'id': item['aweme_id'],
                'title': item['desc'] or '无标题',
                'url': item['video']['play_addr']['url_list'][0]
            }
            videos.append(video_info)
        
        return videos
        
    except Exception as e:
        print(f"获取视频列表失败: {e}")
        return []

def main():
    if not USER_URL:
        print("错误: 未设置 USER_URL")
        return
    
    print(f"开始监控: {USER_URL}")
    
    downloaded = get_downloaded()
    videos = get_videos_from_share_url()
    
    if not videos:
        print("未获取到视频，可能需要配置Cookie")
        return
    
    new_count = 0
    for video in videos:
        if video['id'] not in downloaded:
            if download_video_simple(video['id'], video['url'], video['title']):
                new_count += 1
    
    print(f"\n本次下载 {new_count} 个新视频")

if __name__ == '__main__':
    main()
