import httpx
from bs4 import BeautifulSoup


async def obtener_metadata_espn(url: str) -> dict:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

    def og(prop: str) -> str | None:
        tag = soup.find("meta", property=f"og:{prop}")
        return tag["content"] if tag else None

    return {
        "titulo": og("title"),
        "descripcion": og("description"),
        "canal": "ESPN México",
        "thumbnail": og("image"),
    }