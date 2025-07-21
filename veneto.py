import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://bandi.regione.veneto.it/Public/Elenco?Tipo=1"

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 20)
driver.get(URL)

bandi = []

def estrai_testo_sicuro(by, selettore):
    try:
        el = driver.find_element(by, selettore)
        return el.text.strip()
    except:
        return ""

def estrai_blocchi_scheda_info():
    scheda = {}
    blocchi = driver.find_elements(By.CSS_SELECTOR, ".rowContainer")

    for blocco in blocchi:
        try:
            label = blocco.find_element(By.CSS_SELECTOR, ".display-label").text.strip()
            if not label:
                continue

            # Caso speciale: Acquisti Verdi - Politiche Sostenibili
            if label == "Acquisti Verdi - Politiche Sostenibili":
                voci = blocco.find_elements(By.CSS_SELECTOR, ".display-field.padding-none .display-field.padding-none")
                valore = "\n".join(v.text.strip() for v in voci if v.text.strip())
                scheda[label] = valore
            else:
                valore = blocco.find_element(By.CSS_SELECTOR, ".display-field").text.strip()
                scheda[label] = valore
        except:
            continue
    return scheda

def estrai_allegati():
    allegati = []
    try:
        # Prendo tutti gli <a> con queste classi e href contenente idAllegato
        link_elem = driver.find_elements(By.CSS_SELECTOR, 'a.col-xs-12.col-sm-8.col-md-8.col-lg-8[href*="/Public/Download?idAllegato="]')
        for a in link_elem:
            name = a.text.strip()
            href = a.get_attribute("href")
            if not name or not href:
                continue
            full_href = href if href.startswith("http") else f"https://bandi.regione.veneto.it{href}"
            allegati.append({
                "name": name,
                "link": full_href
            })
    except Exception as e:
        print(" Errore nell'estrazione allegati:", e)
    return allegati

def vai_a_dettaglio(link):
    driver.get(link)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "display-field")))
    time.sleep(1)

    # Titolo
    titolo = estrai_testo_sicuro(By.CSS_SELECTOR, "div.col-xs-12.col-sm-10.col-md-10.col-lg-10.display-field")

    # Scadenza
    data_scadenza = ""
    blocchi_scadenza = driver.find_elements(By.CSS_SELECTOR, ".padding-xs-none.border-separator")
    for blocco in blocchi_scadenza:
        try:
            label = blocco.find_element(By.CSS_SELECTOR, ".display-label").text.strip()
            if "Scadenza" in label:
                data_scadenza = blocco.find_element(By.CSS_SELECTOR, ".display-field").text.strip()
                break
        except:
            continue

    # Categoria e Importo
    categoria = ""
    importo = ""
    righe = driver.find_elements(By.CSS_SELECTOR, ".rowContainer")
    for riga in righe:
        try:
            if "Categoria" in riga.text:
                categoria = riga.find_element(By.CSS_SELECTOR, ".display-field").text.strip()
            if "Importo" in riga.text:
                try:
                    importo = riga.find_element(By.CSS_SELECTOR, "#container-importo").text.strip()
                except:
                    importo = riga.find_element(By.CSS_SELECTOR, ".display-field").text.strip()
        except:
            continue

    # Scheda info e allegati
    scheda_info = estrai_blocchi_scheda_info()
    allegati = estrai_allegati()

    bandi.append({
        "codice": "",
        "categoria": categoria,
        "titolo": titolo,
        "link": link,
        "stato": "Aperto",
        "tipo_utente": "",
        "data_apertura": "",
        "data_scadenza": data_scadenza,
        "scheda_info": scheda_info,
        "allegati": allegati,
        "regione": "Veneto"
    })

    driver.back()
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.evidenzia")))
    time.sleep(1)

# Naviga 4 pagine
for pagina in range(1, 5):
    print(f"🟦 Pagina {pagina}")
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.evidenzia")))
    time.sleep(1)

    links = [a.get_attribute("href") for a in driver.find_elements(By.CSS_SELECTOR, "a.evidenzia")]
    for link in links:
        try:
            vai_a_dettaglio(link)
        except Exception as e:
            print(f"Errore su {link}: {e}")

    if pagina < 4:
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, f'a.paginate_button[data-dt-idx="{pagina+1}"]')
            driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(2)
        except Exception as e:
            print(f" Errore cambio pagina: {e}")
            break

driver.quit()

# Salva JSON
with open("bandi_veneto.json", "w", encoding="utf-8") as f:
    json.dump(bandi, f, indent=2, ensure_ascii=False)

print(f"Salvati {len(bandi)} bandi in 'bandi_veneto.json'")
