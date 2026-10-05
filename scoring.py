"""
Embedding tabanlı anlam benzerligi VE LLM-as-judge skorlama.
Ikisi birlikte iki farkli olcum yontemi sunuyor.

LLM judge artik yapilandirilmis cikti (structured output) kullaniyor:
judge'a serbest metin yazdirip sonra regex ile puan aramak yerine,
cevabin Pydantic semasina uyacagi garanti ediliyor - judge formatindan
saptigi icin sessizce 0.0 puan verme riski ortadan kalkiyor.
"""

from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, util
from openai import OpenAI

_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


def anlam_benzerligi_skoru(referans_cevap: str, uretilen_cevap: str) -> float:
    embeddings = _model.encode(
        [referans_cevap, uretilen_cevap], convert_to_tensor=True
    )
    benzerlik = util.cos_sim(embeddings[0], embeddings[1])
    return float(benzerlik.item())


JUDGE_PROMPT = """Sen bir cevap degerlendiricisisin. Asagida bir soru, dogru kabul edilen
bir referans cevap ve test edilen modelin verdigi cevap var. Test edilen cevabin,
referans cevapla ayni bilgiyi dogru veriyor mu degerlendir.

Onemli: Cevabin uzunluguna veya ne kadar detayli/kendinden emin gorundugune
aldanma. Referans cevaptaki spesifik bilginin, test edilen cevabin icinde
(ister kisa ister uzun bir cevabin icine gomulu olsun) acikca ve dogru
sekilde gecip gecmedigine bak. Referans bilgi cevabin icinde dogru sekilde
varsa yuksek puan ver, yoksa dusuk puan ver - cevabin ne kadar uzun veya
akici yazildigi puani etkilemesin.

Soru: {soru}
Referans cevap: {referans}
Test edilen cevap: {uretilen}
"""


class DegerlendirmeSonucu(BaseModel):
    sebep: str
    puan: int


def llm_judge_skoru(soru: str, referans_cevap: str, uretilen_cevap: str,
                     api_key: str, base_url: str, model: str):
    prompt = JUDGE_PROMPT.format(soru=soru, referans=referans_cevap, uretilen=uretilen_cevap)

    client = OpenAI(api_key=api_key, base_url=base_url, max_retries=5)
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format=DegerlendirmeSonucu,
    )
    sonuc = completion.choices[0].message.parsed

    puan = sonuc.puan / 10.0
    return puan, sonuc.sebep


if __name__ == "__main__":
    referans = "Türkiye'nin başkenti Ankara'dır."
    iyi_cevap = "Ankara, Türkiye'nin başkentidir."
    kotu_cevap = "Bugün hava çok güzel."

    print("İyi/benzer cevap skoru:", anlam_benzerligi_skoru(referans, iyi_cevap))
    print("Kötü/alakasız cevap skoru:", anlam_benzerligi_skoru(referans, kotu_cevap))
