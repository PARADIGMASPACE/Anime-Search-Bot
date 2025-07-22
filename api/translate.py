import httpx

async def translate_text(text: str, source: str = "en", target: str = "ru") -> str:
    url = "http://libretranslate:5000/translate"
    payload = {
        "q": text,
        "source": source,
        "target": target,
        "format": "text"
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            return resp.json()["translatedText"]
    except Exception as e:
        # Можно логировать ошибку, если нужно
        # print(f"Translation error: {e}")
        return text  # Возвращаем исходный текст при ошибке
