from datetime import datetime
import asyncio
from telegram import Bot
import yfinance as yf

# 본인의 텔레그램 봇 토큰과 챗 아이디 입력
TOKEN = "8834121678:AAFlOyVnXLiDaHuKEWACZg320ZJQWxzBXw0"
CHAT_ID = "495759757"

bot = Bot(token=TOKEN)


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

    report.append("📌 **주요 거시 지표**")
    report.append(f"- 원/달러 환율: {krw_usd:,.2f}원")
    report.append(f"- WTI 유가: ${wti:.2f}")
    report.append(f"- 미국 국채 10년물: {us10y:.2f}%\n")
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

  # 4. 한국 하이닉스 주가, 미국 SKNY 주가 및 비율 계산
  try:
    hynix = yf.Ticker("000660.KS")  # 한국 하이닉스
    skny = yf.Ticker("SKNY")  # 미국 상장 SKNY

    hynix_price = hynix.history(period="1d")["Close"].iloc[-1]
    skny_price = skny.history(period="1d")["Close"].iloc[-1]

    # 비율 계산: (SKNY 주가(달러) 환산액 x 10 / 하이닉스 주가) 비율 퍼센트
    skny_krw = skny_price * krw_usd
    ratio = ((skny_krw * 10) / hynix_price) * 100

    report.append("📈 **개별 종목 및 비율 비교**")
    report.append(f"- SK하이닉스 주가: {hynix_price:,.0f}원")
    report.append(f"- SKNY 주가: ${skny_price:,.2f}")
    report.append(f"- 비율 ((SKNY주가×10) 대비 하이닉스): **{ratio:.2f}%**")
  except Exception:
    report.append("❌ 개별 종목 주가 수집 에러")

  return "\n".join(report)


async def main():
  message = get_financial_data()
  await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")


if __name__ == "__main__":
  asyncio.run(main())
