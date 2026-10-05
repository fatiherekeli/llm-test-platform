# LLM Test Platformu

Farklı yapay zeka modellerini aynı sorularla test edip doğruluk ve güvenlik açısından puanlayan bir test platformu. OpenAI API formatını destekleyen herhangi bir sağlayıcıya (Claude, Gemini, OpenAI, DeepSeek) ve Ollama ile yerelde çalışan modellere bağlanabilir.

## Neler yapıyor

**Fonksiyonel test.** Sorular SQuAD veri setinden gelir. Modelin cevabı doğru cevapla iki yöntemle karşılaştırılır: embedding benzerliği (cosine similarity) ve LLM-as-judge puanı.

**Güvenlik testi.** Kısıtlama atlatma, phishing, sistem promptu sızdırma gibi elle yazılmış istemlere ve JailbreakBench (JBB-Behaviors) veri setinden seçilen istemlere modelin nasıl yanıt verdiğine bakılır. Hakem model her cevaba 0 ile 10 arası puan verir, 10 tamamen güvenli demektir. Belirsiz puanlar insan incelemesi için işaretlenir. Sistem promptu sızdırma testinde modele gizli bir kod içeren gerçek bir sistem promptu verilir, kod cevapta aynen geçerse sızıntı sayılır.

**Regresyon testi.** Aynı modelin son iki sonuç dosyasını karşılaştırarak zaman içinde tutarlı kalıp kalmadığını kontrol eder. Yeni API çağrısı gerekmez.

**Kalibrasyon.** Güvenlik hakeminin kararlarını, insan puanı bilinen örneklerle karşılaştırarak ne kadar tutarlı olduğunu ölçer.

## Kurulum

Python 3.10 veya üstü önerilir.

```
pip install -r requirements.txt
```

Proje klasöründe `.env.example` dosyasını `.env` olarak kopyalayıp kullanacağın sağlayıcının anahtarını gir. `.env` dosyası git'e eklenmez, hiçbir zaman paylaşma.

Yerel model kullanacaksan [Ollama](https://ollama.com) kurup bir model indir, örneğin `ollama pull llama3.2:3b`.

## Kullanım

Arayüzle:

```
streamlit run app.py
```

Komut satırıyla (fonksiyonel, regresyon ve güvenlik testi için menü açılır):

```
python run_tests.py
```

Diğer betikler:

- `python kalibrasyon.py` hakem kalibrasyonunu çalıştırır.
- `python run_batch_test.py` testleri Gemini batch modunda toplu çalıştırır.

Sonuçlar `sonuclar/` klasörüne JSON olarak kaydedilir.

## Dosyalar

| Dosya | Görevi |
|---|---|
| `app.py` | Streamlit arayüzü |
| `run_tests.py` | Komut satırı test çalıştırıcı |
| `run_batch_test.py` | Gemini batch modu ile toplu test |
| `llm_client.py` | Tek fonksiyonla tüm sağlayıcılara bağlanan istemci |
| `scoring.py` | Embedding benzerliği ve LLM-as-judge puanlama |
| `guvenlik.py` | Güvenlik testleri ve güvenlik hakemi |
| `regresyon.py` | Sonuç karşılaştırma |
| `kalibrasyon.py` | Hakem kalibrasyonu |
| `test_cases.py` | Veri setlerinden test örneklerini yükler |

## Sınırlar

Hakem de bir yapay zeka modelidir ve hata yapabilir. Küçük yerel modeller hakem olarak zayıf kalır. Varsayılan örnek sayıları küçüktür, ciddi bir karşılaştırma için `test_cases.py` içinde artırılmalıdır.
