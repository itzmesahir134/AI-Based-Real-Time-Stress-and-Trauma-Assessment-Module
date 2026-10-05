# Model Card: M12 Text Distress Classifier

## Model Overview
- **Model Name:** SaathiAI Multilingual Text Distress Classifier (M12)
- **Model Version:** `v1.1.0-tfidf-rf`
- **Architecture:** Multilingual n-gram TF-IDF vectorizer + Random Forest Regressor ensembled with an 8-dimensional psychological distress lexicon matcher.
- **Languages Supported:** English (`en`), Hindi (`hi`), Hinglish/Romanized Hindi (`hi-Latn`), with extensible Indic dialect roots.
- **Intended Use:** Analyze caller transcripts in real time to quantify semantic urgency, threat presence, and emotional distress for helpline responder queues.

---

## Model Dimensions & Features

M12 extracts linguistic evidence across 8 structured psycholinguistic dimensions:
1. **Threat Indicators:** Words signaling physical violence, weapons, stalking, or active harm (`attack`, `knife`, `मारपीट`, `threat`).
2. **Fear Indicators:** Expressions of terror and acute anxiety (`scared`, `terrified`, `डर`, `ghabrahat`).
3. **Help Request Indicators:** Explicit pleas for urgent intervention (`help`, `please send`, `मदद`, `bachao`).
4. **Helplessness Indicators:** Despair and entrapment (`trapped`, `nowhere to go`, `मजबूर`, `koi rasta nahi`).
5. **Urgency Indicators:** Temporal immediacy signals (`immediately`, `hurry`, `urgent`, `turant`).
6. **Negative Affect Indicators:** General emotional pain and distress (`crying`, `pain`, `depression`, `udaas`).
7. **Self-Blame Indicators:** Internalized guilt and shame (`my fault`, `galti meri hai`).
8. **Uncertainty Indicators:** Disorientation and confusion (`confused`, `don't know`).

---

## Evaluation & Calibration

- **Continuous Score:** `0.0` (routine / administrative inquiry) to `100.0` (extreme active crisis).
- **Confidence Calibration:** Scales with word count, token density, and ASR transcription confidence.
- **Fairness & Cultural Sensitivity:** Accounts for colloquial Hindi phrasing and emotional idioms without penalizing polite conversational norms.
