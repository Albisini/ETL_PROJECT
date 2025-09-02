from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time

BASE_URL = "https://www.bandi.regione.lombardia.it"

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 10)

dati_bandi = []

# Carico la prima pagina
driver.get(f"{BASE_URL}/servizi/servizio/catalogo?page=1")

while True:
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.results-block div.card-big")))
    bandi = driver.find_elements(By.CSS_SELECTOR, "div.results-block div.card-big")

    for bando in bandi:
        try:
            codice = bando.find_element(By.CSS_SELECTOR, "span.favourite").get_attribute("data-id")
            titolo = bando.find_element(By.CSS_SELECTOR, "h4.card-title").text
            link = bando.find_element(By.CSS_SELECTOR, "a.text-decoration-none").get_attribute("href")

            try:
                data_chiusura = bando.find_element(By.CSS_SELECTOR, "em > strong").text.strip()
            except:
                data_chiusura = "Non disponibile"

            try:
                stato = bando.find_element(By.CSS_SELECTOR, "small.badge").text.strip()
            except:
                stato = "Non disponibile"
            if stato not in ["Aperto", "In Apertura"]:
                continue
            try:
                tipo_utente = bando.find_element(By.CSS_SELECTOR, "span.categoria").text.strip()
            except:
                tipo_utente = "Non disponibile"

            print(f"Analizzo codice: {codice} - {titolo}")

            # apri dettaglio in nuova scheda
            driver.execute_script("window.open(arguments[0]);", link)
            WebDriverWait(driver, 5).until(lambda d: len(d.window_handles) > 1)
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(2)

            # estrai scheda informativa
            scheda_info = {}
            try:
                titoli = driver.find_elements(By.CSS_SELECTOR, "span.head-text.float-left")
                for titolo_el in titoli:
                    nome_sezione = titolo_el.text.strip()
                    try:
                        bottone = titolo_el.find_element(By.XPATH, "./ancestor::button")
                        driver.execute_script("arguments[0].click();", bottone)
                        time.sleep(1)
                    except Exception as click_err:
                        print(f"⚠ Errore click su {nome_sezione}: {click_err}")

                    try:
                        container_id = bottone.get_attribute("data-target")
                        container = driver.find_element(By.CSS_SELECTOR, container_id)
                        paragrafi = [p.text.strip() for p in container.find_elements(By.TAG_NAME, "p")]
                        liste = [li.text.strip() for li in container.find_elements(By.TAG_NAME, "li")]
                        contenuto = " ".join(paragrafi + liste)
                        scheda_info[nome_sezione] = contenuto
                    except Exception as estrazione_err:
                        print(f"⚠ Errore lettura contenuto {nome_sezione}: {estrazione_err}")
                        scheda_info[nome_sezione] = ""
            except Exception as e:
                print(f"⚠ Errore scheda informativa: {e}")
            # Categoria (
            try:
                categoria_el = driver.find_element(By.CSS_SELECTOR, "a[href*='/servizi/servizio/bandi/']")
                categoria = categoria_el.text.strip()
            except:
                categoria = "Non disponibile"

            # estrai allegati
            allegati_list = []
            try:
                allegati_elements = driver.find_elements(By.CSS_SELECTOR, "a.text-blue-dark[href*='/download/']")
                for a in allegati_elements:
                    nome = a.find_element(By.CSS_SELECTOR, "div.it-right-zone span.text").text.strip()
                    href = a.get_attribute("href")
                    if href.startswith("/"):
                        href = BASE_URL + href
                    allegati_list.append({"nome": nome, "link": href})
            except:
                allegati_list = []

            # estrai data apertura
            try:
                data_apertura_el = driver.find_element(By.XPATH, "//strong[contains(text(),'-')]")
                data_apertura = data_apertura_el.text.strip()
            except:
                data_apertura = "Non disponibile"

            # costruisci il dizionario completo del bando
            bando_info = {
                "codice": codice,
                "categoria": categoria,
                "titolo": titolo,
                "link": link,
                "stato": stato,
                "tipo_utente": tipo_utente,
                "data_apertura": data_apertura,
                "data_chiusura": data_chiusura,
                "allegati": allegati_list,
                "scheda_informativa": scheda_info,
                "regione": "Lombardia"
            }

            dati_bandi.append(bando_info)

            # chiudi tab e torna alla principale
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        except Exception as e:
            print(f" Errore su bando: {e}")
            continue

    # prova tila a cliccare il bottone "Pagina successiva"
    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, "a.page-link.page-up")
        if "disabled" in next_btn.get_attribute("class"):
            print("Ultima pagina raggiunta.")
            break
        next_btn.click()
        time.sleep(3)
    except Exception as e:
        print("Bottone pagina successiva non trovato o errore:", e)
        break

# salva JSON brava brava
with open("bandi_lombardia_completo.json", "w", encoding="utf-8") as f:
    json.dump(dati_bandi, f, ensure_ascii=False, indent=2)

print("File JSON salvato: bandi_lombardia_completo.json")
driver.quit()
