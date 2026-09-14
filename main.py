# -*- coding: utf-8 -*-
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import akshare as ak
import pandas as pd
from datetime import datetime

# 邮件配置（从环境变量读取）
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
SENDER = os.environ.get("MAIL_SENDER", "1317485230@qq.com")
AUTH_CODE = os.environ.get("MAIL_AUTH_CODE", "")
RECEIVER = os.environ.get("MAIL_RECEIVER", "1317485230@qq.com")

def send_email(html_content, subject):
      msg = MIMEText(html_content, "html", "utf-8")
      msg["From"] = SENDER
      msg["To"] = RECEIVER
      msg["Subject"] = Header(subject, "utf-8")
      server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
      server.login(SENDER, AUTH_CODE)
      server.sendmail(SENDER, RECEIVER, msg.as_string())
      server.quit()
      print("邮件发送成功")

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

        # 生成HTML报告
        html = f"""
                <html><head><meta charset="utf-8">
                        <style>
                                    body {{ background: #1a1a2e; color: #eee; font-family: Arial; padding: 20px; }}
                                                .header {{ text-align: center; margin-bottom: 20px; }}
                                                            .index {{ font-size: 24px; color: #e94560; }}
                                                                        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                                                                                    th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #333; }}
                                                                                                th {{ background: #16213e; color: #e94560; }}
                                                                                                            .up {{ color: #e94560; }}
                                                                                                                    </style></head><body>
                                                                                                                            <div class="header">
                                                                                                                                        <h1>📊 主板精选日报</h1>
                                                                                                                                                    <div class="index">上证指数: {idx_close:.0f} ({idx_pct:+.2f}%)</div>
                                                                                                                                                                <div>日期: {today}</div>
                                                                                                                                                                        </div>
                                                                                                                                                                                <h2>今日入选 ({len(selected)}只)</h2>
                                                                                                                                                                                        <table>
                                                                                                                                                                                                    <tr><th>代码</th><th>名称</th><th>最新价</th><th>涨跌幅</th><th>量比</th><th>市盈率</th><th>总市值(亿)</th></tr>
                                                                                                                                                                                                            """
        for _, row in selected.iterrows():
                      pct_class = "up" if row["涨跌幅"] > 0 else ""
                      html += f"""
                      <tr>
                          <td>{row['代码']}</td>
                          <td>{row['名称']}</td>
                          <td>{row['最新价']:.2f}</td>
                          <td class="{pct_class}">{row['涨跌幅']:+.2f}%</td>
                          <td>{row['量比']:.2f}</td>
                          <td>{row['市盈率-动态']:.1f}</td>
                          <td>{row['总市值']/1e8:.0f}</td>
                      </tr>
                      """
                  html += "</table></body></html>"

                  # 发邮件
                  send_email(html, f"【主板精选】{today} 今日入选{len(selected)}只")
                  print("完成!")

              except Exception as e:
                  error_msg = f"选股失败: {str(e)}"
                  print(error_msg)
                  send_email(f"<h2>⚠️ 选股失败</h2><p>{error_msg}</p>", f"【主板精选】{today} 失败警告")

          if __name__ == "__main__":
              main()
          
