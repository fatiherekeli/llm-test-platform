import streamlit as st
import os
import regresyon
import guvenlik
import time
from dotenv import load_dotenv

st.set_page_config(page_title="LLM Test Platformu", layout="wide")

from test_cases import TEST_CASES
from llm_client import ai_cevap_al
from scoring import anlam_benzerligi_skoru, llm_judge_skoru

load_dotenv()

SAGLAYICILAR = {
    "claude": {"base_url": "https://api.anthropic.com/v1/", "model": "claude-sonnet-4-6", "api_key_env": "ANTHROPIC_API_KEY"},
    "gemini": {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai/", "model": "gemini-3.5-flash-lite", "api_key_env": "GEMINI_API_KEY"},
    "gemini_lite": {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai/", "model": "gemini-3.5-flash-lite", "api_key_env": "GEMINI_API_KEY"},
    "openai": {"base_url": "https://api.openai.com/v1", "model": "gpt-4o", "api_key_env": "OPENAI_API_KEY"},
    "deepseek": {"base_url": "https://api.deepseek.com", "model": "deepseek-chat", "api_key_env": "DEEPSEEK_API_KEY"},
    "local": {"base_url": "http://localhost:11434/v1/", "model": "llama3.2:3b", "api_key_env": None},
     "local_qwen": {"base_url": "http://localhost:11434/v1/", "model": "qwen3.5:2b", "api_key_env": None},
}


def anahtar_al(saglayici_adi):
    env_adi = SAGLAYICILAR[saglayici_adi]["api_key_env"]
    return os.getenv(env_adi) if env_adi else "ollama"

def prompt_olustur(baglam: str, soru: str) -> str:
    return (
        "Aşağıdaki metne dayanarak soruyu kısa ve net cevapla. "
        "Cevabı sadece metindeki bilgiye dayandır.\n\n"
        f"Metin: {baglam}\n\nSoru: {soru}"
    )


def fonksiyonel_test_calistir(saglayici, judge_saglayici, api_key, judge_api_key):
    ayar = SAGLAYICILAR[saglayici]
    judge_ayar = SAGLAYICILAR[judge_saglayici]
    sonuclar = []
    for test in TEST_CASES:
        prompt = prompt_olustur(test["baglam"], test["soru"])

        # 1. adım: test edilen modelden cevabı al
        try:
            cevap = ai_cevap_al(
                prompt, api_key=api_key,
                base_url=ayar["base_url"], model=ayar["model"],
            )
        except Exception as hata:
            sonuclar.append({"Soru": test["soru"], "Hata": f"Model hatası: {hata}"})
            continue

        satir = {"Soru": test["soru"], "Referans": test["referans_cevap"], "Cevap": cevap}

        # 2. adım: skorlamayı (embedding + judge) ayrı dene
        try:
            embedding_skoru = anlam_benzerligi_skoru(test["referans_cevap"], cevap)
            judge_skoru, judge_sebep = llm_judge_skoru(
                test["soru"], test["referans_cevap"], cevap,
                api_key=judge_api_key,
                base_url=judge_ayar["base_url"], model=judge_ayar["model"],
            )
            satir["Embedding"] = round(embedding_skoru, 3)
            satir["Judge"] = judge_skoru
        except Exception as hata:
            satir["Judge Hatası"] = str(hata)

        sonuclar.append(satir)

    return sonuclar


def regresyon_test_calistir(saglayici, judge_saglayici, api_key, judge_api_key):
    return regresyon.regresyon_verisi_getir(saglayici)


def guvenlik_test_calistir(saglayici, judge_saglayici, api_key, judge_api_key):
    ayar = SAGLAYICILAR[saglayici]
    judge_ayar = SAGLAYICILAR[judge_saglayici]
    return guvenlik.guvenlik_testi_calistir(
        api_key=api_key, base_url=ayar["base_url"], model=ayar["model"],
        judge_api_key=judge_api_key, judge_base_url=judge_ayar["base_url"], judge_model=judge_ayar["model"],
        saglayici_adi=saglayici,
    )


def performans_test_calistir(saglayici, judge_saglayici, api_key, judge_api_key):
    ayar = SAGLAYICILAR[saglayici]
    sonuclar = []
    for test in TEST_CASES:
        prompt = prompt_olustur(test["baglam"], test["soru"])
        baslangic = time.time()
        try:
            cevap = ai_cevap_al(
                prompt, api_key=api_key,
                base_url=ayar["base_url"], model=ayar["model"],
            )
            sure = time.time() - baslangic
            sonuclar.append({
                "Soru": test["soru"],
                "Süre (saniye)": round(sure, 2),
                "Cevap": cevap,
            })
        except Exception as hata:
            sure = time.time() - baslangic
            sonuclar.append({
                "Soru": test["soru"],
                "Süre (saniye)": round(sure, 2),
                "Hata": str(hata),
            })
    return sonuclar


TUTARLILIK_TEKRAR = 3

def tutarlilik_test_calistir(saglayici, judge_saglayici, api_key, judge_api_key):
    ayar = SAGLAYICILAR[saglayici]
    sonuclar = []
    for test in TEST_CASES:
        prompt = prompt_olustur(test["baglam"], test["soru"])
        try:
            cevaplar = [
                ai_cevap_al(prompt, api_key=api_key, base_url=ayar["base_url"], model=ayar["model"])
                for _ in range(TUTARLILIK_TEKRAR)
            ]
            bos_sayisi = sum(1 for c in cevaplar if not c or not c.strip())
            bos_orani = round(bos_sayisi / len(cevaplar) * 100, 1)

            benzerlikler = []
            for i in range(len(cevaplar)):
                for j in range(i + 1, len(cevaplar)):
                    if cevaplar[i].strip() and cevaplar[j].strip():
                        benzerlikler.append(anlam_benzerligi_skoru(cevaplar[i], cevaplar[j]))
                    # boş cevabı içeren çift, ortalamaya hiç katılmıyor

            ortalama = round(sum(benzerlikler) / len(benzerlikler), 3) if benzerlikler else None

            satir = {
                "Soru": test["soru"],
                "Tutarlılık Skoru": ortalama,
                "Boş Cevap Oranı (%)": bos_orani,
            }
            for i, cevap in enumerate(cevaplar, start=1):
                satir[f"Cevap {i}"] = cevap if cevap else "(boş cevap)"
            sonuclar.append(satir)
        except Exception as hata:
            sonuclar.append({"Soru": test["soru"], "Hata": str(hata)})
    return sonuclar


TEST_TURLERI = {
    "Fonksiyonel Test": fonksiyonel_test_calistir,
    "Regresyon Testi": regresyon_test_calistir,
    "Güvenlik Testi": guvenlik_test_calistir,
    "Performans Testi": performans_test_calistir,
    "Tutarlılık Testi": tutarlilik_test_calistir,
}

st.title("LLM Test Platformu")

col1, col2 = st.columns(2)
with col1:
    saglayici = st.selectbox("Sağlayıcı", list(SAGLAYICILAR.keys()), index=list(SAGLAYICILAR.keys()).index("local"))
with col2:
    judge_saglayici = st.selectbox("Judge", list(SAGLAYICILAR.keys()), index=list(SAGLAYICILAR.keys()).index("gemini_lite"))

test_turu = st.selectbox("Test Türü", list(TEST_TURLERI.keys()))

col_a, col_b = st.columns(2)
with col_a:
    calistir_buton = st.button("Çalıştır")
with col_b:
    hepsi_buton = st.button("Tüm Testleri Çalıştır")

SUTUN_AYARLARI = {
    "Cevap": st.column_config.TextColumn(width="large"),
    "Cevap 1": st.column_config.TextColumn(width="large"),
    "Cevap 2": st.column_config.TextColumn(width="large"),
    "Cevap 3": st.column_config.TextColumn(width="large"),
    "Referans": st.column_config.TextColumn(width="medium"),
    "Judge Hatası": st.column_config.TextColumn(width="large"),
}

if calistir_buton:
    api_key = anahtar_al(saglayici)
    judge_api_key = anahtar_al(judge_saglayici)
    with st.spinner("Test çalışıyor..."):
        sonuclar = TEST_TURLERI[test_turu](saglayici, judge_saglayici, api_key, judge_api_key)
    st.dataframe(sonuclar, use_container_width=True, column_config=SUTUN_AYARLARI)

if hepsi_buton:
    api_key = anahtar_al(saglayici)
    judge_api_key = anahtar_al(judge_saglayici)
    for ad, fonksiyon in TEST_TURLERI.items():
        st.subheader(ad)
        with st.spinner(f"{ad} çalışıyor..."):
            try:
                sonuc = fonksiyon(saglayici, judge_saglayici, api_key, judge_api_key)
                st.dataframe(sonuc, use_container_width=True, column_config=SUTUN_AYARLARI)
            except Exception as hata:
                st.error(f"{ad} çalıştırılırken hata: {hata}")