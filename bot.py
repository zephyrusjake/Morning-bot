from datetime import datetime
import asyncio
from bs4 import BeautifulSoup
import requests
from telegram import Bot
import yfinance as yf

# 본인의 텔레그램 봇 토큰과 챗 아이디 입력
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
      # adrinfo.kr의 구조에 맞춰 코스피 ADR 값 추출 (텍스트 매칭 또는 첫 번째 퍼센트 값 활용)
      # 사이트 구조 변경에 대비해 안전하게 텍스트 검색 수행
      text = soup.get_text()
      # 'KOSPI' 글자 근처의 퍼센트 값을 찾는 로직 등 적용 가능
      # 기본 메인 페이지의 KOSPI ADR 표출부 파싱
      # 예시로 최신 구조의 요약 텍스트에서 KOSPI 항목 뒤의 수치 추출
      import re

      # KOSPI 뒤에 나오는 첫 번째 숫자+% 패턴 찾기
      match = re.search(r"KOSPI.*?([\d.]+%)", text, re.DOTALL)
      if match:
        return match.group(1)
    return "조회 실패"
  except Exception:
    return "수집 에러"


def get_financial_data():
  report = []
  report.append(f"📊 [모닝 금융 브리핑] ({datetime.today().strftime('%Y-%m-%d')})\n")

  # 1. 환율, WTI 유가, 미국 국채 10년물
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

    # 코스피 ADR 추가
    kospi_adr = get_adr()
    report.append(f"- 코스피 ADR (adrinfo.kr): {kospi_adr}\n")
  except Exception:
    report.append("❌ 거시 지표 수집 에러\n")
    krw_usd = 1350

  # 2. 글로벌 시총 1, 2, 3위 (Billion 단위)
  try:
    global_tickers = {
        "Apple": "AAPL",
        "Microsoft": "MSFT",
        "NVIDIA": "NVDA",
        "Alphabet": "GOOGL",
        "Amazon": "AMZN",
    }
    report.append("🌍 **글로벌 시총 Top 3**")
    g_list = []
    for name, tkr in global_tickers.items():
      stock = yf.Ticker(tkr)
      mcap = stock.info.get("marketCap", 0)
      g_list.append((name, mcap))

    g_list.sort(key=lambda x: x[1], reverse=True)
    for name, mcap in g_list[:3]:
      mcap_B = mcap / 1_000_000_000
      report.append(f"- {name}: ${mcap_B:,.2f}B")
    report.append("")
  except Exception:
    report.append("❌ 글로벌 시총 수집 에러\n")

  # 3. 한국 시총 1, 2위 (Billion 단위 - USD 환산)
  try:
    kr_tickers = {
        "Samsung Electronics": "005930.KS",
        "SK Hynix": "000660.KS",
        "LG Energy Solution": "373220.KS",
    }
    report.append("🇰🇷 **국내 시총 Top 2 (USD 환산)**")
    kr_list = []
    for name, tkr in kr_tickers.items():
      stock = yf.Ticker(tkr)
      mcap_krw = stock.info.get("marketCap", 0)
      kr_list.append((name, mcap_krw))

    kr_list.sort(key=lambda x: x[1], reverse=True)
    for name, mcap_krw in kr_list[:2]:
      mcap_usd = mcap_krw / krw_usd
      mcap_B = mcap_usd / 1_000_000_000
      report.append(f"- {name}: ${mcap_B:,.2f}B")
    report.append("")
  except Exception:
    report.append("❌ 국내 시총 수집 에러\n")

  # 4. 하이닉스(A), SKNY(B) 주가 및 C값, 비율 계산
  try:
    hynix = yf.Ticker("000660.KS")  # A: 코스피 하이닉스 주가 (원)
    skny = yf.Ticker("SKNY")  # B: 나스닥 SKNY 주가 (달러)

    A = hynix.history(period="1d")["Close"].iloc[-1]
    B = skny.history(period="1d")["Close"].iloc[-1]

    # C = A / 원달러환율 / 10
    C = (A / krw_usd) / 10

    # C / B 비율 계산 (퍼센트 형태로 표현하기 위해 x100 또는 순수 배율 확인 - 요청하신 C/B 값 계산)
    # 만약 퍼센트로 보고 싶다면 (C / B) * 100 형태로 응용 가능하며, 여기서는 C/B 비율 값 자체를 명시합니다.
    c_b_ratio = (C / B) * 100 if B != 0 else 0

    report.append("📈 **하이닉스 & SKNY 비교 분석**")
    report.append(f"- 코스피 하이닉스 주가 (A): {A:,.0f}원")
    report.append(f"- 나스닥 SKNY 주가 (B): ${B:,.2f}")
    report.append(f"- 계산된 C값 (A / 환율 / 10): ${C:,.2f}")
    report.append(f"- C / B 비율: **{c_b_ratio:.2f}%**")
  except Exception:
    report.append("❌ 개별 종목 주가 수집 에러")

  return "\n".join(report)


async def main():
  message = get_financial_data()
  await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")


if __name__ == "__main__":
  asyncio.run(main())
