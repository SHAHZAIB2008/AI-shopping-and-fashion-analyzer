# 👗 AI Fashion Analyzer & Shopping Assistant

Upload → Analyze → Ask → Shop | Get personalized fashion recommendations with real product images from top Pakistani brands.

## 🚀 Features

* 📷 **Image Analysis** – Upload a fashion image and detect clothing items.
* 💬 **Ask Questions** – Ask for outfit recommendations (e.g., *“Find me a black kurti”*).
* 🛍️ **Live Product Search** – Fetch latest products from Pakistani brands (e.g., Khaadi, Nishat Linen).
* 🖼️ **Product Display** – Shows images, brand, price, and direct shopping link.
* 🤖 **AI Assistant** – Natural language answers + product suggestions.

---

## 🏗️ Project Structure

```
image_anlysis/
│── backend/        # FastAPI backend
│   ├── main.py     # API endpoints
│   ├── scraper.py  # Web scraping logic
│   └── ...
│
│── frontend/       # Streamlit frontend
│   ├── app.py      # UI code
│   └── ...
│
│── requirements.txt
│── README.md
```

---

## ⚙️ Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/ai-fashion-analyzer.git
cd ai-fashion-analyzer
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # (Linux/Mac)
venv\Scripts\activate      # (Windows)
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the App

### Start Backend (FastAPI)

```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Check API docs at 👉 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Start Frontend (Streamlit)

```bash
cd ../frontend
streamlit run app.py
```

Access app at 👉 [http://localhost:8501](http://localhost:8501)

---

## 🛍️ Example Workflow

1. Upload a fashion image (kurti, dress, etc.).
2. See **AI Analysis** of the outfit.
3. Ask a question like *“Give me a party wear kurti from Nishat Linen”*.
4. Get:

   * AI recommendations
   * **Real product images + prices + buy links**

---

## 📦 Dependencies

* [FastAPI](https://fastapi.tiangolo.com/) – Backend API
* [Streamlit](https://streamlit.io/) – Frontend UI
* [Requests](https://pypi.org/project/requests/) – API & scraping
* [BeautifulSoup4](https://pypi.org/project/beautifulsoup4/) – Scraping fashion brand websites
* \[Ollama / LLM Integration] – For AI responses


