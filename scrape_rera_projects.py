from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time

driver = webdriver.Chrome()
driver.get("https://rera.odisha.gov.in/projects/project-list")
driver.maximize_window()

wait = WebDriverWait(driver, 10)
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "app-project-list .card")))
time.sleep(2)

results = []

# Loop through the first 6 projects
for i in range(6):
    buttons = driver.find_elements(By.CLASS_NAME, "btn-primary")

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", buttons[i])
    time.sleep(1.5)
    driver.execute_script("arguments[0].click();", buttons[i])
    time.sleep(2)  # Wait for the detail page to load

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    project_data = {
        block.select_one('label').get_text(strip=True).replace('\xa0', ' ').lower():
            block.select_one('strong').get_text(strip=True)
        for block in soup.select('div.details-project')
        if block.select_one('label') and block.select_one('strong')
    }

    project_name = project_data.get("project name", "Not Found")
    rera_no = project_data.get("rera regd. no.", "Not Found")

    # Navigate to the "Promoter Details" tab
    promoter_tab = driver.find_element(By.XPATH, "//a[contains(text(), 'Promoter Details')]")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", promoter_tab)
    time.sleep(1)
    driver.execute_script("arguments[0].click();", promoter_tab)
    time.sleep(2)

    # Parse promoter information
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    promoter_data = {
        label.get_text(strip=True).replace('\xa0', ' ').lower():
            label.find_next_sibling('strong').get_text(strip=True)
        for label in soup.select('app-promoter-details label')
        if label.find_next_sibling('strong')
    }
    promoter_name = promoter_data.get("company name") or \
                    promoter_data.get("proprietory name") or \
                    promoter_data.get("propietory name") or "Not Found"

    promoter_address = promoter_data.get("registered office address") or \
                       promoter_data.get("current residence address") or \
                       promoter_data.get("permanent address") or "Not Found"

    gst_no = promoter_data.get("gst no.") or "Not Found"

    results.append({
        "Project Name": project_name,
        "RERA Regd. No": rera_no,
        "Promoter Name": promoter_name,
        "Promoter Address": promoter_address,
        "GST No.": gst_no
    })

    # Go back to the main project list page
    driver.back()
    time.sleep(2)

driver.quit()

df = pd.DataFrame(results)
df.to_csv("odisha_rera_projects.csv", index=False)

print("\n--- Scraped Projects ---")
print(df.to_string(index=False))
