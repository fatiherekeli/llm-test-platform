"""
Regresyon testi: modelin/prompt'un aynı test setinde zaman içinde
tutarlı kalıp kalmadığını, önceki bir çalıştırmayla karşılaştırarak
kontrol eder. Yeni API çağrısı gerektirmez - sadece elindeki
sonuç dosyalarını karşılaştırır.
"""

import glob
import json


def son_iki_dosyayi_bul(saglayici: str):
    dosyalar = sorted(glob.glob(f"sonuclar/sonuclar_{saglayici}_*.json"))
    gecerli_dosyalar = []
    for dosya in dosyalar:
        with open(dosya, "r", encoding="utf-8") as f:
            veri = json.load(f)
        if any(s["judge_skoru"] is not None for s in veri["sonuclar"]):
            gecerli_dosyalar.append(dosya)
    if len(gecerli_dosyalar) < 2:
        return None, None
    return gecerli_dosyalar[-2], gecerli_dosyalar[-1]


def regresyon_testi_calistir(saglayici: str):
    eski_dosya, yeni_dosya = son_iki_dosyayi_bul(saglayici)
    if eski_dosya is None:
        print(f"'{saglayici}' için karşılaştırılacak en az 2 sonuç dosyası bulunamadı.")
        return

    with open(eski_dosya, "r", encoding="utf-8") as f:
        eski = json.load(f)
    with open(yeni_dosya, "r", encoding="utf-8") as f:
        yeni = json.load(f)

    eski_skorlar = {s["soru"]: s["judge_skoru"] for s in eski["sonuclar"] if s["judge_skoru"] is not None}
    yeni_skorlar = {s["soru"]: s["judge_skoru"] for s in yeni["sonuclar"] if s["judge_skoru"] is not None}

    print(f"\n=== Regresyon Testi: {eski_dosya} -> {yeni_dosya} ===\n")

    dusenler, yukselenler, ayniler = [], [], []
    for soru, eski_puan in eski_skorlar.items():
        if soru not in yeni_skorlar:
            continue
        yeni_puan = yeni_skorlar[soru]
        fark = yeni_puan - eski_puan
        if fark < 0:
            dusenler.append((soru, eski_puan, yeni_puan))
        elif fark > 0:
            yukselenler.append((soru, eski_puan, yeni_puan))
        else:
            ayniler.append(soru)

    if dusenler:
        print(f"DÜŞEN sorular ({len(dusenler)}):")
        for soru, e, y in dusenler:
            print(f"  - {soru}\n    {e:.1f} -> {y:.1f}")
    if yukselenler:
        print(f"\nYÜKSELEN sorular ({len(yukselenler)}):")
        for soru, e, y in yukselenler:
            print(f"  - {soru}\n    {e:.1f} -> {y:.1f}")

    print(f"\nDeğişmeyen: {len(ayniler)}, Düşen: {len(dusenler)}, Yükselen: {len(yukselenler)}")

    if eski_skorlar and yeni_skorlar:
        eski_ort = sum(eski_skorlar.values()) / len(eski_skorlar)
        yeni_ort = sum(yeni_skorlar.values()) / len(yeni_skorlar)
        print(f"Ortalama judge skoru: {eski_ort:.3f} -> {yeni_ort:.3f}  (fark: {yeni_ort - eski_ort:+.3f})")


def regresyon_verisi_getir(saglayici: str):
    eski_dosya, yeni_dosya = son_iki_dosyayi_bul(saglayici)
    if eski_dosya is None:
        return [{"Hata": f"'{saglayici}' için karşılaştırılacak en az 2 sonuç dosyası bulunamadı."}]

    with open(eski_dosya, "r", encoding="utf-8") as f:
        eski = json.load(f)
    with open(yeni_dosya, "r", encoding="utf-8") as f:
        yeni = json.load(f)

    eski_skorlar = {s["soru"]: s["judge_skoru"] for s in eski["sonuclar"] if s["judge_skoru"] is not None}
    yeni_skorlar = {s["soru"]: s["judge_skoru"] for s in yeni["sonuclar"] if s["judge_skoru"] is not None}

    sonuclar = []
    for soru, eski_puan in eski_skorlar.items():
        if soru not in yeni_skorlar:
            continue
        yeni_puan = yeni_skorlar[soru]
        sonuclar.append({
            "Soru": soru,
            "Eski Skor": eski_puan,
            "Yeni Skor": yeni_puan,
            "Fark": round(yeni_puan - eski_puan, 3),
        })
    return sonuclar