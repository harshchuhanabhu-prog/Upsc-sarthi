# UPSC Sarthi — AI-Powered Bilingual UPSC Preparation Platform

## क्या है यह?

UPSC Sarthi एक संपूर्ण द्विभाषी (हिंदी + अंग्रेज़ी) UPSC तैयारी प्लेटफ़ॉर्म है जिसमें 10+ AI टूल्स शामिल हैं:

- **Answer Evaluator** — 6-चरण AI मूल्यांकन एनिमेशन, उत्तर पुस्तिका पर मार्कअप, अनुभागीय प्रतिक्रिया
- **Essay Evaluator** — 6 मानदंडों पर निबंध मूल्यांकन
- **MCQ Practice** — कथन-आधारित प्रश्न, Prelims/Mains tabs, व्याख्या
- **Daily Answer Writing** — रोज़ नया प्रश्न
- **PYQ (2011-2026)** — Prelims + Mains + Hindi Literature Optional
- **AI Mentor** — चैट इंटरफ़ेस
- **Current Affairs** — दैनिक स्वतः-अद्यतन (GitHub Actions से)
- **Case Study Generator & Finder**
- **Full Paper Test Series**
- **Leaderboard & Progress Tracker**

## फ़ाइलें

```
upsc-sarthi/
├── UPSC_Sarthi.html          ← मुख्य ऐप (ब्राउज़र में खोलें)
├── update_news.py            ← दैनिक करंट अफ़ेयर्स अपडेटर स्क्रिप्ट
├── requirements.txt           ← Python डिपेंडेंसीज़
├── data/
│   └── articles.json          ← अपडेटेड लेख (स्क्रिप्ट द्वारा जनरेटेड)
└── .github/
    └── workflows/
        └── daily-news.yml     ← GitHub Actions (रोज़ 6 AM IST)
```

## सेटअप कैसे करें

### 1. ऐप चलाना (तुरंत)
- `UPSC_Sarthi.html` को ब्राउज़र में खोलें
- सब कुछ चलेगा — करंट अफ़ेयर्स में इनलाइन डेटा दिखेगा

### 2. दैनिक ऑटो-अपडेट सेट करना (GitHub Actions)

1. GitHub पर एक नया रिपॉज़िटरी बनाएँ
2. इस फ़ोल्डर की सभी फ़ाइलें अपलोड करें:
   ```bash
   git init
   git add .
   git commit -m "UPSC Sarthi initial setup"
   git branch -M main
   git remote add origin https://github.com/yourusername/upsc-sarthi.git
   git push -u origin main
   ```
3. GitHub रिपॉज़िटरी में Settings → Actions → General में जाएँ
4. "Workflow permissions" को "Read and write permissions" में बदलें
5. बस! हर दिन सुबह 6:00 AM IST पर GitHub Actions चलेगा, नए लेख खींचेगा, और `data/articles.json` को अपडेट कर देगा

### 3. मैन्युअल रूप से अपडेट चलाना

```bash
pip install feedparser
python update_news.py
```

### 4. वेब सर्वर से चलाना (ऑटो-अपडेट के लिए ज़रूरी)

HTML को सीधे खोलने पर `fetch()` ब्लॉक हो जाता है (file:// प्रोटोकॉल)। ऑटो-अपडेट के लिए वेब सर्वर चाहिए:

```bash
# Python से
python -m http.server 8000

# फिर ब्राउज़र में खोलें
# http://localhost:8000/UPSC_Sarthi.html
```

या GitHub Pages से होस्ट करें — तो दुनिया भर से एक्सेस होगा।

## करंट अफ़ेयर्स कैसे अपडेट होते हैं?

1. `update_news.py` रोज़ चलता है (GitHub Actions द्वारा)
2. यह PIB, The Hindu, Indian Express, DownToEarth, ISRO के RSS फ़ीड्स खींचता है
3. UPSC-संबंधित कीवर्ड्स से फ़िल्टर करता है
4. विषय-वार वर्गीकृत करता है (Polity, Economy, IR, Environment, etc.)
5. महत्व स्तर तय करता है (High/Medium)
6. GS पेपर और सिलेबस मैपिंग जोड़ता है
7. हिंदी सारांश जनरेट करता है
8. विस्तृत विश्लेषण (संदर्भ + प्रमुख बिंदु) बनाता है
9. `data/articles.json` में सेव करता है और ऑटो-कमिट करता है

## RSS स्रोत

- PIB (Press Information Bureau)
- The Hindu — National + Economy
- Indian Express
- DownToEarth (Environment)
- ISRO

## भविष्य में सुधार

- [ ] Sarvam AI / Bhashini API से बेहतर हिंदी अनुवाद
- [ ] अधिक RSS स्रोत जोड़ना
- [ ] AI-आधारित लेख सारांश जनरेशन
- [ ] UPSC के ट्रेंड के अनुसार स्वचालित प्रश्न जनरेशन
