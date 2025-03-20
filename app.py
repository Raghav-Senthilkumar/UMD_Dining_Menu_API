from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import json
from fastapi.responses import JSONResponse

# Initialize FastAPI app
app = FastAPI()

# Local MongoDB connection
client = MongoClient("mongodb://localhost:27017/")  # Connect to local MongoDB
db = client['meal_database']  # Use or create a database named 'meal_database'
collection = db['meal_collection']  # Use or create a collection named 'meal_collection'

# Get the current date
current_date = datetime.now()

# Get the next six days
next_six_days = [(current_date + timedelta(days=i)).strftime('%-m/%-d/%Y') for i in range(7)]

# Define a function to extract meal data from a given URL
def extract_meal_data(session, url):
    response = session.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    data = {
        'breakfast': [],
        'lunch': [],
        'dinner': []
    }

    panes = {
        'pane-1': 'breakfast',
        'pane-2': 'lunch',
        'pane-3': 'dinner'
    }

    present_panes = {}
    for pane_id in panes.keys():
        if soup.find(id=pane_id):
            present_panes[pane_id] = panes[pane_id]

    if len(present_panes) == 2:
        if 'pane-1' in present_panes and 'pane-2' in present_panes:
            present_panes = {
                'pane-1': 'brunch',
                'pane-2': 'dinner'
            }

    for pane_id, meal_name in present_panes.items():
        pane_div = soup.find(id=pane_id)
        if pane_div:
            cards = pane_div.find_all(class_='card')
            for card in cards:
                card_title = card.find(class_='card-title')
                card_title_text = card_title.get_text(strip=True) if card_title else 'Not found'

                card_text = card.find(class_='card-text')
                menu_items_list = []
                if card_text:
                    menu_items = card_text.find_all(class_='row menu-item-row')
                    for item in menu_items:
                        menu_name = item.find(class_='menu-item-name')
                        food = menu_name.get_text(strip=True) if menu_name else 'Not found'

                        nutri_icons = item.find_all(class_='nutri-icon')
                        restrictions = [icon.get('title', 'No title') for icon in nutri_icons]

                        menu_items_list.append({
                            'food': food,
                            'restrictions': restrictions
                        })

                data[meal_name].append({
                    'card_title': card_title_text,
                    'menu_items': menu_items_list
                })
        else:
            print(f"Element with id '{pane_id}' not found.")

    return data

# Define a function to extract specific nutrition facts from a meal URL
def extract_restrictions(session, meal_url):
    response = session.get(meal_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    meal_data = {
        'nutrient_information': {},
        'serving_size': 'Not found',
        'calories_per_serving': 'Not found'
    }

    cards = soup.find_all(class_='nutfactstopnutrient')
    for card in cards:
        if card:
            b_tag = card.find('b')
            if b_tag:
                nutrient_name = b_tag.text.strip()
                nutrient_value = card.text.replace(nutrient_name, '').strip()
                if nutrient_value:
                    meal_data['nutrient_information'][nutrient_name] = nutrient_value

    cards = soup.find_all(class_='nutfactsservsize')
    if len(cards) > 1:
        second_card = cards[1]
        meal_data['serving_size'] = second_card.text.strip()

    try:
        td_element = soup.find('td')
        if td_element:
            paragraphs = td_element.find_all('p')
            if len(paragraphs) > 1:
                meal_data['calories_per_serving'] = paragraphs[1].text.strip()
    except Exception as e:
        print(f"An error occurred while extracting calories: {e}")

    return meal_data

# Define the base URL and location numbers with their corresponding names
base_url = 'https://nutrition.umd.edu/?locationNum={location_num}&dtdate={date}'
location_info = {
    16: "South Campus",
    19: "Yahentamitsi Dining Hall",
    51: "251 North"
}

# Initialize a dictionary to hold data for all dates and locations
all_data = {}

def fetch_data_for_date_and_location(session, date, location_num, location_name):
    location_url = base_url.format(location_num=location_num, date=date)
    print(f"Fetching data for {location_name} (location number {location_num}) on {date} from {location_url}...")

    location_data = extract_meal_data(session, location_url)

    all_meals = []
    response = session.get(location_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    for pane_id in ['pane-1', 'pane-2', 'pane-3']:
        pane_div = soup.find(id=pane_id)
        if pane_div:
            menu_items = pane_div.find_all('a', class_='menu-item-name')
            all_meals.extend([(item.text.strip(), item['href']) for item in menu_items if item.has_attr('href')])

    for meal_name, href in all_meals:
        meal_url = f'http://nutrition.umd.edu/{href}'
        meal_data = extract_restrictions(session, meal_url)

        for meal_type in location_data.values():
            for meal_entry in meal_type:
                for menu_item in meal_entry.get('menu_items', []):
                    if menu_item['food'] == meal_name:
                        menu_item.update(meal_data)

    return date, location_name, location_data

# FastAPI endpoint to fetch and store meal data
@app.get("/fetch-meal-data")
async def fetch_meal_data():
    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_data = {
                executor.submit(fetch_data_for_date_and_location, session, date, location_num, location_name): (date, location_name)
                for date in next_six_days
                for location_num, location_name in location_info.items()
            }
            for future in future_to_data:
                date, location_name, location_data = future.result()
                if date not in all_data:
                    all_data[date] = {}
                all_data[date][location_name] = location_data

    # Convert the dictionary to JSON
    json_data = json.dumps(all_data, indent=4)

    # Insert the JSON data into MongoDB
    try:
        result = collection.insert_one({"meal_data": json_data})
        print(f"Inserted document with id: {result.inserted_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to insert data into MongoDB: {e}")

    return JSONResponse(content={"message": "Meal data fetched and stored successfully!", "data": json_data})

# FastAPI endpoint to retrieve meal data from MongoDB
@app.get("/get-meal-data")
async def get_meal_data():
    try:
        # Retrieve the latest document from MongoDB
        latest_document = collection.find_one(sort=[("_id", -1)])
        if latest_document:
            return JSONResponse(content={"data": latest_document["meal_data"]})
        else:
            raise HTTPException(status_code=404, detail="No meal data found in MongoDB.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve data from MongoDB: {e}")

# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)