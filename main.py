# -*- coding: utf-8 -*-
import os
import requests
import akshare as ak
import pandas as pd
from datetime import datetime

# Server酱微信推送配置
SERVER_CHAN_KEY = os.environ.get("SERVER_CHAN_KEY", "")

def send_wechat(title, content):
          """通过Server酱推送到微信"""
          try:
                        url = f"https://sctapi.ftqq.com/{SERVER_CHAN_KEY}.send"
                        data = {"title": title, "desp": content}
                        r = requests.post(url, data=data, timeout=10)
                        if r.status_code == 200:
                                          print("✅ 微信推送成功")
          else:
                            print(f"❌ 微信推送失败: {r.status_code}")
except Exception as e:
        print(f"❌ 推送异常: {e}")

def main():
          today = datetime.now().strftime("%Y-%m-%d")
          print(f"开始选股 {today}")

    try:
                  # 获取上证指数
                  idx_df = ak.stock_zh_index_daily(symbol="sh000001")
                  idx_last = idx_df.iloc[-1]
                  idx_close = idx_last["close"]
                  idx_pct = (idx_last["close"] / idx_df.iloc[-2]["close"] - 1) * 100

        # 获取全部A股实时行情
                  df = ak.stock_zh_a_spot_em()
                  print(f"获取到 {len(df)} 只股票")

        # 筛选主板股票（60开头=沪主板，00开头=深主板）
                  df["代码"] = df["代码"].astype(str)
                  main_df = df[df["代码"].str.startswith(("60", "00"))].copy()

        # 简单筛选条件
                  main_df["涨跌幅"] = pd.to_numeric(main_df["涨跌幅"], errors="coerce")
                  main_df["量比"] = pd.to_numeric(main_df["量比"], errors="coerce")
                  main_df["市盈率-动态"] = pd.to_numeric(main_df["市盈率-动态"], errors="coerce")
                  main_df["总市值"] = pd.to_numeric(main_df["总市值"], errors="coerce")

        # 筛选：涨幅1-5%，量比>1.5，市盈率5-50，市值50亿-500亿
                  selected = main_df[
                      (main_df["涨跌幅"].between(1, 5)) &
                      (main_df["量比"] > 1.5) &
                      (main_df["市盈率-动态"].between(5, 50)) &
                      (main_df["总市值"].between(50e8, 500e8))
          ].copy()

        # 按量比排序，取前20只
                  selected = selected.sort_values("量比", ascending=False).head(20)

        print(f"选出 {len(selected)} 只股票")

        # 生成Markdown报告
        md = f"""## 📊 主板精选日报

        **上证指数**: {idx_close:.0f} ({idx_pct:+.2f}%)  
        **日期**: {today}

        ---

        ### 今日入选 ({len(selected)}只)

        | 代码 | 名称 | 最新价 | 涨跌幅 | 量比 | 市盈率 | 总市值(亿) |
        |------|------|--------|--------|------|--------|------------|
        """
        for _, row in selected.iterrows():
                          md += f"| {row['代码']} | {row['名称']} | {row['最新价']:.2f} | {row['涨跌幅']:+.2f}% | {row['量比']:.2f} | {row['市盈率-动态']:.1f} | {row['总市值']/1e8:.0f} |
                          "

        # 推送到微信
        send_wechat(f"主板精选 {today} 入选{len(selected)}只", md)
        print("完成!")

except Exception as e:
        error_msg = f"选股失败: {str(e)}"
        print(error_msg)
        send_wechat(f"⚠️ 主板精选失败 {today}", error_msg)

if __name__ == "__main__":
          main()
      
