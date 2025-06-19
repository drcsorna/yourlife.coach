import requests
import time

# USDA FoodData Central API endpoint and API key
API_KEY = "39Kk8zLuBp9PeopykEEke0kd2QEie5WFVc8a1uOS"
API_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

def fetch_api_data(categories, notifications):
    initial_data = []
    
    # Define search terms for each category
    search_terms = {
        "Breakfast": ["oatmeal", "eggs", "toast", "cereal", "pancakes"],
        "Lunch": ["sandwich", "salad", "soup", "pasta", "rice"],
        "Dinner": ["chicken", "beef", "fish", "vegetables", "potato"],
        "Snack": ["apple", "banana", "nuts", "yogurt", "crackers"]
    }
    
    for category in categories:
        # Use appropriate search terms for the category
        search_queries = search_terms.get(category, search_terms["Snack"])
        category_foods = []
        
        # Try multiple search terms to get variety
        for search_query in search_queries:
            if len(category_foods) >= 10:  # Limit to 10 items per category
                break
                
            params = {
                "api_key": API_KEY,
                "query": search_query,
                "pageSize": 5,  # Smaller page size for faster response
                "sortBy": "dataType.keyword",
                "sortOrder": "asc"
            }
            
            try:
                print(f"Fetching data for {category} with query: {search_query}")
                response = requests.get(API_URL, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    foods = data.get("foods", [])
                    
                    if foods:
                        print(f"Got {len(foods)} foods for {search_query}")
                        for food in foods[:2]:  # Take only 2 items per search query
                            if len(category_foods) >= 10:
                                break
                            food_name = food.get("description", "").strip()
                            if food_name and food_name not in [item[0] for item in category_foods]:
                                category_foods.append([food_name, category])
                    else:
                        print(f"No foods found for {search_query}")
                        
                elif response.status_code == 403:
                    print(f"API key issue: {response.status_code}")
                    notifications.append(f"API authentication failed for {category}")
                    break
                else:
                    print(f"API request failed with status code: {response.status_code}")
                    
            except requests.RequestException as e:
                print(f"Request exception for {search_query}: {e}")
                continue
            except Exception as e:
                print(f"Unexpected error for {search_query}: {e}")
                continue
            
            # Small delay to respect API rate limits
            time.sleep(0.3)
        
        # Add the foods we found for this category
        if category_foods:
            initial_data.extend(category_foods)
            notifications.append(f"Successfully fetched {len(category_foods)} items for {category}")
            print(f"Successfully added {len(category_foods)} items for {category}")
        else:
            # Add placeholder items if API failed
            print(f"No API data for {category}, adding placeholders")
            placeholder_items = [
                f"Sample {category.lower()} item {i+1}" for i in range(5)
            ]
            for item in placeholder_items:
                initial_data.append([item, category])
            notifications.append(f"Added placeholder items for {category} (API unavailable)")
    
    # If we got no data at all, add some basic placeholder items
    if not initial_data:
        print("No data from API, creating basic placeholders")
        basic_items = [
            ["Oatmeal", "Breakfast"],
            ["Scrambled Eggs", "Breakfast"],
            ["Turkey Sandwich", "Lunch"],
            ["Green Salad", "Lunch"],
            ["Grilled Chicken", "Dinner"],
            ["Steamed Vegetables", "Dinner"],
            ["Apple", "Snack"],
            ["Greek Yogurt", "Snack"],
        ]
        initial_data.extend(basic_items)
        notifications.append("Created basic meal database (API unavailable)")
    
    print(f"Final data count: {len(initial_data)} items")
    return initial_data