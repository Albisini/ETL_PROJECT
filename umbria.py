import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
options = Options()
# options.add_argument("--headless")  # togli il commento per esecuzione senza finestra
options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=options)

def get_scheda_info(driver):
    scheda_info = {}
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.divInformazioni dl"))
        )
        dl = driver.find_element(By.CSS_SELECTOR, "div.divInformazioni dl")
        dts = dl.find_elements(By.TAG_NAME, "dt")
        dds = dl.find_elements(By.TAG_NAME, "dd")
        for dt, dd in zip(dts, dds):
            key = dt.text.strip()
            value = dd.text.strip()
            scheda_info[key] = value
    except TimeoutException:
        print("⚠️ Timeout nel caricamento delle informazioni")
    except Exception as e:
        print("Errore get_scheda_info:", e)
    return scheda_info

def get_allegati(driver):
    allegati = []
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.divAllegati"))
        )
        links = driver.find_elements(By.CSS_SELECTOR, "div.divAllegati a")
        for link in links:
            name = link.text.strip()
            href = link.get_attribute("href")
            if href:
                allegati.append({"name": name, "link": href})
    except TimeoutException:
        print("⚠️ Timeout nel caricamento degli allegati")
    except Exception as e:
        print("Errore get_allegati:", e)
    return allegati

try:
    driver.get("https://www.regione.umbria.it/la-regione/bandi")

    iframe_id = "_48_INSTANCE_murcPC6Xfznf_iframe"
    WebDriverWait(driver, 10).until(
        EC.frame_to_be_available_and_switch_to_it((By.ID, iframe_id))
    )
    print(f"✅ Switch effettuato su iframe {iframe_id}")

    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table.taglib-search-iterator"))
    )
    print("✅ Tabella trovata!")

    table = driver.find_element(By.CSS_SELECTOR, "table.taglib-search-iterator")
    rows = table.find_elements(By.CSS_SELECTOR,
        "tr.portlet-section-body.results-row, tr.portlet-section-alternate.results-row.alt"
    )

    data_base = []
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        if len(cells) >= 8:
            link_tag = None
            try:
                link_tag = cells[7].find_element(By.TAG_NAME, "a")
            except NoSuchElementException:
                pass
            dettaglio_link = link_tag.get_attribute("href") if link_tag else ""

            data_base.append({
                "codice": "",
                "categoria": cells[0].text.strip(),
                "titolo": cells[2].text.strip(),
                "link": dettaglio_link,
                "stato": "Aperto",
                "data_chiusura": cells[4].text.strip(),
                "regione": "Umbria"
            })

    data = []
    for bando in data_base:
        if bando["link"]:
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[1])
            driver.get(bando["link"])

            time.sleep(2)  # pausa per caricamento JS

            allegati = get_allegati(driver)
            scheda_info = get_scheda_info(driver)
            tipo_utente= scheda_info.pop("Tipo Beneficiario", None)
            bando["allegati"] = allegati
            bando["scheda_info"] = scheda_info
            bando["tipo_utente"] = tipo_utente
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        else:
            bando["allegati"] = []
            bando["scheda_info"] = {}
            bando["tipo_utente"] = ""
        data.append(bando)

    for b in data:
        print(b)
    with open("bandi_umbria.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✅ Dati salvati in bandi_umbria.json")
except TimeoutException:
    print("❌ Timeout: la tabella non è stata caricata.")
    with open("debug.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)

finally:
    driver.quit()
