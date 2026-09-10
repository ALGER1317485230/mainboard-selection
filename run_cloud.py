# -*- coding: utf-8 -*-
"""
云端入口脚本：刷新数据 → 选股 → 发邮件
用于GitHub Actions每天定时运行
"""
import os, sys, json, time, subprocess
from datetime import datetime

# 设置路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
V1_DIR = os.path.join(BASE_DIR, "v1")
V7_DIR = os.path.join(BASE_DIR, "v7")
CACHE_DIR = os.path.join(V7_DIR, "cache")
OUT_ROOT = os.path.join(BASE_DIR, "output")

sys.path.insert(0, V1_DIR)
sys.path.insert(0, V7_DIR)

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(OUT_ROOT, exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def run_cmd(cmd, name, timeout=1800):
    log(f"=== 启动 {name} ===")
    p = subprocess.run(cmd, cwd=V7_DIR, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if p.stdout:
        print(p.stdout[-2000:])
    if p.returncode != 0:
        log(f"[ERROR] {name} 失败(rc={p.returncode})")
        if p.stderr:
            print(p.stderr[-2000:])
        return False
    log(f"[OK] {name} 完成")
    return True

def main():
    log("=" * 50)
    log("云端选股任务开始")
    
    # 1. 刷新数据
    log("步骤1: 刷新行情数据")
    ok = run_cmd([sys.executable, "refresh_and_select.py"], "数据刷新", timeout=1800)
    if not ok:
        log("数据刷新失败，发送警告邮件")
        send_warning_email("数据刷新失败")
        return False
    
    # 2. 选股 + 发邮件
    log("步骤2: 选股并发送邮件")
    ok = run_cmd([sys.executable, "cloud_daily_report.py"], "选股+邮件", timeout=300)
    if not ok:
        log("选股或邮件发送失败")
        return False
    
    log("云端选股任务完成")
    log("=" * 50)
    return True

def send_warning_email(reason):
    """发送警告邮件"""
    import smtplib
    from email.mime.text import MIMEText
    from email.utils import formataddr
    
    sender = os.environ.get("EMAIL_SENDER", "")
    password = os.environ.get("EMAIL_PASSWORD", "")
    receiver = os.environ.get("EMAIL_RECEIVER", sender)
    
    if not sender or not password:
        log("邮箱配置缺失，无法发送警告邮件")
        return
    
    msg = MIMEText(f"⚠️ 主板精选选股日报警告\n\n原因：{reason}\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n请检查数据刷新日志。", "plain", "utf-8")
    msg["From"] = formataddr(["主板精选", sender])
    msg["To"] = formataddr(["", receiver])
    msg["Subject"] = "【主板精选】⚠️ 数据刷新失败"
    
    try:
        server = smtplib.SMTP_SSL("smtp.qq.com", 465, timeout=30)
        server.login(sender, password)
        server.sendmail(sender, [receiver], msg.as_string())
        server.quit()
        log("警告邮件已发送")
    except Exception as e:
        log(f"警告邮件发送失败: {e}")

if __name__ == "__main__":
    main()
