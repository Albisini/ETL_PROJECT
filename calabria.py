import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import time
import random
options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)

base = "https://www.regione.calabria.it/bandi-e-avvisi-di-gara/page/"
bandi = []

for page in range(1, 6):
    url = base + str(page) + "/"
    print(f"📄 Carico pagina {page}: {url}")
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h3.card-title"))
        )
    except Exception as e:
        print(f"⚠️ Timeout nella pagina {page}: {e}")
        continue

    # Estrazione dei titoli e url
    cards = driver.find_elements(By.CSS_SELECTOR, "div.card-body")
    if not cards:
        print(f"⚠️ Nessuna card trovata a pagina {page}")
    for card in cards:
        try:
            link = card.find_element(By.CSS_SELECTOR, "a[href]")
            title = link.find_element(By.CSS_SELECTOR, "h3.card-title").text.strip()
            href = link.get_attribute("href")

            # Apri il link del bando
            driver.execute_script("window.open(arguments[0]);", href)
            driver.switch_to.window(driver.window_handles[1])

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "section.entry-content"))
                )

                # Estrazione delle info principali
                scheda_info = {}
                try:
                    labels = driver.find_elements(By.CSS_SELECTOR, "div.rc-text.rc-info-description")
                    for label in labels:
                        key_el = label.find_element(By.CSS_SELECTOR, "strong span")
                        val_el = label.find_elements(By.CSS_SELECTOR, "span")
                        if len(val_el) > 1:
                            key = key_el.text.strip().replace(":", "")
                            val = val_el[1].text.strip()
                            scheda_info[key] = val
                except Exception as e:
                    print("Errore nell'estrazione di scheda_info:", e)

                # Estrazione della data ultimo aggiornamento
                try:
                    data_el = driver.find_element(By.CSS_SELECTOR, "span.update-p")
                    scheda_info["Ultimo aggiornamento"] = data_el.text.strip()
                except:
                    pass

                # Estrazione degli allegati
                allegati = []
                try:
                    allegati_cards = driver.find_elements(By.CSS_SELECTOR, "div.card.card-teaser.attach")
                    for allegato in allegati_cards:
                        try:
                            name = allegato.find_element(By.CSS_SELECTOR, "span.card-title").text.strip()
                            link = allegato.find_element(By.TAG_NAME, "a").get_attribute("href")
                            allegati.append({"name": name, "link": link})
                        except:
                            continue
                except:
                    pass
                data_chiusura = scheda_info.pop("Data di Scadenza", None)
                codice_bando = "CB" + str(random.randint(100000000000, 999999999999))
                bandi.append({
                    "codice": codice_bando,
                    "categoria": "",
                    "titolo": title,
                    "url": href,
                    "stato": "Aperto",
                    "tipo_utente": "",
                    "data_chiusura": data_chiusura,
                    "allegati": allegati,
                    "scheda_info": scheda_info,
                    "regione": "Calabria"
                })

            except Exception as e:
                print(f"❌ Errore durante scraping dettagli bando: {e}")
            finally:
                # Chiudi la scheda secondaria
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

        except Exception as e:
            print(f"Errore estrazione card in pagina {page}: {e}")
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            continue
    time.sleep(1)

driver.quit()

# OUTPUT finale
print(f"\n✅ Totale bandi estratti: {len(bandi)}\n")
for b in bandi:
    print(f"🔸 {b['titolo']}\nURL: {b['url']}")
    print("📌 Scheda info:")
    for k, v in b['scheda_info'].items():
        print(f"  - {k}: {v}")
    print("📎 Allegati:")
    for a in b['allegati']:
        print(f"  - {a['name']} → {a['link']}")
    print("-" * 60)

with open("bandi_calabria.json", "w", encoding="utf-8") as f:
    json.dump(bandi, f, ensure_ascii=False, indent=2)

print(f"\n✅ Totale bandi estratti: {len(bandi)}")
print("✅ File JSON salvato: bandi_calabria.json")