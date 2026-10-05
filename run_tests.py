import os
import json
from datetime import datetime
from dotenv import load_dotenv
from functools import partial
from llm_client import ai_cevap_al
from test_cases import TEST_CASES
from scoring import anlam_benzerligi_skoru, llm_judge_skoru

load_dotenv()

SAGLAYICILAR = {
    "claude": {"base_url": "https://api.anthropic.com/v1/", "model": "claude-sonnet-4-6"},
    "gemini": {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai/", "model": "gemini-3.5-flash-lite"},
    "gemini_lite": {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai/", "model": "gemini-3.5-flash-lite"},
    "openai": {"base_url": "https://api.openai.com/v1", "model": "gpt-4o"},
    "deepseek": {"base_url": "https://api.deepseek.com", "model": "deepseek-chat"},
    "local": {"base_url": "http://localhost:11434/v1/", "model": "llama3.2:3b"},
}

API_KEY = os.getenv("API_KEY")
SAGLAYICI = os.getenv("SAGLAYICI", "gemini")

JUDGE_API_KEY = os.getenv("JUDGE_API_KEY")
JUDGE_SAGLAYICI = os.getenv("JUDGE_SAGLAYICI", "gemini_lite")


def prompt_olustur(baglam: str, soru: str) -> str:
    return (
        "Aşağıdaki metne dayanarak soruyu kısa ve net cevapla. "
        "Cevabı sadece metindeki bilgiye dayandır.\n\n"
        f"Metin: {baglam}\n\n"
        f"Soru: {soru}"
    )


def testleri_calistir():
    ayar = SAGLAYICILAR[SAGLAYICI]
    fonksiyon = partial(ai_cevap_al, api_key=API_KEY, **ayar)
    judge_ayar = SAGLAYICILAR[JUDGE_SAGLAYICI]

    print(f"\n=== {SAGLAYICI} test sonuçları (judge: {JUDGE_SAGLAYICI}, {len(TEST_CASES)} soru) ===\n")

    sonuclar = []
    for i, test in enumerate(TEST_CASES, start=1):
        soru, referans, baglam = test["soru"], test["referans_cevap"], test["baglam"]
        try:
            prompt = prompt_olustur(baglam, soru)
            uretilen_cevap = fonksiyon(prompt)

            embedding_skoru = anlam_benzerligi_skoru(referans, uretilen_cevap)
            judge_skoru, judge_ham_cevap = llm_judge_skoru(soru, referans, uretilen_cevap,
                                                            api_key=JUDGE_API_KEY, **judge_ayar)

            print(f"[{i}/{len(TEST_CASES)}] soru: {soru}")
            print(f"    referans: {referans}")
            print(f"    cevap: {uretilen_cevap}")
            print(f"    judge diyor ki: {judge_ham_cevap.strip()}")
            print(f"    embedding: {embedding_skoru:.3f}  judge: {judge_skoru:.3f}\n")

            sonuclar.append({
                "soru": soru, "referans_cevap": referans, "uretilen_cevap": uretilen_cevap,
                "embedding_skoru": embedding_skoru, "judge_skoru": judge_skoru, "hata": None,
            })
        except Exception as hata:
            print(f"[{i}/{len(TEST_CASES)}] HATA: {hata}\n")
            sonuclar.append({
                "soru": soru, "referans_cevap": referans, "uretilen_cevap": None,
                "embedding_skoru": None, "judge_skoru": None, "hata": str(hata),
            })

    basarili = [s for s in sonuclar if s["hata"] is None]
    if basarili:
        ort_embedding = sum(s["embedding_skoru"] for s in basarili) / len(basarili)
        ort_judge = sum(s["judge_skoru"] for s in basarili) / len(basarili)
        print(f"Ortalama embedding skoru: {ort_embedding:.3f}  ({len(basarili)}/{len(sonuclar)} başarılı)")
        print(f"Ortalama judge skoru: {ort_judge:.3f}")
    else:
        print("Hiçbir test başarıyla tamamlanamadı.")

    os.makedirs("sonuclar", exist_ok=True)
    dosya_adi = os.path.join("sonuclar", f"sonuclar_{SAGLAYICI}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(dosya_adi, "w", encoding="utf-8") as f:
        json.dump({
            "saglayici": SAGLAYICI, "judge": JUDGE_SAGLAYICI,
            "tarih": datetime.now().isoformat(), "sonuclar": sonuclar,
        }, f, ensure_ascii=False, indent=2)
    print(f"\nSonuçlar kaydedildi: {dosya_adi}")


if __name__ == "__main__":
    print("Hangi test türünü çalıştırmak istersin?")
    print("1) Fonksiyonel Test (soru-cevap testlerini çalıştır)")
    print("2) Regresyon Testi (son iki sonucu karşılaştır)")
    print("3) Güvenlik Testi (adversarial/jailbreak istemleriyle test et)")
    secim = input("Seçim (1/2/3): ").strip()

    if secim == "1":
        testleri_calistir()
    elif secim == "2":
        import regresyon
        regresyon.regresyon_testi_calistir(SAGLAYICI)
    elif secim == "3":
        import guvenlik
        ayar = SAGLAYICILAR[SAGLAYICI]
        judge_ayar = SAGLAYICILAR[JUDGE_SAGLAYICI]
        guvenlik.guvenlik_testi_calistir(
            api_key=API_KEY, base_url=ayar["base_url"], model=ayar["model"],
            judge_api_key=JUDGE_API_KEY, judge_base_url=judge_ayar["base_url"], judge_model=judge_ayar["model"],
            saglayici_adi=SAGLAYICI,
        )
    else:
        print("Geçersiz seçim.")