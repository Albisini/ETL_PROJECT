from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import json
import time
import random

# Configurazione Chrome headless
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

base_url = "https://www.regione.sicilia.it/istituzioni/servizi-informativi/bandi"
params = "?f%5B0%5D=category%3A20&f%5B1%5D=category%3A21&f%5B2%5D=category%3A22"
page = 0
bandi = []

while True:
    url = f"{base_url}{params}&page={page}"
    driver.get(url)
    time.sleep(3)

    cards = driver.find_elements(By.CSS_SELECTOR, "div.card-body")
    if not cards:
        print(f"Nessun bando trovato alla pagina {page}. Fine della scansione.")
        break

    print(f"Pagina {page + 1}: trovati {len(cards)} bandi")

    # Prima prendo solo i dati base da tutti i bandi in pagina
    base_data_list = []
    for card in cards:
        try:
            scadenza_el = card.find_element(By.CSS_SELECTOR, "div.res-card-competition-announcement__deadline p.date")
            scadenza = scadenza_el.text.strip()

            titolo_el = card.find_element(By.CSS_SELECTOR, "h5.card-title a")
            titolo = titolo_el.text.strip()

            href = titolo_el.get_attribute("href")
            full_link = "https://www.regione.sicilia.it" + href if href.startswith("/") else href

            codice_bando = "SI" + str(random.randint(100000000000, 999999999999))

            base_data_list.append({
                "codice": codice_bando,
                "titolo": titolo,
                "scadenza": scadenza,
                "url": full_link
            })
        except NoSuchElementException:
            continue

    # Ora visito ogni link per estrarre i dettagli
    for bando_base in base_data_list:
        try:
            driver.get(bando_base["url"])
            time.sleep(2)

            try:
                descrizione_el = driver.find_element(By.CSS_SELECTOR, "#announcement-description .field__item")
                descrizione = descrizione_el.text.strip()
            except NoSuchElementException:
                descrizione = ""

            allegati = []
            try:
                allegati_cards = driver.find_elements(By.CSS_SELECTOR, "#attached-documents .media-document")
                for item in allegati_cards:
                    try:
                        name = item.find_element(By.CSS_SELECTOR, "h5.card-title").text.strip()
                        link = item.find_element(By.CSS_SELECTOR, "a.read-more").get_attribute("href")
                        if link.startswith("/"):
                            link = "https://www.regione.sicilia.it" + link
                        allegati.append({"name": name, "link": link})
                    except NoSuchElementException:
                        continue
            except NoSuchElementException:
                allegati = []

            bando = {
                "codice": bando_base["codice"],
                "categoria": "Imprese",
                "titolo": bando_base["titolo"],
                "url": bando_base["url"],
                "stato": "Aperto",
                "tipo_utente": "",
                "data_chiusura": bando_base["scadenza"],
                "scheda_info": descrizione,
                "allegati": allegati,
                "regione": "Sicilia"
            }

            bandi.append(bando)

        except Exception as e:
            print(f"Errore nell'estrazione di un bando: {e}")
            continue

    page += 1

driver.quit()

# Salvataggio su JSON
with open("bandi_sicilia.json", "w", encoding="utf-8") as f:
    json.dump(bandi, f, indent=2, ensure_ascii=False)

print(f"Estrazione completata: trovati {len(bandi)} bandi. File salvato: bandi_sicilia.json")
