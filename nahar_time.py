import requests
import csv
import os.path


class NaharTime:
    def __init__(self, favourite_food_ids: list, username: str, password: str):
        self.favourite_food_ids = favourite_food_ids
        api_url = "https://api.nahartime.com/v1/"
        # get token
        get_token_url = api_url + "token/createToken"
        user_pass_form = {"deviceType": "webApp", "username": username, "password": password}
        get_token_response = requests.post(url=get_token_url, json=user_pass_form).json()
        token = get_token_response.get("token")
        self.headers = {"Authorization": f"Bearer {token}"}
        # get credit
        credit_url = api_url + "user/userCredit"
        credit_response = requests.get(url=credit_url, headers=self.headers).json()
        self.credit = credit_response.get("credit")
        # get days
        get_days_url = api_url + "date/get?xDayAfter=7"
        get_days_response = requests.get(url=get_days_url, headers=self.headers).json()
        self.day_ids = [item.get("id") for item in get_days_response
                        if not item.get("isHoliday") and "پنجشنبه" not in item.get("persianDate")]
        self.chosen_foods = dict()
        self.get_food_day_url = api_url + "company/menu?dayId="
        self.submit_foods_url = api_url + "invoice/submit"
        self.food_history_url = api_url + "user/GetUserInvoicesMonth?month="
        self.file_name = "foods.csv"
        self.food_ids = list()
        if os.path.isfile(self.file_name):
            with open(self.file_name, "r", encoding="UTF8") as file:
                reader = csv.reader(file)
                for row in reader:
                    self.food_ids.append(row[0])
        else:
            with open(self.file_name, "w", encoding="UTF8") as file:
                writer = csv.writer(file)
                writer.writerow(["id", "name", "price", "restaurant", "image"])

    def update_food_list(self):
        new_foods = list()
        for ID in self.day_ids:
            get_food_day_url = self.get_food_day_url + str(ID)
            get_food_day_response = requests.get(url=get_food_day_url, headers=self.headers).json()
            for category in get_food_day_response:
                for food in category.get("foodItemViewModels"):
                    if food.get("foodItemId") not in self.food_ids:
                        self.food_ids.append(food.get("foodItemId"))
                        new_foods.append(
                            [food.get("foodItemId"),
                             food.get("foodItemName"),
                             food.get("foodItemDiscountedPrice"),
                             food.get("restaurantName"),
                             food.get("foodItemImage")]
                        )
        with open(self.file_name, "w", encoding="UTF8") as file:
            writer = csv.writer(file)
            for new_food in new_foods:
                writer.writerow(new_food)

    def get_history(self, month_num: int, year: int):
        # needs attention
        food_names = list()
        food_restaurants = list()
        for i in range(6):
            if month_num - i > 0:
                food_history_url = self.food_history_url + str(month_num - i) + "&year=" + str(year)
                days = requests.get(url=food_history_url, headers=self.headers).json()
                for day in days:
                    for item in day.get("foodItems"):
                        food_names.append(item.get("foodItemName"))
                        food_restaurants.append(item.get("restaurantName"))
        food_ids_counter = dict()
        for food_id in food_names:
            food_ids_counter[food_id] = food_ids_counter[food_id] + 1 if food_id in food_ids_counter else 1
        popular_foods = sorted(food_ids_counter, key=food_ids_counter.get, reverse=True)
        print(food_ids_counter)
        print(popular_foods)

    def get_foods(self):
        for ID in self.day_ids:
            get_food_day_url = self.get_food_day_url + str(ID)
            get_food_day_response = requests.get(url=get_food_day_url, headers=self.headers).json()
            for category in get_food_day_response:
                food_day_price = list()
                food_day_id = list()
                for food in category.get("foodItemViewModels"):
                    if food.get("hasFoodStock") and food.get("foodItemId") in self.favourite_food_ids:
                        food_day_id.append(food.get("foodItemId"))
                        food_day_price.append(food.get("foodItemDiscountedPrice"))
                if (len(food_day_price) > 0) and (self.credit - min(food_day_price) > 0):
                    self.credit -= min(food_day_price)
                    self.chosen_foods[ID] = food_day_id[food_day_price.index(min(food_day_price))]

    def choose_foods(self):
        for day, food in self.chosen_foods.items():
            food_form = {"forSubmit": True,
                         "dayId": day,
                         "companyAddressId": 10160,
                         "companyAddressFloorId": None,
                         "foodItemIdQuantityList": [{"foodItemId": str(food), "quantity": 1}]}
            response = requests.post(url=self.submit_foods_url, headers=self.headers, json=food_form).json()
            print(response)


nahar_time = NaharTime(favourite_food_ids=[17571, 18400, 17576, 17401, 17782], username="09113485808",
                       password="123456")
nahar_time.get_foods()
nahar_time.choose_foods()
nahar_time.update_food_list()
# nahar_time.get_history(month_num=4, year=1401)
