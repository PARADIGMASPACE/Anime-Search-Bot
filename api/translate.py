import httpx


async def translate_text(text: str, source: str = "en", target: str = "ru") -> str:
    url = "http://libretranslate:5000/translate"
    payload = {"q": text, "source": source, "target": target, "format": "text"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()["translatedText"]
