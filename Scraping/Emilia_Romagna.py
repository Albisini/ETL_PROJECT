from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
import json

options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

# URL iniziale
base_url = "https://bandi.regione.emilia-romagna.it/search_bandi_form?SearchableText=&b_size=20&b_start=0&stato_bandi=open"
driver.get(base_url)
time.sleep(2)

risultati = []
pagina_corrente = 1

while True:
    print(f"\n Leggo la pagina {pagina_corrente}...")

    # Estrai link ai bandi
    links = driver.find_elements(By.CSS_SELECTOR, "a.state-published")
    urls = [link.get_attribute("href") for link in links]

    for url in urls:
        driver.get(url)
        time.sleep(2)

        scheda_info = {}
        allegati = []

        # Titolo
        try:
            titolo = driver.find_element(By.CSS_SELECTOR, "h1[data-element='page-name']").text.strip()
        except:
            titolo = "Titolo non trovato"

        # Descrizione
        try:
            descr_div = driver.find_element(By.CSS_SELECTOR, "div.richtext-blocks")
            scheda_info["Descrizione"] = descr_div.text.strip()
        except:
            scheda_info["Descrizione"] = "Non trovata"

        # Chi può fare domanda
        try:
            destinatari = []
            elementi = driver.find_elements(By.CSS_SELECTOR, "section ul")
            for ul in elementi:
                if any(termine in ul.text for termine in ["Enti", "Imprese", "Cittadini", "Associazioni"]):
                    destinatari = [li.text.strip() for li in ul.find_elements(By.TAG_NAME, "li") if li.text.strip()]
                    break
            scheda_info["Chi può fare domanda"] = destinatari
        except:
            scheda_info["Chi può fare domanda"] = []

        # Categoria
        try:
            categoria_header = driver.find_element(By.XPATH, "//h3[contains(text(),'Tipologia del bando')]")
            categoria_val = categoria_header.find_element(By.XPATH, "./following-sibling::span")
            categoria = categoria_val.text.strip()
        except:
            categoria = "Non trovata"

        # Allegati
        try:
            allegati_card = driver.find_elements(By.CSS_SELECTOR, "div.card-teaser.attachment")
            for card in allegati_card:
                try:
                    link_tag = card.find_element(By.CSS_SELECTOR, "a")
                    name = link_tag.text.strip()
                    link = link_tag.get_attribute("href")
                    allegati.append({"name": name, "link": link})
                except:
                    continue
        except:
            allegati = []

        try:
            scadenza = "Non trovata"
            paragrafi = driver.find_elements(By.CSS_SELECTOR, "p")

            for p in paragrafi:
                spans = p.find_elements(By.TAG_NAME, "span")
                if len(spans) >= 2:
                    if "scadenza termini partecipazione" in spans[0].text.lower():
                        scadenza = spans[1].text.strip()
                        break
        except Exception as e:
            print("Errore nella lettura della scadenza:", e)
            scadenza = "Non trovata"

        risultati.append({
            "codice":"",
            "categoria": categoria,
            "titolo": titolo,
            "link": url,
            "stato":"Aperto",
            "tipo_utente": "",
            "data_apertura": "",
            "data_scadenza": scadenza,
            "scheda_info": scheda_info,
            "allegati": allegati,
            "regione": "Emilia Romagna"
        })

    # Torna alla pagina iniziale e prova a cliccare pagina successiva
    driver.get(base_url)
    time.sleep(2)
    pagina_corrente += 1

    try:
        bottone = driver.find_element(By.CSS_SELECTOR, f'a[aria-label="Page {pagina_corrente}"]')
        ActionChains(driver).move_to_element(bottone).click().perform()
        time.sleep(2)
    except:
        print(" Nessuna pagina successiva trovata. Fine.")
        break

driver.quit()

# Salva in JSON
with open("bandi_emilia_romagna.json", "w", encoding="utf-8") as f:
    json.dump(risultati, f, ensure_ascii=False, indent=2)

print(f"\n Salvato {len(risultati)} bandi in 'bandi_emilia_romagna.json'")
