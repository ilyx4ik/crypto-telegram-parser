import xml.etree.ElementTree as ET
import requests


def get_latest_news():
  url = "https://cointelegraph.com/rss"
  headers = {"User-Agent": "Mozilla/5.0"}

  try:
    response = requests.get(url, headers=headers, timeout=10)
    root = ET.fromstring(response.content)
    items = root.findall(".//item")[:3]

    news_list = []
    for item in items:
      title = item.find("title").text
      link = item.find("link").text
      news_list.append({"title": title, "url": link})

    return news_list

  except Exception as e:
    print(f"Ошибка при получении новостей: {e}")
    return []


if __name__ == "__main__":
  news = get_latest_news()
  for i, item in enumerate(news, 1):
    print(f"{i}. {item['title']}\n   URL: {item['url']}\n")