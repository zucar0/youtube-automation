# test_news.py (temporal, no lo subas al repo)
import asyncio
from app.services.news_search import buscar_notas_similares

async def main():
    resultado = await buscar_notas_similares("america", "América Femeil es campeón de campeonaas derrotando a Tigres en penales")
    print(f"Noticias encontradas: {len(resultado)}")
    for n in resultado:
        print(f"- {n['titulo']} ({n['fuente']})")

asyncio.run(main())