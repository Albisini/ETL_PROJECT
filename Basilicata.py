from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import json

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--window-size=1920,1080")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

bandi = []

try:
    driver.get("https://portalebandi.regione.basilicata.it/")
    # Scroll fino in fondo per caricare tutti gli avvisi
    SCROLL_PAUSE_TIME = 2
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    elementi_bandi = driver.find_elements(By.CSS_SELECTOR, "div.jet-listing-grid__item")

    for bando in elementi_bandi:
        try:
            titolo = bando.find_element(By.CSS_SELECTOR, "span.elementor-heading-title").text
            print(f"titolo: {titolo}")

            link_elem = bando.find_element(By.CSS_SELECTOR, "a.elementor-button-link")
            url = link_elem.get_attribute("href")
            print(f"url: {url}")

            data_scadenza = ""
            try:
                data_elem = bando.find_element(By.XPATH, ".//div[contains(@class,'jet-listing-dynamic-field__content') and contains(., 'Data di scadenza')]")
                data_text = data_elem.text
                data_scadenza = data_text.split(": ", 1)[1]
                print(f"data_scadenza: {data_scadenza}")
            except:
                pass

            # Apro il link "Maggiori dettagli" in una nuova scheda
            driver.execute_script("window.open(arguments[0]);", url)
            driver.switch_to.window(driver.window_handles[1])
            time.sleep(2)  # attendo caricamento pagina

            destinatari_text = ""
            try:
                destinatari_elem = driver.find_element(By.XPATH, "//span[contains(text(),'Destinatari')]/..")
                destinatari_text = destinatari_elem.text
                print(f"destinatari_text: {destinatari_text}")
            except:
                destinatari_text = "Destinatari non trovato"

            allegati = []
            try:
                attachment_links = driver.find_elements(By.CSS_SELECTOR, "a.attachment-download")
                for link in attachment_links:
                    name = link.get_attribute("data-original-name")
                    href = link.get_attribute("href")
                    if name and href:
                        allegati.append({"name": name, "link": href})
                print(f"allegati: {allegati}")
            except:
                allegati = []

            driver.close()
            driver.switch_to.window(driver.window_handles[0])

            codice_bando = "BA" + str(random.randint(100000000000, 999999999999))
            bandi.append({
                "codice": codice_bando,
                "categoria": "",
                "titolo": titolo,
                "url": url,
                "stato": "Aperto",
                "tipo_utente": destinatari_text,
                "data_chiusura": data_scadenza,
                "allegati": allegati,
                "scheda_info": {},
                "regione": "Basilicata"
            })

        except Exception as e:
            print(f"⚠️ Errore durante l'elaborazione di un bando: {e}")
            continue

finally:
    driver.quit()

# Controllo che tutti i dati siano JSON-serializzabili (debug)
for i, b in enumerate(bandi):
    for k, v in b.items():
        if not isinstance(v, (str, int, float, bool, list, dict, type(None))):
            print(f"❌ Errore nel bando #{i}, campo '{k}': tipo {type(v)}")

# Salvataggio finale
with open("bandi_basilicata.json", "w", encoding="utf-8") as f:
    json.dump(bandi, f, ensure_ascii=False, indent=2)

print(f"✅ Completato. Salvati {len(bandi)} bandi.")
