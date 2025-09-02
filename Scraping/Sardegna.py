import sys
import logging
from selenium.webdriver.remote.remote_connection import LOGGER
LOGGER.setLevel(logging.WARNING)
sys.path.insert(0,'/usr/lib/chromium-browser/chromedriver')
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from tqdm.notebook import tqdm
import pandas
import json
import pprint
from chromedriver_py import binary_path

chrome_options = webdriver.ChromeOptions()  # Initialize Chrome options
chrome_options.add_argument('--headless')  # Run Chrome in headless mode - In our local notebook we can remove the `--headless` option.
chrome_options.add_argument('--no-sandbox')  # Disable Chrome’s default sandboxing behavior
chrome_options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems
chrome_options.add_argument("window-size=1900,800")  # Set the window size for the browser
chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")  # Set a custom user agent

service = Service(executable_path=binary_path)  # Create a Service object with the path to the ChromeDriver executable
wd = webdriver.Chrome(service=service, options=chrome_options)  # Initialize the WebDriver with the specified service and options

wd.get("https://www.regione.sardegna.it/")

wd.save_screenshot('screenshot.png')


import matplotlib.pyplot as plt
import matplotlib.image as mpimg

img = mpimg.imread('/content/screenshot.png')
plt.figure(figsize=(20, 10))
imgplot = plt.imshow(img)
plt.xticks([])
plt.yticks([])
plt.show()

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pandas as pd

# ==== AVVIO ====

# 1. Attendi che il main menu sia visibile
main_menu = WebDriverWait(wd, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "div.main-menu"))
)

# 2. Trova il blocco del menu di sinistra
left_menu = main_menu.find_element(By.CSS_SELECTOR, "div.left-menu.navbar-light")

# 3. Trova l'elenco delle voci del menu
ul_navbar = left_menu.find_element(By.CSS_SELECTOR, "ul.navbar-nav.d-md-block.d-none.navbar-nav")

# 4. Clic su "Atti, Bandi e Archivi"
link = ul_navbar.find_element(By.XPATH, ".//a[normalize-space(text())='Atti, Bandi e Archivi']")
link.click()
print("✅ Cliccato su 'Atti, Bandi e Archivi'")

# 5. Clic su "Bandi"
bandi_link = WebDriverWait(wd, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'link-service-item') and contains(@class, 'close-menu-link') and contains(text(), 'Bandi')]"))
)
bandi_link.click()
print("✅ Cliccato su 'Bandi'")

# 6. Attesa caricamento card
WebDriverWait(wd, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "div.card-wrapper"))
)
print("✅ Pagina 'Bandi' caricata con card visibili")

# 7. Screenshot iniziale (opzionale)
time.sleep(2)
screenshot_path = "screenshot_bandi.png"
wd.save_screenshot(screenshot_path)
print(f"📸 Screenshot salvato in: {screenshot_path}")

img = mpimg.imread(screenshot_path)
plt.imshow(img)
plt.axis('off')
plt.title("Pagina Bandi")
plt.show()


# ==== FUNZIONE PER ESTRARRE UN BLOCCO DI PAGINE ====

def estrai_blocco(wd, start_page, end_page, batch_index):
    bandi = []
    current_page = 1

    # Vai alla pagina di partenza (cliccando "Next" fino a start_page)
    while current_page < start_page:
        try:
            next_button = WebDriverWait(wd, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@class='page-link' and @aria-label='Next']"))
            )
            old_card = wd.find_element(By.CSS_SELECTOR, "div.card-bg.card")
            wd.execute_script("arguments[0].scrollIntoView({block: 'end'});", next_button)
            time.sleep(0.5)
            wd.execute_script("arguments[0].click();", next_button)
            WebDriverWait(wd, 10).until(EC.staleness_of(old_card))
            WebDriverWait(wd, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.card-bg.card"))
            )
            current_page += 1
        except Exception as e:
            print(f"⛔ Errore navigando alla pagina {start_page}: {e}")
            return

    # Estrai da start_page a end_page
    for page_num in range(start_page, end_page + 1):
        print(f"📄 Pagina {page_num}")

        WebDriverWait(wd, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.card-bg.card"))
        )

        try:
            old_card = wd.find_element(By.CSS_SELECTOR, "div.card-bg.card")
        except:
            old_card = None

        cards = wd.find_elements(By.CSS_SELECTOR, "div.card-bg.card")

        for card in cards:
            try:
                titolo_elem = card.find_element(By.CSS_SELECTOR, "h5.card-title a")
                titolo = titolo_elem.text.strip()
                link = titolo_elem.get_attribute("href")

                stato = card.find_element(
                    By.XPATH,
                    ".//div[div[@class='style_data_title__OAsdz' and text()='Stato']]//div[contains(@class,'badge-ras')]"
                ).text.strip()

                if stato == "APERTO":
                    bandi.append({"titolo": titolo, "link": link, "stato": stato})
            except Exception as e:
                print(f"⚠️ Errore card: {e}")

        # Clic su "Next" se non è l'ultima pagina del blocco
        if page_num < end_page:
            try:
                next_button = WebDriverWait(wd, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@class='page-link' and @aria-label='Next']"))
                )
                wd.execute_script("arguments[0].scrollIntoView({block: 'end'});", next_button)
                time.sleep(0.5)
                wd.execute_script("arguments[0].click();", next_button)
                print("➡️ Next cliccato")
                WebDriverWait(wd, 10).until(EC.staleness_of(old_card))
                WebDriverWait(wd, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.card-bg.card"))
                )
            except Exception as e:
                print(f"⛔ Errore cliccando Next a pagina {page_num}: {e}")
                break

    # Salva blocco su CSV
    df = pd.DataFrame(bandi)
    filename = f"ds_bandi_sardegna_blocco_{batch_index}.csv"
    df.to_csv(filename, encoding='utf-8', index=False)
    print(f"✅ Salvato: {filename} | Totale bandi aperti: {len(bandi)}")


# ==== ESEGUI PIÙ BLOCCHI ====

total_pages = 506
blocchi_da = 100
batch_num = 1

while (batch_num - 1) * blocchi_da < total_pages:
    start_page = (batch_num - 1) * blocchi_da + 1
    end_page = min(batch_num * blocchi_da, total_pages)

    estrai_blocco(wd, start_page, end_page, batch_num)
    batch_num += 1
