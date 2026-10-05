"""
Batch Mode ile toplu LLM testi. Sorular tek tek değil, hepsi birden
Google'a gönderiliyor, arka planda işleniyor, sonuçlar toplu halde
geri alınıyor. Dakikalık/günlük canlı istek limitlerine takılmıyoruz
çünkü batch işleri ayrı, çok daha yüksek bir kota havuzunu kullanıyor.
"""

import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from test_cases import TEST_CASES
from scoring import anlam_benzerligi_skoru, llm_judge_skoru

load_dotenv()

API_KEY = os.getenv("API_KEY")
MODEL = "gemini-3.5-flash-lite"

JUDGE_API_KEY = os.getenv("JUDGE_API_KEY")
JUDGE_MODEL = "gemini-3.5-flash-lite"
JUDGE_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

client = genai.Client(api_key=API_KEY)


def batch_isini_olustur():
    istekler = [
        {"contents": [{"parts": [{"text": test["soru"]}], "role": "user"}]}
        for test in TEST_CASES
    ]
    is_ = client.batches.create(
        model=MODEL,
        src=istekler,
        config={"display_name": f"llm-test-{datetime.now().strftime('%Y%m%d_%H%M%S')}"},
    )
    print(f"Batch iş oluşturuldu: {is_.name}")
    return is_.name


def batch_isini_bekle(is_adi):
    tamamlanan = {"JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED", "JOB_STATE_EXPIRED"}
    is_ = client.batches.get(name=is_adi)
    while is_.state.name not in tamamlanan:
        print(f"Durum: {is_.state.name}, 30 sn sonra tekrar kontrol edilecek...")
        time.sleep(30)
        is_ = client.batches.get(name=is_adi)
    print(f"İş tamamlandı: {is_.state.name}")
    return is_


def sonuclari_degerlendir(is_):
    if is_.state.name != "JOB_STATE_SUCCEEDED":
        print("İş başarısız oldu, sonuç değerlendirilemiyor.")
        return

    sonuclar = []
    for i, (test, yanit) in enumerate(zip(TEST_CASES, is_.dest.inlined_responses), start=1):
        soru, referans = test["soru"], test["referans_cevap"]

        if yanit.error:
            print(f"[{i}/{len(TEST_CASES)}] HATA: {yanit.error}")
            sonuclar.append({"soru": soru, "referans_cevap": referans, "uretilen_cevap": None,
                              "embedding_skoru": None, "judge_skoru": None, "hata": str(yanit.error)})
            continue

        uretilen_cevap = yanit.response.text
        embedding_skoru = anlam_benzerligi_skoru(referans, uretilen_cevap)
        judge_skoru = llm_judge_skoru(soru, referans, uretilen_cevap,
                                       api_key=JUDGE_API_KEY, base_url=JUDGE_BASE_URL, model=JUDGE_MODEL)
        print(f"[{i}/{len(TEST_CASES)}] embedding: {embedding_skoru:.3f}  judge: {judge_skoru:.3f}")

        sonuclar.append({"soru": soru, "referans_cevap": referans, "uretilen_cevap": uretilen_cevap,
                          "embedding_skoru": embedding_skoru, "judge_skoru": judge_skoru, "hata": None})

    basarili = [s for s in sonuclar if s["hata"] is None]
    if basarili:
        ort_embedding = sum(s["embedding_skoru"] for s in basarili) / len(basarili)
        ort_judge = sum(s["judge_skoru"] for s in basarili) / len(basarili)
        print(f"\nOrtalama embedding skoru: {ort_embedding:.3f} ({len(basarili)}/{len(sonuclar)} başarılı)")
        print(f"Ortalama judge skoru: {ort_judge:.3f}")

    os.makedirs("sonuclar", exist_ok=True)
    dosya_adi = os.path.join("sonuclar", f"sonuclar_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(dosya_adi, "w", encoding="utf-8") as f:
        json.dump({"model": MODEL, "tarih": datetime.now().isoformat(), "sonuclar": sonuclar},
                   f, ensure_ascii=False, indent=2)
    print(f"Sonuçlar kaydedildi: {dosya_adi}")


if __name__ == "__main__":
    is_adi = batch_isini_olustur()
    is_ = batch_isini_bekle(is_adi)
    sonuclari_degerlendir(is_)