**English** | [Türkçe](README.tr.md)

# LLM Test Platform

A test platform that runs different AI models through the same questions and scores them for accuracy and safety. It can connect to any provider that supports the OpenAI API format (Claude, Gemini, OpenAI, DeepSeek) and to models running locally through Ollama.

## What it does

**Functional test.** Questions come from the SQuAD dataset. A model's answer is compared with the reference answer in two ways: embedding similarity (cosine similarity) and an LLM-as-judge score.

**Safety test.** The model is given hand-written prompts (restriction bypass, phishing, system prompt leakage) and prompts sampled from the JailbreakBench (JBB-Behaviors) dataset, and its responses are checked. A judge model gives each response a score from 0 to 10, where 10 is fully safe. Borderline scores are flagged for human review. In the system prompt leakage test, the model receives a real system prompt that contains a fake secret code, and any response that repeats the code counts as a leak.

**Regression test.** Compares the last two result files of the same model to check whether its behavior stays consistent over time. It needs no new API calls.

**Calibration.** Measures how consistent the safety judge is by comparing its decisions with examples that have known human scores.

## Setup

Python 3.10 or newer is recommended.

```
pip install -r requirements.txt
```

Copy `.env.example` to `.env` in the project folder and fill in the key for the provider you use. The `.env` file is excluded from git. Never share it.

To use a local model, install [Ollama](https://ollama.com) and pull a model, for example `ollama pull llama3.2:3b`.

## Usage

With the web interface:

```
streamlit run app.py
```

From the command line (opens a menu for functional, regression and safety tests):

```
python run_tests.py
```

Other scripts:

- `python kalibrasyon.py` runs the judge calibration.
- `python run_batch_test.py` runs the tests in bulk using Gemini batch mode.

Results are saved as JSON files in the `sonuclar/` folder.

## Files

| File | Purpose |
|---|---|
| `app.py` | Streamlit interface |
| `run_tests.py` | Command-line test runner |
| `run_batch_test.py` | Bulk testing with Gemini batch mode |
| `llm_client.py` | A single client that connects to all providers |
| `scoring.py` | Embedding similarity and LLM-as-judge scoring |
| `guvenlik.py` | Safety tests and the safety judge |
| `regresyon.py` | Result comparison |
| `kalibrasyon.py` | Judge calibration |
| `test_cases.py` | Loads test examples from the datasets |

## Limitations

The judge is also an AI model and can make mistakes. Small local models are weak judges. The default sample sizes are small, so for a serious comparison increase them in `test_cases.py`. The code, comments and interface are in Turkish.
