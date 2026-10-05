"""
Test soruları Hugging Face'teki hazır bir veri setinden (SQuAD) çekiliyor.
Her örnek; soru, referans (doğru) cevap VE cevabın içinde geçtiği kaynak
paragraf (context/baglam) ile birlikte geliyor. SQuAD aslında "okuduğunu
anlama" testi — modele kaynak metni de vermemiz lazım, yoksa ezbere
bilmesini istemiş oluruz ki bu adil bir test olmaz.
"""

from datasets import load_dataset


def test_setini_yukle(adet: int = 30):
    veri = load_dataset("rajpurkar/squad", split="validation")
    veri = veri.shuffle(seed=42).select(range(adet))
    return [
        {
            "soru": ornek["question"],
            "referans_cevap": ornek["answers"]["text"][0],
            "baglam": ornek["context"],
        }
        for ornek in veri
    ]


TEST_CASES = test_setini_yukle(adet=1)


def guvenlik_test_seti_yukle(harmful_adet: int = 6, benign_adet: int = 2, seed: int = 42):
    """
    JailbreakBench/JBB-Behaviors veri setinden (100 zararlı + 100 zararsız davranış,
    OpenAI kullanım politikasındaki kategorilere göre) rastgele bir alt küme çeker.
    SQuAD'daki gibi shuffle(seed=...) ile sabitliyoruz ki her çalıştırmada aynı
    örnekler gelsin (tekrarlanabilirlik).
    """
    zararli = load_dataset("JailbreakBench/JBB-Behaviors", name="behaviors", split="harmful")
    zararli = zararli.shuffle(seed=seed).select(range(harmful_adet))

    zararsiz = load_dataset("JailbreakBench/JBB-Behaviors", name="behaviors", split="benign")
    zararsiz = zararsiz.shuffle(seed=seed).select(range(benign_adet))

    sonuc = []
    for ornek in zararli:
        sonuc.append({"ad": f"[JBB/{ornek['Category']}] {ornek['Behavior']}", "istem": ornek["Goal"]})
    for ornek in zararsiz:
        sonuc.append({"ad": f"[JBB/benign] {ornek['Behavior']}", "istem": ornek["Goal"]})
    return sonuc


GUVENLIK_ALT_KUMESI = guvenlik_test_seti_yukle()