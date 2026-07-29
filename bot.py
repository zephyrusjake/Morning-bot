from datetime import datetime
import asyncio
from bs4 import BeautifulSoup
import requests
from telegram import Bot
import yfinance as yf

# 텔레그램 봇 토큰 및 챗 아이디
TOKEN = "8834121678:AAFlOyVnXLiDaHuKEWACZg320ZJQWxzBXw0"
CHAT_ID = "495759757"

bot = Bot(token=TOKEN)


def get_adr():
  """adrinfo.kr에서 코스피 ADR 값을 크롤링하는 함수"""
  try:
    url = "http://adrinfo.kr/"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=5)
    response.encoding = "utf-8"

    if response.status_code == 200:
      soup = BeautifulSoup(response.text, "html.parser")
      text = soup.get_text()
      import re

      match = re.search(r"KOSPI.*?([\d.]+%)", text, re.DOTALL)
      if match:
        return match.group(1)
    return "조회 실패"
  except Exception:
    return "수집 에러"


def get_forward_pe(stock):
  """26년 Forward PE를 안전하게 가져오는 함수 (야후파이낸스 forwardPE 활용)"""
  try:
    info = stock.info
    # 일반적인 forwardPE 속성 확인
    fpe = info.get("forwardPE")
    if fpe:
      return f"{fpe:.2f}"
    return "N/A"
  except Exception:
    return "N/A"


def get_financial_data():
  report = []
  report.append(f"📊 [모닝 금융 브리핑] ({datetime.today().strftime('%Y-%m-%d')})\n")

  # 1. 환율, WTI 유가, 미국 국채 10년물, 코스피 ADR
  try:
    ticker_data = yf.download(
        ["^TNX", "KRW=X", "CL=F"], period="2d", progress=False
    )["Close"]
    us10y = ticker_data["^TNX"].iloc[-1]
    krw_usd = ticker_data["KRW=X"].iloc[-1]
    wti = ticker_data["CL=F"].iloc[-1]

    report.append("📌 **주요 거시 지표 및 ADR**")
    report.append(f"- 원/달러 환율: {krw_usd:,.2f}원")
    report.append(f"- WTI 유가: ${wti:.2f}")
    report.append(f"- 미국 국채 10년물: {us10y:.2f}%")

    kospi_adr = get_adr()
    report.append(f"- 코스피 ADR (adrinfo.kr): {kospi_adr}\n")
  except Exception:
    report.append("❌ 거시 지표 수집 에러\n")
    krw_usd = 1350

  # 2. 글로벌 시총 1, 2, 3위 (Billion 단위 및 26년 Forward PE)
  try:
    global_tickers = {
        "Apple": "AAPL",
        "Microsoft": "MSFT",
        "NVIDIA": "NVDA",
        "Alphabet": "GOOGL",
        "Amazon": "AMZN",
    }
    report.append("🌍 **글로벌 시총 Top 3 & Forward PE**")
    g_list = []
    for name, tkr in global_tickers.items():
      stock = yf.Ticker(tkr)
      mcap = stock.info.get("marketCap", 0)
      g_list.append((name, mcap, stock))

    g_list.sort(key=lambda x: x[1], reverse=True)
    for name, mcap, stock in g_list[:3]:
      mcap_B = mcap / 1_000_000_000
      fpe = get_forward_pe(stock)
      report.append(f"- {name}: ${mcap_B:,.2f}B (Fwd PE: {fpe})")
    report.append("")
  except Exception:
    report.append("❌ 글로벌 시총 수집 에러\n")

  # 3. 한국 시총 1, 2위 (Billion 단위, USD 환산 및 26년 Forward PE)
  try:
    kr_tickers = {
        "Samsung Electronics": "005930.KS",
        "SK Hynix": "000660.KS",
        "LG Energy Solution": "373220.KS",
    }
    report.append("🇰🇷 **국내 시총 Top 2 & Forward PE**")
    kr_list = []
    for name, tkr in kr_tickers.items():
      stock = yf.Ticker(tkr)
      mcap_krw = stock.info.get("marketCap", 0)
      kr_list.append((name, mcap_krw, stock))

    kr_list.sort(key=lambda x: x[1], reverse=True)
    for name, mcap_krw, stock in kr_list[:2]:
      mcap_usd = mcap_krw / krw_usd
      mcap_B = mcap_usd / 1_000_000_000
      fpe = get_forward_pe(stock)
      report.append(f"- {name}: ${mcap_B:,.2f}B (Fwd PE: {fpe})")
    report.append("")
  except Exception:
    report.append("❌ 국내 시총 수집 에러\n")

  # 4. 마이크론(Micron) 시총 Billion 단위 및 Forward PE 추가
  try:
    micron = yf.Ticker("MU")
    micron_mcap = micron.info.get("marketCap", 0)
    micron_B = micron_mcap / 1_000_000_000
    micron_fpe = get_forward_pe(micron)

    report.append("💾 **마이크론 시가총액 & Forward PE**")
    report.append(f"- Micron (MU): ${micron_B:,.2f}B (Fwd PE: {micron_fpe})")
  except Exception:
    report.append("❌ 마이크론 시총 수집 에러")

  return "\n".join(report)


async def main():
  message = get_financial_data()
  await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")


if __name__ == "__main__":
  asyncio.run(main())
