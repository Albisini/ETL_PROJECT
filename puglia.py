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

driver = webdriver.Chrome(options=options)

base_url = "https://www.regione.puglia.it/bandi-e-avvisi?p_p_id=RicercaNews_INSTANCE_4CYftWJNTppj&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&_RicercaNews_INSTANCE_4CYftWJNTppj_datefilterSel=&_RicercaNews_INSTANCE_4CYftWJNTppj_searchContent=&_RicercaNews_INSTANCE_4CYftWJNTppj_toggler=false&p_p_resource_id=%2Fricerca%2Fnews%2Fnews-list&_RicercaNews_INSTANCE_4CYftWJNTppj_resetCur=false&_RicercaNews_INSTANCE_4CYftWJNTppj_delta=10&_RicercaNews_INSTANCE_4CYftWJNTppj_cur="

bandi = []

for page in range(1, 14):
    print(f" Pagina {page}")
    driver.get(base_url + str(page))
    time.sleep(2)

    containers = driver.find_elements(By.CSS_SELECTOR, "div.row.news-list-item")

    for c in containers:
        try:
            titolo_el = c.find_element(By.CSS_SELECTOR, "div.row.titolo a")
            titolo = titolo_el.text.strip()
            link = titolo_el.get_attribute("href")

            # Trova la categoria
            try:
                categoria_el = c.find_element(By.CSS_SELECTOR, "div.categoria-news span")
                categoria = categoria_el.text.strip()
            except:
                categoria = ""
            # Apri il link del bando
            driver.execute_script("window.open(arguments[0]);", link)
            driver.switch_to.window(driver.window_handles[1])

            # Attendi che la descrizione si carichi
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.news-description"))
            )
            soup = BeautifulSoup(driver.page_source, "html.parser")

            descrizione = ""
            desc_el = soup.select_one("div.news-description")
            if desc_el:
                descrizione = desc_el.get_text(separator="\n", strip=True)

            # Estrai gli allegati
            allegati = []
            document_section = soup.select("ul.document-list.generic-content-document-list li")
            for li in document_section:
                a_tag = li.find("a", href=True)
                if a_tag and ".pdf" in a_tag["href"]:
                    name = a_tag.get_text(strip=True)
                    href = a_tag["href"]
                    full_link = href if href.startswith("http") else "https://www.regione.puglia.it" + href
                    allegati.append({
                        "name": name,
                        "link": full_link
                    })
            codice_bando = "PU" + str(random.randint(100000000000, 999999999999))
            bandi.append({
                "codice": codice_bando,
                "categoria":categoria,
                "titolo": titolo,
                "url": link,
                "stato": "Aperto",
                "tipo_utente":"",
                "data_chiusura": "",
                "allegati": allegati,
                "scheda_info": {
                    "descrizione": descrizione
                },
                "regione": "Puglia"
            })

            # Chiudi la scheda secondaria
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        except Exception as e:
            print("⚠️ Errore su un bando:", e)
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            continue

# Salvataggio finale
with open("bandi_puglia.json", "w", encoding="utf-8") as f:
    json.dump(bandi, f, ensure_ascii=False, indent=2)

driver.quit()
print(f"✅ Completato. Salvati {len(bandi)} bandi.")

