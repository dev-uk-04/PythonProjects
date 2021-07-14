from selenium import webdriver
import time

chrome_driver_path = "chromedriver.exe"
driver = webdriver.Chrome(executable_path=chrome_driver_path)
driver.get("http://orteil.dashnet.org/experiments/cookie/")

cookie_position = driver.find_element_by_css_selector("#cookie")
store = driver.find_elements_by_css_selector("#store b")
del store[-1]
store_dict = {items.text.split("-")[0].strip(): int(items.text.split("-")[1].replace(",", "").strip()) for items in store}
items_list = [key for key in store_dict.keys()]
# print(store_dict)
# print(items_list)

timeout = time.time() + 5
five_min = time.time() + 60*5  # 5 minutes

while True:
    cookie_position.click()
    # Every 5 seconds:
    if time.time() > timeout:
        # Fetch available money for spending
        money = int(driver.find_element_by_id("money").text)
        print(f"Money available for spending is {money}")
        # Fetch not available items
        na_items = driver.find_elements_by_class_name("grayed b")
        na_upgrades = [item.text.split("-")[0].strip() for item in na_items if item.text.split("-")[0].strip() != '']
        # Sort the available items
        available_upgrades = list(set(items_list) - set(na_upgrades))
        affordable_items = {store_dict[item]: item for item in available_upgrades}
        max_price = max(list(affordable_items.keys()))

        # Compare expensive item price with available money
        if money >= int(max_price):
            expensive_item = affordable_items[max_price]
            driver.find_element_by_id(f"buy{expensive_item}").click()
            print(f"Bought {expensive_item}")

        cookies_per_sec = driver.find_element_by_id("cps")
        print(f"Cookies per second : {cookies_per_sec.text}")

        timeout = time.time() + 5
