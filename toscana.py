from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
import json

# Inizializza il driver
driver = webdriver.Chrome()

base_url = "https://www.regione.toscana.it"
start_page = 1
bandi = []
codice_counter = 1

while True:
    url = f"{base_url}/bandi-aperti?delta=20&start={start_page}"
    driver.get(url)
    time.sleep(3)

    print(f" Scansione pagina {start_page}...")

    card_elements = driver.find_elements(By.CSS_SELECTOR, "div.rtds-card__content")
    if not card_elements:
        print("Nessun bando trovato, uscita.")
        break

    for card in card_elements:
        try:
            titolo_el = card.find_element(By.CSS_SELECTOR, "h3.rtds-card__title a")
            titolo = titolo_el.text.strip()
            link = titolo_el.get_attribute("href")

            stato = card.find_element(By.CSS_SELECTOR, "span.rtds-chip--status").text.strip()
            if "Aperto" not in stato:
                continue  # Salta bandi non aperti

            scadenza = card.find_element(By.CSS_SELECTOR, "small.rtds-card__date time").get_attribute("datetime")

            # Vai nella pagina del bando per info aggiuntive
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[1])
            driver.get(link)
            time.sleep(2)

            corpo_bando = driver.find_element(By.CSS_SELECTOR, "div.rtds-article-body").text.strip()

            scheda_info = {
                "descrizione": corpo_bando
            }

            # Estrai link degli allegati (se presenti)
            allegati = []
            link_elements = driver.find_elements(By.XPATH, "//a[contains(@href, 'Contenuto.xml')]")
            for el in link_elements:
                href = el.get_attribute("href")
                nome = el.text.strip()
                if href and nome:
                    allegati.append({
                        "name": nome,
                        "link": href
                    })

            # Chiudi la scheda e torna alla pagina precedente
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

            # Genera codice bando
            codice_bando = f"TO{codice_counter:011d}"
            codice_counter += 1

            bando = {
                "codice": codice_bando,
                "categoria": "",
                "titolo": titolo,
                "url": link,
                "tipo_utente": "",
                "stato": stato,
                "scadenza": scadenza,
                "scheda_info": scheda_info,
                "allegati": allegati,
                "regione": "Toscana"
            }

            bandi.append(bando)

        except Exception as e:
            print(f"Errore: {e}")
            continue

    # Controlla se esiste una pagina successiva
    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, "a[title='Pagina Seguente']")
        if "disabled" in next_btn.get_attribute("class"):
            break
    except NoSuchElementException:
        break

    start_page += 1

driver.quit()

# Salva tutto in JSON
with open("bandi_toscana.json", "w", encoding="utf-8") as f:
    json.dump(bandi, f, indent=2, ensure_ascii=False)

print(" Estrazione completata. File salvato: bandi_toscana.json")
