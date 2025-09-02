import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

URL = "https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza?t=Bandi&ente=altri"

driver = webdriver.Chrome()
driver.get(URL)
wait = WebDriverWait(driver, 30)

def attendi_tabella():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody")))
    time.sleep(1)
    righe = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
    while len(righe) <= 1:
        time.sleep(1)
        righe = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
    return righe

def scroll_lento():
    for i in range(0, 2000, 300):
        driver.execute_script(f"window.scrollTo(0, {i});")
        time.sleep(0.5)

def estrai_info_dettaglio(driver):
    info = {}
    try:
        sezione = driver.find_element(By.CSS_SELECTOR, ".bando-dettaglio, .scheda-info, body")
    except:
        sezione = driver.find_element(By.TAG_NAME, "body")

    strong_elements = sezione.find_elements(By.TAG_NAME, "strong")
    for strong in strong_elements:
        try:
            chiave = strong.text.strip().replace(":", "")
            parent = strong.find_element(By.XPATH, "..")
            divs = parent.find_elements(By.XPATH, "following-sibling::div[contains(@class, 'col-sm-8')]")
            if divs:
                valore = divs[0].text.strip()
                info[chiave] = valore
        except Exception:
            continue
    return info

def estrai_allegati(driver):
    allegati = []
    try:
        sezioni = driver.find_elements(By.CSS_SELECTOR, "button.accordion-button")
        doc_section = None

        for btn in sezioni:
            if "documentazione" in btn.text.lower():
                print("Trovato bottone Documentazione:", btn.text)
                if btn.get_attribute("aria-expanded") == "false":
                    btn.click()
                    time.sleep(1)
                aria_controls = btn.get_attribute("data-bs-target") or btn.get_attribute("aria-controls")
                if aria_controls:
                    aria_controls = aria_controls.replace("#", "")
                    doc_section = driver.find_element(By.ID, aria_controls)
                break

        if not doc_section:
            print("Non trovata sezione Documentazione specifica, cerco per keyword nel testo...")
            divs = driver.find_elements(By.CSS_SELECTOR, "div")
            for d in divs:
                if "documentazione" in d.text.lower():
                    doc_section = d
                    break

        if doc_section:
            print("Sezione Documentazione trovata")
            allegati_links = doc_section.find_elements(By.CSS_SELECTOR, "a.Attach_label")

            for link_el in allegati_links:
                try:
                    name_el = link_el.find_element(By.XPATH, "preceding-sibling::strong[1]")  # strong prima del link
                    name = name_el.text.strip()
                except:
                    try:
                        name_el = link_el.find_element(By.XPATH, "preceding::strong[1]")
                        name = name_el.text.strip()
                    except:
                        name = link_el.text.strip()

                link = link_el.get_attribute("href")
                if link:
                    print(f"Allegato trovato: {name} -> {link}")
                    allegati.append({"name": name, "link": link})
        else:
            print("Nessuna sezione Documentazione trovata")
    except Exception as e:
        print("Errore durante estrazione allegati:", e)
    return allegati

bandi_data = []
indice = 1

righe = attendi_tabella()

while indice < len(righe):
    try:
        righe = attendi_tabella()
        riga = righe[indice]

        scroll_lento()
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", riga)
        time.sleep(1)

        celle = riga.find_elements(By.TAG_NAME, "td")
        if len(celle) < 6:
            indice += 1
            continue

        tipo = celle[0].text.strip()
        codice_gara = celle[1].text.strip()
        titolo = celle[2].text.strip()
        data_scadenza = celle[5].text.strip()

        if tipo != "Bando":
            indice += 1
            continue

        print(f"Trovato bando: {codice_gara} - clicco per il dettaglio")

        bottone = riga.find_element(By.CSS_SELECTOR, ".fa-search")
        clickable = bottone.find_element(By.XPATH, "./ancestor::a | ./ancestor::button")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", clickable)
        ActionChains(driver).move_to_element(clickable).pause(0.5).click(clickable).perform()

        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        dettaglio_url = driver.current_url
        print(f"Aperto: {dettaglio_url}")
        time.sleep(2)

        try:
            btn_dettaglio = driver.find_element(By.CSS_SELECTOR, "button.accordion-button")
            if btn_dettaglio.get_attribute("aria-expanded") == "false":
                btn_dettaglio.click()
                time.sleep(1)
        except:
            pass

        scheda_info = estrai_info_dettaglio(driver)
        allegati = estrai_allegati(driver)

        bandi_data.append({
            "codice": codice_gara,
            "categoria": "Servizio",
            "titolo": titolo,
            "link": dettaglio_url,
            "stato": "Aperto",
            "tipo_utente": "",
            "data_apertura": "",
            "data_scadenza": data_scadenza,
            "scheda_info": scheda_info,
            "allegati": allegati if allegati else [],
            "regione": "Lazio"
        })

        driver.back()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody")))
        time.sleep(2)
        indice += 1

    except Exception as e:
        print(f"Errore su '{codice_gara}': {e}")
        indice += 1
        try:
            driver.get(URL)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody")))
            time.sleep(2)
        except:
            pass
        continue

driver.quit()

if bandi_data:
    with open("bandi1.json", "w", encoding="utf-8") as f:
        json.dump(bandi_data, f, indent=2, ensure_ascii=False)
    print(f"{len(bandi_data)} bandi salvati su bandi.json")
else:
    print("Nessun bando trovato.")
