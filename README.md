# UMD Dining Hall Web Scraper

## Overview
This project is a **FastAPI-based web scraper** designed to collect meal data from the University of Maryland (UMD) dining halls. It scrapes meal options, nutritional information, and dietary restrictions, then stores the data in **MongoDB**. The scraped data is exposed via a RESTful API, which can be consumed by a **Swift app** (or any other frontend) to display meal information.

---

## Features

1. **Meal Data Scraping**:
   - Scrapes meal data from UMD dining hall websites.
   - Extracts meal options, nutritional information, and dietary restrictions.
   - Supports multiple dining halls, including **South Campus**, **Yahentamitsi Dining Hall**, and **251 North**.

2. **Nutritional Information**:
   - Calculates nutritional facts such as calories, serving size, and nutrient information.
   - Uses **BeautifulSoup** to parse HTML and extract relevant data.

3. **Dietary Restrictions**:
   - Identifies dietary restrictions (e.g., vegetarian, gluten-free) for each meal.
   - Displays restrictions alongside meal options.

4. **FastAPI Backend**:
   - Exposes RESTful API endpoints for fetching and storing meal data.
   - Supports concurrent scraping using **ThreadPoolExecutor** for faster data retrieval.
   - Stores scraped data in **MongoDB** for persistence.

5. **MongoDB Integration**:
   - Stores meal data in a structured format for easy retrieval.
   - Supports querying by date, dining hall, and meal type (e.g., breakfast, lunch, dinner).

6. **Swift App Integration**:
   - The API can be consumed by a **Swift app** to display meal options, nutritional facts, and dietary restrictions.
   - Provides a clean and efficient way to fetch and display dining hall data.

---

## Requirements

To run this application, you need the following Python libraries and tools installed:

### **Python Libraries**:
- `fastapi` – For building the backend API.
- `uvicorn` – For running the FastAPI server.
- `requests` – For making HTTP requests to scrape data.
- `beautifulsoup4` – For parsing HTML and extracting meal data.
- `pymongo` – For interacting with MongoDB.
- `python-dotenv` – For managing environment variables (optional).

### **MongoDB**:
- A running instance of **MongoDB** (local or cloud-based, e.g., MongoDB Atlas).

### **Installing Dependencies**:
You can install the required Python libraries using `pip`:
```bash
pip install fastapi uvicorn requests beautifulsoup4 pymongo python-dotenv
