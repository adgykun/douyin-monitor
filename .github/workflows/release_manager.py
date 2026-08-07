import os
import subprocess
import json
from datetime import datetime
from pathlib import Path

REPO = os.getenv('REPO', '')
MAX_FILES_PER_RELEASE = 20

def get_current_release():
    try:
        with open('current_release.txt', 'r') as f:
            data = json.load(f)
            return data.get('tag'), data.get('count', 0)
    except:
        return None, 0

def save_current_release(tag, count):
    with open('current_release.txt', 'w') as f:
        json.dump({'tag': tag, 'count': count}, f)

def create_release(tag):
    title = f"视频备份 {tag}"
    body = f"创建: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    cmd = ['gh', 'release', 'create', tag, '--title', title, '--notes', body]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"创建Release: {tag}")
        return True
    else:
        print(f"创建失败: {result.stderr}")
        return False

def upload_files(tag, files):
    if not files:
        return True
    
    cmd = ['gh', 'release', 'upload', tag] + files + ['--clobber']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"上传 {len(files)} 个文件")
        return True
    else:
        print(f"上传失败: {result.stderr}")
        return False

def main():
    video_dir = Path('videos')
    if not video_dir.exists():
        print("没有视频")
        return
    
    files = [str(f) for f in video_dir.glob('*.mp4')]
    if not files:
        print("没有新视频")
        return
    
    print(f"发现 {len(files)} 个视频")
    
    tag, count = get_current_release()
    
    if tag is None or count >= MAX_FILES_PER_RELEASE:
        tag = f"backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        if not create_release(tag):
            return
        count = 0
    
    slots = MAX_FILES_PER_RELEASE - count
    to_upload = files[:slots]
    
    print(f"Release: {tag} ({count}/{MAX_FILES_PER_RELEASE})")
    print(f"上传: {len(to_upload)} 个")
    
    if upload_files(tag, to_upload):
        save_current_release(tag, count + len(to_upload))
        for f in to_upload:
            os.remove(f)
        
        remaining = files[slots:]
        if remaining:
            save_current_release(None, MAX_FILES_PER_RELEASE)
            main()

if __name__ == '__main__':
    main()
