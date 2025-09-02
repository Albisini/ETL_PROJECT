import json
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def estrai_dettagli_bando(driver, wait, url_base, link_bando):
    scheda_info = {}
    allegati = []

    # Vai alla pagina dettaglio del bando
    driver.get(urljoin(url_base, link_bando))

    # Aspetta che il blocco chiave/valore sia presente
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.col-sm-4 > strong")))

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Estrazione chiavi/valori
    keys = soup.select("div.col-sm-4 > strong")
    values = soup.select("div.col-sm-8")
    for k, v in zip(keys, values):
        chiave = k.get_text(strip=True).rstrip(":")
        valore = v.get_text(strip=True)
        scheda_info[chiave] = valore

    # --- Nuova estrazione allegati con il metodo fornito ---
    allegati_divs = soup.select("div.accordion-body > div > div")
    for allegato_div in allegati_divs:
        titolo_tag = allegato_div.find("strong")
        titolo = titolo_tag.get_text(strip=True) if titolo_tag else "Senza titolo"
        link_tag = allegato_div.find("a", class_="Attach_label")
        link = urljoin(url_base, link_tag['href']) if link_tag and link_tag.has_attr('href') else None
        if link:
            allegati.append({"name": titolo, "link": link})

    # Se vuoi mantenere anche il vecchio metodo, puoi farlo qui sotto (commentato)
    # link_tags = soup.find_all("a", href=True)
    # for tag in link_tags:
    #     href = tag['href']
    #     name = tag.get_text(strip=True)
    #     if not name or not href or href.startswith('#'):
    #         continue
    #     if any(href.lower().endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip']):
    #         full_url = urljoin(url_base, href)
    #         allegati.append({"name": name, "link": full_url})

    return scheda_info, allegati

def scrape_bandi():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    url_base = "https://centraleacquisti.regione.lazio.it"
    url = url_base + "/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza?t=Bandi&ente=altri"
    driver.get(url)

    wait = WebDriverWait(driver, 20)
    bandi = []

    for pagina in range(1, 4):  # pagine 1,2,3
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "app-tabella-tr > tr.even, app-tabella-tr > tr.odd"))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")
        righe = soup.select("app-tabella-tr > tr.even, app-tabella-tr > tr.odd")

        for riga in righe:
            celle = riga.find_all("td")
            if len(celle) < 6:
                continue

            tipo = celle[0].get_text(strip=True)
            cig = celle[1].get_text(strip=True)
            titolo = celle[2].get_text(strip=True)
            ente = celle[3].get_text(strip=True)
            importo = celle[4].get_text(strip=True)
            scadenza = celle[5].get_text(strip=True)

            link = ""
            last_td = celle[-1]
            a_tag = last_td.find("a")
            if a_tag and a_tag.has_attr("href"):
                link = a_tag["href"]

            scheda_info = {}
            allegati = []
            if link:
                try:
                    scheda_info, allegati = estrai_dettagli_bando(driver, wait, url_base, link)
                    driver.back()
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "app-tabella-tr > tr.even, app-tabella-tr > tr.odd")))
                except Exception as e:
                    print(f"Errore nell'estrazione dettagli bando {link}: {e}")

            codice_bando = "LA" + str(random.randint(100000000000, 999999999999))
            bandi.append({
                "codice_bando": codice_bando,
                "categoria": "",
                "tipo": tipo,
                "titolo": titolo,
                "link": link,
                "stato": "Aperto",
                "tipo_utente": ente,
                "data_chiusura": scadenza,
                "allegati": allegati,
                "scheda_info": scheda_info,
                "regione": "Lazio"
            })

        if pagina < 3:
            try:
                btn_next = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f'button[title="Pagina {pagina + 1}"].btn'))
                )
                btn_next.click()
                time.sleep(random.uniform(2, 3))
            except Exception as e:
                print(f"Errore nel cliccare pagina {pagina + 1}: {e}")
                break

    driver.quit()
    return bandi

if __name__ == "__main__":
    bandi = scrape_bandi()

    with open("lazio.json", "w", encoding="utf-8") as f:
        json.dump(bandi, f, ensure_ascii=False, indent=2)

    print("Scraping completato. File salvato come bandi_lazio.json.")
