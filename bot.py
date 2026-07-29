from datetime import datetime, timezone, timedelta
import asyncio
from bs4 import BeautifulSoup
import requests
from telegram import Bot
import yfinance as yf

# 텔레그램 봇 토큰 및 챗 아이디
TOKEN = "8834121678:AAFlOyVnXLiDaHuKEWACZg320ZJQWxzBXw0"
CHAT_ID = "495759757"

bot = Bot(token=TOKEN)


def get_adr_sentiment(adr_str):
  """ADR 수치에 따른 시장 판단 기준 반환"""
  try:
    import re

    val = float(re.sub(r"[^\d.]", "", adr_str))

    if val >= 120:
      return f"{adr_str} (과열권)"
    elif val > 100:
      return f"{adr_str} (상승 우위)"
    elif val == 100:
      return f"{adr_str} (균형)"
    elif val > 75:
      return f"{adr_str} (조정/약세 우위)"
    else:
      return f"{adr_str} (바닥권)"
  except Exception:
    return adr_str


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
        raw_adr = match.group(1)
        return get_adr_sentiment(raw_adr)
    return "조회 실패"
  except Exception:
    return "수집 에러"


def get_forward_pe(stock):
  """26년 Forward PE를 안전하게 가져오는 함수"""
  try:
    info = stock.info
    fpe = info.get("forwardPE")
    if fpe:
      return f"{fpe:.2f}"
    return "N/A"
  except Exception:
    return "N/A"


def calc_change(series):
  """전일 대비 등락률(%) 계산 함수 (삼각형 제거)"""
  try:
    prev = series.iloc[-2]
    curr = series.iloc[-1]
    rate = ((curr - prev) / prev) * 100
    if rate > 0:
      return f"+{rate:.2f}%"
    elif rate < 0:
      return f"{rate:.2f}%"
    else:
      return f"0.00%"
  except Exception:
    return "N/A"


def get_vix_sentiment(vix_val):
  """VIX 수치에 따른 시장 심리 상태 반환"""
  if vix_val < 15:
    return "탐욕/안정"
  elif vix_val < 20:
    return "보통"
  elif vix_val < 30:
    return "공포/주의"
  else:
    return "극단적 공포"


def get_financial_data():
  report = []

  # 한국 시간(KST, UTC+9) 계산
  kst = timezone(timedelta(hours=9))
  current_time = datetime.now(kst).strftime("%Y-%m-%d %H:%M")

  report.append(f"📊 [금융 브리핑] ({current_time})\n")

  # 1. 거시 지표 및 변동성 지수
  try:
    tickers = ["^TNX", "KRW=X", "CL=F", "^VIX", "^SOX", "MU"]
    ticker_data = yf.download(tickers, period="2d", progress=False)["Close"]

    us10y = ticker_data["^TNX"].iloc[-1]

    krw_usd = ticker_data["KRW=X"].iloc[-1]
    krw_chg = calc_change(ticker_data["KRW=X"])

    wti = ticker_data["CL=F"].iloc[-1]
    wti_chg = calc_change(ticker_data["CL=F"])

    vix = ticker_data["^VIX"].iloc[-1]
    vix_sentiment = get_vix_sentiment(vix)

    sox = ticker_data["^SOX"].iloc[-1]
    sox_chg = calc_change(ticker_data["^SOX"])

    mu_price = ticker_data["MU"].iloc[-1]
    mu_chg = calc_change(ticker_data["MU"])

    report.append("📌 **주요 거시 지표 및 변동성**")
    report.append(f"- 원/달러 환율: {krw_usd:,.2f}원 ({krw_chg})")
    report.append(f"- WTI 유가: ${wti:.2f} ({wti_chg})")
    report.append(f"- 미국 국채 10년물: {us10y:.2f}%")
    report.append(f"- 공포지수(VIX): {vix:.2f} ({vix_sentiment})")

    kospi_adr = get_adr()
    report.append(f"- 코스피 ADR: {kospi_adr}\n")
  except Exception:
    report.append("❌ 거시 지표 수집 에러\n")
    krw_usd = 1350
    mu_price = 0
    mu_chg = "0.00%"
    sox = 0
    sox_chg = "0.00%"

  # 2. 글로벌 시총 1, 2, 3위 (Billion 단위 및 Forward PE)
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

  # 3. 한국 시총 1, 2위 (Billion 단위, USD 환산 및 Forward PE)
  try:
    kr_tickers = {
        "삼성전자": "005930.KS",
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

  # 4. 마이크론 시가총액, 주가 및 필라델피아 반도체 지수
  try:
    micron = yf.Ticker("MU")
    micron_mcap = micron.info.get("marketCap", 0)
    micron_B = micron_mcap / 1_000_000_000
    micron_fpe = get_forward_pe(micron)

    report.append("💾 **마이크론 시가총액 & Forward PE**")
    report.append(f"- Micron (MU): ${micron_B:,.2f}B (Fwd PE: {micron_fpe})")
    report.append(f"- 마이크론 주가: ${mu_price:,.2f} ({mu_chg})")
    report.append(f"- 필라델피아 반도체: {sox:,.2f} ({sox_chg})")
  except Exception:
    report.append("❌ 마이크론 시총 수집 에러")

  return "\n".join(report)


async def main():
  message = get_financial_data()
  await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")


if __name__ == "__main__":
  asyncio.run(main())
