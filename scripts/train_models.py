"""Train and export real ML model checkpoints for SaathiAI M09 (Voice) and M12 (Text).

Generates trained model artifacts in models/voice/ and models/text/.
"""

import json
from pathlib import Path
import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_VOICE_DIR = BASE_DIR / "models" / "voice"
MODELS_TEXT_DIR = BASE_DIR / "models" / "text"


def train_voice_model():
    """Train Gradient Boosting model on acoustic distress feature profiles."""
    print("--- Training Voice Distress Model (M09) ---")
    MODELS_VOICE_DIR.mkdir(parents=True, exist_ok=True)

    np.random.seed(42)
    n_samples = 1200

    # Feature definitions (26 dimensions):
    # 0: pitch_mean, 1: pitch_std, 2: pitch_range, 3: speech_rate, 4: pause_ratio,
    # 5: pause_count, 6: energy_mean, 7: energy_std, 8: jitter, 9: shimmer,
    # 10: spectral_centroid_mean, 11: zcr_mean, 12: voiced_fraction, 13..25: mfcc_0..12

    feature_names = [
        "pitch_mean", "pitch_std", "pitch_range", "speech_rate_syl_per_sec",
        "pause_ratio", "pause_count", "energy_mean", "energy_std",
        "jitter", "shimmer", "spectral_centroid_mean", "zcr_mean", "voiced_fraction"
    ] + [f"mfcc_{i}" for i in range(13)]

    X = np.zeros((n_samples, len(feature_names)))
    y = np.zeros(n_samples)

    for i in range(n_samples):
        # Scenario profile generator
        profile = np.random.choice(["calm", "mild_anxiety", "moderate_distress", "acute_panic", "sobbing_trauma", "monotone_depression"])
        
        if profile == "calm":
            p_mean = np.random.uniform(110, 190)
            p_std = np.random.uniform(10, 25)
            p_range = np.random.uniform(40, 100)
            rate = np.random.uniform(3.0, 4.8)
            pause_r = np.random.uniform(0.10, 0.30)
            jitter = np.random.uniform(0.005, 0.015)
            shimmer = np.random.uniform(0.015, 0.035)
            centroid = np.random.uniform(1200, 1800)
            target = np.random.uniform(5, 25)
        elif profile == "mild_anxiety":
            p_mean = np.random.uniform(160, 230)
            p_std = np.random.uniform(25, 45)
            p_range = np.random.uniform(90, 160)
            rate = np.random.uniform(4.2, 5.8)
            pause_r = np.random.uniform(0.20, 0.40)
            jitter = np.random.uniform(0.015, 0.030)
            shimmer = np.random.uniform(0.030, 0.055)
            centroid = np.random.uniform(1700, 2400)
            target = np.random.uniform(30, 50)
        elif profile == "moderate_distress":
            p_mean = np.random.uniform(200, 280)
            p_std = np.random.uniform(40, 65)
            p_range = np.random.uniform(140, 220)
            rate = np.random.uniform(4.8, 6.5)
            pause_r = np.random.uniform(0.30, 0.55)
            jitter = np.random.uniform(0.025, 0.045)
            shimmer = np.random.uniform(0.045, 0.075)
            centroid = np.random.uniform(2200, 3100)
            target = np.random.uniform(52, 74)
        elif profile == "acute_panic":
            p_mean = np.random.uniform(260, 390)
            p_std = np.random.uniform(60, 95)
            p_range = np.random.uniform(200, 320)
            rate = np.random.uniform(5.5, 7.5)
            pause_r = np.random.uniform(0.40, 0.70)
            jitter = np.random.uniform(0.040, 0.075)
            shimmer = np.random.uniform(0.065, 0.120)
            centroid = np.random.uniform(2800, 4200)
            target = np.random.uniform(78, 98)
        elif profile == "sobbing_trauma":
            p_mean = np.random.uniform(180, 320)
            p_std = np.random.uniform(50, 90)
            p_range = np.random.uniform(160, 280)
            rate = np.random.uniform(2.0, 4.0)
            pause_r = np.random.uniform(0.45, 0.80)
            jitter = np.random.uniform(0.045, 0.085)
            shimmer = np.random.uniform(0.070, 0.130)
            centroid = np.random.uniform(2000, 3500)
            target = np.random.uniform(75, 96)
        else: # monotone_depression
            p_mean = np.random.uniform(100, 160)
            p_std = np.random.uniform(4, 12)
            p_range = np.random.uniform(15, 50)
            rate = np.random.uniform(2.2, 3.5)
            pause_r = np.random.uniform(0.35, 0.65)
            jitter = np.random.uniform(0.010, 0.025)
            shimmer = np.random.uniform(0.025, 0.050)
            centroid = np.random.uniform(1100, 1600)
            target = np.random.uniform(45, 70)

        pause_count = int(pause_r * np.random.uniform(5, 18))
        energy_m = np.random.uniform(0.02, 0.15)
        energy_std = energy_m * np.random.uniform(0.4, 1.4)
        zcr_m = np.random.uniform(0.03, 0.12)
        voiced_f = np.random.uniform(0.45, 0.90)
        mfccs = np.random.normal(loc=0.0, scale=1.0, size=13)

        row = [
            p_mean, p_std, p_range, rate, pause_r, pause_count,
            energy_m, energy_std, jitter, shimmer, centroid, zcr_m, voiced_f
        ] + list(mfccs)

        X[i] = row
        y[i] = np.clip(target + np.random.normal(0, 3.0), 0, 100)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("regressor", GradientBoostingRegressor(
            n_estimators=120,
            max_depth=4,
            learning_rate=0.08,
            random_state=42
        ))
    ])

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    print(f"Voice Model Trained: R2 = {r2:.4f}, MAE = {mae:.2f}")

    joblib.dump(pipeline, MODELS_VOICE_DIR / "voice_distress_model.joblib")
    with open(MODELS_VOICE_DIR / "voice_feature_names.json", "w", encoding="utf-8") as f:
        json.dump(feature_names, f, indent=2)
    print(f"Artifacts saved to {MODELS_VOICE_DIR}")


def train_text_model():
    """Train Multilingual TF-IDF + Regressor model for text distress classification."""
    print("\n--- Training Text Distress Model (M12) ---")
    MODELS_TEXT_DIR.mkdir(parents=True, exist_ok=True)

    # Synthetic multilingual text corpus across distress levels
    corpus = [
        # Calm / Informational (0-20)
        ("Hello, I am just calling to check the working hours of your centre.", 8.0),
        ("Can you please guide me on how to register for the workshop?", 12.0),
        ("नमस्ते, क्या आप मुझे नजदीकी स्वास्थ्य केंद्र का पता बता सकते हैं?", 10.0),
        ("Main enquiry ke liye call kar raha hoon, OPD ka time kya hai?", 11.0),
        ("Everything is fine here, just needed some standard information.", 5.0),
        ("Thank you for the update, have a nice day.", 2.0),
        ("कृपया मुझे फॉर्म भरने की प्रक्रिया समझाएं।", 9.0),

        # Mild anxiety / Inquiry (25-45)
        ("I am feeling a bit stressed about my exam results lately.", 32.0),
        ("I haven't been sleeping well for the past two days, feeling restless.", 38.0),
        ("Mujhe thodi ghabrahat ho rahi hai, kuch samajh nahi aa raha.", 40.0),
        ("मुझे थोड़ी चिंता हो रही है अपने भविष्य को लेकर।", 35.0),
        ("I feel a little overwhelmed with work pressure and need someone to talk to.", 42.0),
        ("Pichle kuch dino se man udaas sa rehta hai.", 44.0),

        # Moderate distress (50-70)
        ("I had a terrible fight at home and I feel totally trapped and isolated.", 62.0),
        ("He is constantly threatening to throw me out of the house. I am scared.", 68.0),
        ("Mujhe bohot dar lag raha hai, woh mujhe harass kar rahe hain.", 65.0),
        ("घर पर बहुत झगड़ा हुआ है और मुझे अपनी सुरक्षा का डर लग रहा है।", 67.0),
        ("I don't know where to go, my family is not supporting me and I am crying.", 60.0),
        ("Please help me find a shelter, I cannot stay in this abusive place.", 72.0),
        ("Mere paas koi rasta nahi bacha hai, bohot pareshaan hoon.", 64.0),

        # High / Critical distress (75-100)
        ("Please send police immediately! He has a knife and is breaking the door!", 98.0),
        ("Bachao! Koi bacha lo mujhe! Bahar se aag laga di hai!", 100.0),
        ("He is physically beating me right now, please send help hurry!", 96.0),
        ("मदद करो, मेरी जान खतरे में है, वह मुझे जान से मारने की धमकी दे रहा है!", 98.0),
        ("I can't take this pain anymore, I feel like ending my life right now.", 95.0),
        ("Mujhe bachao, mere upar attack hua hai, khoon beh raha hai!", 97.0),
        ("I am hiding inside the bathroom, please don't hang up, he is trying to break in.", 92.0),
        ("I have swallowed pills and I am losing consciousness, please help.", 99.0),
    ]

    # Augment with variations
    augmented_texts = []
    augmented_targets = []

    for text, score in corpus:
        for _ in range(25):
            noise = np.random.normal(0, 2.0)
            augmented_texts.append(text)
            augmented_targets.append(np.clip(score + noise, 0, 100))

    X_train, X_test, y_train, y_test = train_test_split(
        augmented_texts, augmented_targets, test_size=0.2, random_state=42
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=1200,
            sublinear_tf=True
        )),
        ("regressor", RandomForestRegressor(
            n_estimators=100,
            max_depth=6,
            random_state=42
        ))
    ])

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    print(f"Text Model Trained: R2 = {r2:.4f}, MAE = {mae:.2f}")

    joblib.dump(pipeline, MODELS_TEXT_DIR / "text_distress_model.joblib")
    print(f"Artifacts saved to {MODELS_TEXT_DIR}")


if __name__ == "__main__":
    train_voice_model()
    train_text_model()
    print("\n[SUCCESS] All ML models trained and exported successfully.")
