"""
TEK, genel bir fonksiyon - Claude, Gemini, OpenAI, DeepSeek dahil,
OpenAI API formatını destekleyen HERHANGİ bir sağlayıcıya bu fonksiyonla
bağlanıyoruz. Rate-limit (429) ve sunucu (5xx) hatalarında kütüphanenin
kendi otomatik retry mekanizmasını kullanıyoruz.
"""

from openai import OpenAI


def ai_cevap_al(soru: str, api_key: str, base_url: str, model: str,
                sistem_mesaji: str = None) -> str:
    client = OpenAI(api_key=api_key, base_url=base_url, max_retries=5)
    mesajlar = []
    if sistem_mesaji:
        mesajlar.append({"role": "system", "content": sistem_mesaji})
    mesajlar.append({"role": "user", "content": soru})
    yanit = client.chat.completions.create(
        model=model,
        messages=mesajlar,
    )
    return yanit.choices[0].message.content