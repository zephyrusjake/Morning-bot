from datetime import datetime, timezone, timedelta
import asyncio
from bs4 import BeautifulSoup
import requests
from telegram import Bot

TOKEN = "8834121678:AAFlOyVnXLiDaHuKEWACZg320ZJQWxzBXw0"
CHAT_ID = "495759757"

bot = Bot(token=TOKEN)


def get_semiconductor_news():
  """삼성전자, 하이닉스, 반도체 키워드 최신 기사 5개 스크랩"""
  try:
    # '삼성전자 하이닉스 반도체' 통합 검색 (최신순 정렬: sort=1)
    url = "https://search.naver.com/search.naver?where=news&query=%EC%82%BC%EC%84%B1%EC%A0%84%EC%9E%90+%ED%95%98%EC%9D%B4%EB%8B%89%EC%8A%A4+%EB%B0%98%EB%8F%84%EC%B2%B4&sort=1"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
            " like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=5)

    if response.status_code == 200:
      soup = BeautifulSoup(response.text, "html.parser")
      news_items = soup.select(".news_tit")
      news_list = []

      for item in news_items[:5]:  # 상위 5개 기사 추출
        title = item.get_text()
        link = item.attrs["href"]
        news_list.append(f"• [{title}]({link})")

      if news_list:
        return "\n\n".join(news_list)
    return "관련 뉴스를 찾지 못했습니다."
  except Exception:
    return "뉴스 수집 에러가 발생했습니다."


async def main():
  kst = timezone(timedelta(hours=9))
  current_time = datetime.now(kst).strftime("%Y-%m-%d %H:%M")

  report = [
      f"📰 **[반도체·삼성·하이닉스 주요 뉴스]** ({current_time})\n",
      get_semiconductor_news(),
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

