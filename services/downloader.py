import requests
import re
from urllib.parse import urljoin
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Для асинхронного выполнения синхронного кода
executor = ThreadPoolExecutor(max_workers=2)


def get_video_info(page_url: str):
    """Получает информацию о видео с сайта 1tv.ru"""
    print(f"\n🔍 Получаю информацию: {page_url}")

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })

    try:
        # Загружаем страницу
        response = session.get(page_url)
        response.raise_for_status()
        html = response.text

        # Ищем video_id
        match = re.search(r'video_id=(\d+)', html)
        if not match:
            print("❌ video_id не найден")
            return None

        video_id = match.group(1)
        print(f"✅ video_id: {video_id}")

        # Получаем плейлист
        playlist_url = f"https://www.1tv.ru/playlist?admin=false&single=false&sort=none&video_id={video_id}"
        playlist_response = session.get(playlist_url)
        playlist_response.raise_for_status()

        videos_data = playlist_response.json()
        if not videos_data:
            print("❌ Плейлист пуст")
            return None

        first_video = videos_data[0]
        video_title = first_video.get('title', 'Без названия')
        print(f"🎬 Название: {video_title}")

        # Ищем MP4 в sources
        sources = first_video.get('sources', [])
        video_url = None

        for source in sources:
            if source.get('type') == 'video/mp4':
                video_url = source.get('src')
                print("✅ Найдена MP4 ссылка")
                break

        if not video_url:
            print("❌ MP4 не найден")
            return None

        # Формируем полный URL
        if video_url.startswith('//'):
            video_url = 'https:' + video_url
        elif video_url.startswith('/'):
            video_url = urljoin('https://www.1tv.ru', video_url)

        print(f"📥 URL для скачивания получен")
        return {
            'title': video_title,
            'video_url': video_url
        }

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None


async def download_video_with_progress(video_url: str, save_path: str, progress_callback=None):
    """
    Асинхронно скачивает видео с отображением прогресса
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        executor,
        _download_sync,
        video_url,
        save_path,
        progress_callback,
        loop  # Передаём цикл событий
    )


def _download_sync(video_url: str, save_path: str, progress_callback, loop):
    """Синхронная функция скачивания (выполняется в потоке)"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })

    try:
        print(f"⬇️ Начинаю скачивание: {video_url}")
        response = session.get(video_url, stream=True, timeout=30)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        last_percent = -1

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    # Обновляем прогресс не чаще чем раз в 2% или 10 чанков
                    if progress_callback and total_size > 0:
                        percent = (downloaded / total_size) * 100
                        if int(percent // 2) > int(last_percent // 2):  # Каждые 2%
                            last_percent = percent
                            # Создаем корутину и запускаем в главном цикле
                            asyncio.run_coroutine_threadsafe(
                                progress_callback(downloaded, total_size, percent),
                                loop
                            )

        print(f"✅ Скачивание завершено: {save_path}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False