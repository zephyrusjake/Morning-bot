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

  try:
    ticker_data = yf.download(
        ["^TNX", "KRW=X"], period="2d", progress=False
    )["Close"]
    us10y = ticker_data["^TNX"].iloc[-1]
    krw_usd = ticker_data["KRW=X"].iloc[-1]
    report.append(f"🇺🇸 미국 국채 10년물: {us10y:.2f}%")
    report.append(f"🇰🇷 원/달러 환율: {krw_usd:,.2f}원")
  except Exception:
    report.append(f"❌ 환율/국채 수집 에러")

  try:
    top_tickers = {"Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA"}
    report.append("\n🌍 글로벌 시총 상위:")
    for name, tkr in top_tickers.items():
      stock = yf.Ticker(tkr)
      price = stock.history(period="1d")["Close"].iloc[-1]
      report.append(f"- {name}: ${price:,.2f}")
  except Exception:
    report.append(f"❌ 시총 수집 에러")

  return "\n".join(report)


async def main():
  message = get_financial_data()
  await bot.send_message(chat_id=CHAT_ID, text=message)


if __name__ == "__main__":
  asyncio.run(main())
