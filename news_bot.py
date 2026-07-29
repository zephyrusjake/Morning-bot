from datetime import datetime, timezone, timedelta
import asyncio
import xml.etree.ElementTree as ET
import urllib.parse
import requests
from telegram import Bot
import yfinance as yf

TOKEN = "8834121678:AAFlOyVnXLiDaHuKEWACZg320ZJQWxzBXw0"
CHAT_ID = "495759757"

bot = Bot(token=TOKEN)


def get_google_news():
  """구글 뉴스 RSS에서 국내 반도체/삼성전자/하이닉스 뉴스 3개 수집"""
  try:
    query = "반도체 삼성전자 하이닉스"
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"

    response = requests.get(url, timeout=5)
    if response.status_code == 200:
      root = ET.fromstring(response.content)
      items = root.findall(".//item")[:3]  # 상위 3개
      news_list = []

      for item in items:
        title = item.find("title").text
        link = item.find("link").text
        news_list.append(f"• [{title}]({link})")

      if news_list:
        return "\n\n".join(news_list)
    return "관련 구글 뉴스를 찾지 못했습니다."
  except Exception as e:
    return f"구글 뉴스 에러: {str(e)}"


def get_yahoo_news():
  """야후 파이낸스에서 'semiconductor' 및 'SK Hynix' 관련 글로벌 뉴스 3개 수집"""
  try:
    yahoo_news_list = []

    # 1. 반도체(Semiconductor) 관련 티커(^SOX 또는 시장 전체 검색 활용) 및 SK하이닉스(000660.KS) 객체 생성
    # 야후는 개별 티커의 .news 속성을 통해 관련 뉴스를 제공합니다.
    sk_hynix = yf.Ticker("000660.KS")
    hynix_news = sk_hynix.news

    # SK하이닉스 뉴스에서 상위 2개 추출
    if hynix_news:
      for item in hynix_news[:2]:
        title = item.get("title")
        link = item.get("link")
        if title and link:
          yahoo_news_list.append(f"• [SK Hynix] {title} ({link})")

    # 2. 글로벌 반도체 섹터 대표로 마이크론(MU)이나 엔비디아(NVDA) 뉴스 활용 (semiconductor 성격)
    micron = yf.Ticker("MU")
    mu_news = micron.news
    if mu_news:
      for item in mu_news[:2]:
        title = item.get("title")
        link = item.get("link")
        if title and link:
          yahoo_news_list.append(f"• [Semiconductor/MU] {title} ({link})")

    if yahoo_news_list:
      return "\n\n".join(yahoo_news_list[:3])  # 총 3개로 제한
    return "관련 야후 뉴스를 찾지 못했습니다."
  except Exception as e:
    return f"야후 뉴스 에러: {str(e)}"


async def main():
  kst = timezone(timedelta(hours=9))
  current_time = datetime.now(kst).strftime("%Y-%m-%d %H:%M")

  report = [
      f"📰 **[글로벌 반도체 뉴스 브리핑]** ({current_time})\n",
      "🇰🇷 **[Google 뉴스 - 국내 주요]**",
      get_google_news(),
      "\n🌍 **[Yahoo Finance - 글로벌/SK Hynix]**",
      get_yahoo_news(),
  ]

  message = "\n".join(report)
  await bot.send_message(
      chat_id=CHAT_ID,
      text=message,
      parse_mode="Markdown",
      disable_web_page_preview=True,
  )


if __name__ == "__main__":
  asyncio.run(main())
