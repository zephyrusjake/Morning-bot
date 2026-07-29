from datetime import datetime, timezone, timedelta
import asyncio
import xml.etree.ElementTree as ET
import urllib.parse
from deep_translator import GoogleTranslator
import requests
from telegram import Bot

TOKEN = "8834121678:AAFlOyVnXLiDaHuKEWACZg320ZJQWxzBXw0"
CHAT_ID = "495759757"

bot = Bot(token=TOKEN)


def translate_text(text):
  """영문 텍스트를 한국어로 번역하는 함수"""
  try:
    return GoogleTranslator(source="en", target="ko").translate(text)
  except Exception:
    return text  # 번역 실패 시 원문 반환


def get_google_news(query, lang_kr=True):
  """구글 뉴스 RSS를 이용해 키워드 뉴스 수집 및 영문은 한글 번역"""
  try:
    encoded_query = urllib.parse.quote(query)
    hl = "ko" if lang_kr else "en"
    gl = "KR" if lang_kr else "US"

    url = (
        f"https://news.google.com/rss/search?q={encoded_query}&hl={hl}&gl={gl}&ceid={gl}:{hl}"
    )
    response = requests.get(url, timeout=5)

    if response.status_code == 200:
      root = ET.fromstring(response.content)
      items = root.findall(".//item")[:3]  # 상위 3개 기사 추출
      news_list = []

      for item in items:
        title = item.find("title").text
        link = item.find("link").text

        # 영문 뉴스인 경우 제목을 한국어로 번역
        if not lang_kr:
          title = translate_text(title)

        news_list.append(f"• [{title}]({link})")

      if news_list:
        return "\n\n".join(news_list)
    return "관련 뉴스를 찾지 못했습니다."
  except Exception as e:
    return f"뉴스 수집 에러: {str(e)}"


async def main():
  kst = timezone(timedelta(hours=9))
  current_time = datetime.now(kst).strftime("%Y-%m-%d %H:%M")

  # 1. 국내 뉴스 (한국어)
  kr_news = get_google_news("반도체 삼성전자 하이닉스", lang_kr=True)
  # 2. 글로벌 영문 뉴스 (가져오면서 한국어로 자동 번역)
  global_news = get_google_news("semiconductor sk hynix", lang_kr=False)

  report = [
      f"📰 **[반도체 뉴스 브리핑]** ({current_time})\n",
      "🇰🇷 **[국내 주요 뉴스]**",
      kr_news,
      "\n🌍 **[글로벌 뉴스 (번역)]**",
      global_news,
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
