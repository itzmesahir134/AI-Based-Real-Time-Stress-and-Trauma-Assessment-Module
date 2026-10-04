# Benchmark Speech Datasets: Acquisition, Licensing & Evaluation Guide

This guide documents the 5 speech benchmark sources evaluated for testing the **SAATHI-AI** audio processing pipeline.

---

## 1. CREMA-D (Crowd-sourced Emotional Multimodal Actors Dataset)

### Dataset Profile
- **Institution:** Cheyney University of Pennsylvania & University of Rochester
- **Official Source:** [https://github.com/CheyneyComputerScience/CREMA-D](https://github.com/CheyneyComputerScience/CREMA-D)
- **License:** Open Database License (ODbL) v1.0 / Open Data Commons Attribution License
- **Attribution Required:** Yes
- **Citation:**
  > Cao, H., Cooper, D. G., Keutmann, M. K., Gur, R. C., Nenkova, A., & Verma, R. (2014).  
  > *CREMA-D: Crowd-sourced Emotional Multimodal Actors Dataset.*  
  > IEEE Transactions on Affective Computing, 5(4), 377–390.
- **Commercial Restrictions:** Permissive with attribution and share-alike under ODbL.
- **Languages:** English.
- **Number of Speakers:** 91 professional actors (48 male, 43 female).
- **Demographics:** Diverse ethnic representation (African American, Asian, Caucasian, Hispanic, Unspecified).
- **Native Audio Format:** 16-bit uncompressed WAV, 16,000 Hz, Mono.
- **Approximate Download Size:** Full audio corpus is ~600 MB (7,442 clips); test subset is ~3 MB (32 clips).
- **Transcripts:** 12 standardized sentences:
  1. *It's eleven o'clock* (`IEO`)
  2. *That is exactly what happened* (`TIE`)
  3. *I'm on my way to the meeting* (`IOM`)
  4. *I wonder what this is about* (`IWW`)
  5. *The surface is slick* (`TSI`)
  6. *We've got to find the way out* (`WVO`)
  7. *Don't forget a jacket* (`DFA`)
  8. *I think I've seen this before* (`ITH`)
  9. *The movie is about to start* (`ITS`)
  10. *I would like a new alarm clock* (`TAI`)
  11. *I think I have an idea* (`TIE`)
  12. *More to it than meets the eye* (`MTI`)

### Available Affective Labels
- 6 categorical emotions:
  - `ANG` – Anger
  - `DIS` – Disgust
  - `FEA` – Fear
  - `HAP` – Happiness
  - `NEU` – Neutral
  - `SAD` – Sadness
- 4 emotional intensities:
  - `LO` – Low
  - `MD` – Medium
  - `HI` – High
  - `XX` – Unspecified (Neutral baseline)

### Testing Role in SAATHI-AI
Baseline clean speech, acoustic stability under intense vocalizations (screaming, sobbing, shouting), diverse ethnic accents, and VAD accuracy on varying speaking tempos.

---

## 2. RAVDESS (Ryerson Audio-Visual Database of Emotional Speech and Song)

### Dataset Profile
- **Institution:** Ryerson University (SMART Lab)
- **Official Source:** [Zenodo Record 1188976](https://zenodo.org/records/1188976)
- **License:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)
- **Attribution Required:** Yes
- **Citation:**
  > Livingstone, S. R., & Russo, F. A. (2018).  
  > *The Ryerson Audio-Visual Database of Emotional Speech and Song (RAVDESS): A dynamic, multimodal set of facial and vocal expressions in North American English.*  
  > PLoS ONE, 13(5), e0196391.
- **Commercial Restrictions:** Non-commercial research only (CC BY-NC-SA 4.0). Evaluation and benchmarking are permitted.
- **Languages:** North American English.
- **Number of Speakers:** 24 professional actors (12 male, 12 female).
- **Native Audio Format:** 16-bit uncompressed WAV, 48,000 Hz, Stereo. (Normalized to 16,000 Hz Mono in test set).
- **Approximate Download Size:** Full audio speech is ~1.04 GB; test subset is ~6 MB (16 clips).
- **Transcripts:** Two standardized statements:
  1. *"Kids are talking by the door"* (Statement 01)
  2. *"Dogs are sitting by the door"* (Statement 02)

### Naming Identifier Structure
`Modality (03 = audio-only) - VocalChannel (01 = speech) - Emotion (01-08) - Intensity (01-02) - Statement (01-02) - Repetition (01-02) - Actor (01-24)`

### Available Affective Labels
- Emotions:
  - `01` – Neutral
  - `02` – Calm
  - `03` – Happy
  - `04` – Sad
  - `05` – Angry
  - `06` – Fearful
  - `07` – Disgust
  - `08` – Surprised
- Intensities:
  - `01` – Normal
  - `02` – Strong

### Testing Role in SAATHI-AI
Calm vocalization baselines, emotional intensity differentiation (normal vs strong arousal), and high-frequency studio audio downsampling robustness.

---

## 3. IEMOCAP (Interactive Emotional Dyadic Motion Capture Database)

### Dataset Profile
- **Institution:** Speech Analysis and Interpretation Laboratory (SAIL), University of Southern California (USC)
- **Official Source:** [https://sail.usc.edu/iemocap/](https://sail.usc.edu/iemocap/)
- **License:** Custom USC SAIL Academic Research End-User License Agreement (EULA)
- **Attribution Required:** Yes
- **Citation:**
  > Busso, C., Bulut, M., Lee, C. C., Kazemzadeh, A., Mower, E., Kim, S., Chang, J. N., Lee, S., & Narayanan, S. (2008).  
  > *IEMOCAP: Interactive emotional dyadic motion capture database.*  
  > Language Resources and Evaluation, 42(4), 335–359.
- **Commercial Restrictions:** Strictly Academic / Non-commercial research. Redistribution or public re-hosting is strictly prohibited.
- **Languages:** English.
- **Number of Speakers:** 10 actors (5 male, 5 female) across 5 dyadic interaction sessions.
- **Native Audio Format:** 16-bit uncompressed WAV, 16,000 Hz, 2-channel / Mono.
- **Approximate Download Size:** ~2.5 GB (audio + time-aligned transcripts).
- **Transcripts:** Time-aligned, word-level and sentence-level dialogue transcripts.

### Acquisition Process
1. Visit the USC SAIL request portal: [https://sail.usc.edu/iemocap/release_form.php](https://sail.usc.edu/iemocap/release_form.php)
2. Submit your institutional email and sign the electronic EULA.
3. Upon receiving credentials from USC, download the session archive.
4. Extract selected `.wav` conversational turns into:
   ```text
   test_audio/original/iemocap/
   ```
5. Run `python -m tools.build_test_set` to automatically normalize and index them into `test_audio/curated/conversational/`.

### Testing Role in SAATHI-AI
Natural turn-taking, multi-speaker conversational dialogue, overlapping speech segments, spontaneous hesitation, and conversational backchannels.

---

## 4. MSP-Podcast (Multimodal Speech Processing Podcast Database)

### Dataset Profile
- **Institution:** Multimodal Speech Processing (MSP) Lab, University of Texas at Dallas
- **Official Source:** [https://ecs.utdallas.edu/research/researchlabs/msp-lab/MSP-Podcast.html](https://ecs.utdallas.edu/research/researchlabs/msp-lab/MSP-Podcast.html)
- **License:** UT Dallas MSP-Podcast Academic License Agreement
- **Attribution Required:** Yes
- **Citation:**
  > Lotfian, R., & Busso, C. (2017).  
  > *Building Natural Emotional Datasets in the Wild: MSP-Podcast.*  
  > IEEE Transactions on Affective Computing, 10(2), 271–283.
- **Commercial Restrictions:** Academic research only without a negotiated commercial agreement.
- **Languages:** English (in-the-wild conversational podcast audio from global English speakers).
- **Number of Speakers:** >1,200 unique speakers.
- **Native Audio Format:** 16-bit WAV, 16,000 Hz / 44,100 Hz.
- **Approximate Download Size:** >100 GB (full corpus v1.10+); recommended test subset is 10–30 MB.
- **Transcripts:** Automated and manually verified transcripts for spontaneous dialogue segments.

### Acquisition Process
1. Visit the UT Dallas request form: [https://ecs.utdallas.edu/research/researchlabs/msp-lab/MSP-Podcast.html](https://ecs.utdallas.edu/research/researchlabs/msp-lab/MSP-Podcast.html)
2. Complete and sign the license agreement.
3. Access the secure download repository provided by UT Dallas.
4. Place selected podcast `.wav` clips into:
   ```text
   test_audio/original/msp_podcast/
   ```
5. Run `python -m tools.build_test_set` to automatically normalize and index them.

### Testing Role in SAATHI-AI
Real-world conversational flow, podcast recording acoustics, natural speech interruptions, and diverse regional English accents.

---

## 5. IndicVoices / AI4Bharat Multilingual Speech Datasets

### Dataset Profile
- **Institution:** AI4Bharat, Indian Institute of Technology Madras (IIT Madras) & OpenSLR
- **Official Source:** [https://ai4bharat.iitm.ac.in/indicvoices/](https://ai4bharat.iitm.ac.in/indicvoices/) and [https://www.openslr.org](https://www.openslr.org)
- **License:** Creative Commons Attribution 4.0 International (CC BY 4.0) / CC BY-SA 4.0
- **Attribution Required:** Yes
- **Citation:**
  > AI4Bharat. (2024).  
  > *IndicVoices: Towards building an inclusive multilingual speech dataset for Indian languages.*  
  > arXiv preprint arXiv:2403.01926.
- **Commercial Restrictions:** Permissive (CC BY 4.0) with attribution.
- **Languages:** 22 scheduled Indian languages. Currently curated in SAATHI-AI:
  - Hindi (`hi`)
  - Marathi (`mr`)
  - Tamil (`ta`)
  - Telugu (`te`)
  - Kannada (`kn`)
  - Punjabi (`pa`)
  - Gujarati (`gu`)
- **Number of Speakers:** >22,500 native speakers covering 208 Indian districts.
- **Native Audio Format:** 16-bit WAV / FLAC, 16,000 Hz / 48,000 Hz Mono.
- **Approximate Download Size:** Entire corpus is >1.5 TB (12,000 hours); test subset is ~12 MB (19 clips).
- **Speech Types:**
  - Read speech (8%)
  - Extempore speech (76%)
  - Conversational dialogue (15%)

### Testing Role in SAATHI-AI
Indian language phonetic handling, Devanagari / Dravidian script ASR accuracy, Indian English accent evaluation, and multilingual voice activity detection.

---

## Ethical Boundaries & Data Governance

### 1. Emotion != Trauma
Emotional vocalizations (screams, crying, loud shouts, panic) represent acute affective arousal. They are **NOT** psychological trauma. Trauma is a clinical psychiatric construct defined by DSM-5/ICD-11 criteria, involving intrusive memories, avoidance behavior, negative alterations in cognition/mood, and arousal changes over extended periods.

No machine learning model should ever assert:
```json
// INVALID AND UNETHICAL:
{
  "emotion": "fear",
  "trauma": true
}
```

Instead, SAATHI-AI maintains strict capability boundaries:
```json
// VALID PIPELINE DIAGNOSTIC:
{
  "sample_id": "EMO_010",
  "category": "emotional",
  "original_label": "fear",
  "pipeline_capabilities_tested": [
    "acoustic_quality_snr",
    "voice_activity_bursts",
    "whisper_asr_transcription"
  ],
  "trauma_assertion": null
}
```

### 2. Speaker Leakage Prevention
To prevent speaker dominance and data leakage:
- Speaker IDs are tracked in `test_audio/metadata/samples.csv` (`speaker_id_if_available`).
- No single speaker represents more than 15% of the overall test suite.
- Clean and emotional samples are distributed across at least 28 unique speaker identities.
- If these benchmark files are ever referenced in future model training, samples in `test_audio/curated/` must remain in an independent, frozen test split.
