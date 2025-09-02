from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import dateparser
import time
import json

# === CONFIGURAZIONI ===
BASE_URL = "https://www.regione.liguria.it"
URL_TEMPLATE = "https://www.regione.liguria.it/homepage-bandi-e-avvisi/publiccompetitions/?page={}"
DATA_SOGLIA = dateparser.parse("15 Luglio 2025")
CATEGORIE_AMMESSE = ["CONTRIBUTI", "GARE", "AVVISI", "CONCORSI"]

# === IMPOSTAZIONI SELENIUM ===
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
driver = webdriver.Chrome(options=options)

def estrai_bandi_dalla_pagina():
    soup = BeautifulSoup(driver.page_source, "html.parser")
    bandi_trovati = []

    for item in soup.select(".pc_latest_item_bando"):
        categoria_el = item.select_one(".pc_latest_item_fondo_link")
        if not categoria_el:
            continue
        categoria = categoria_el.text.strip().upper()
        if categoria not in CATEGORIE_AMMESSE:
            continue

        tipo_utente_el = item.select_one(".pc_latest_item_beneficiari")
        tipo_utente = tipo_utente_el.text.strip().capitalize() if tipo_utente_el else ""

        link_tag = item.select_one("a.bando_link")
        if not link_tag:
            continue

        titolo = link_tag.text.strip()
        relative_url = link_tag["href"]
        full_url = urljoin(BASE_URL, relative_url)

        bandi_trovati.append({
            "titolo": titolo,
            "url": full_url,
            "categoria": categoria,
            "tipo_utente": tipo_utente
        })

    return bandi_trovati

def estrai_dettagli_bando(url):
    driver.get(url)
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    data_el = soup.select_one(".pc_latest_item_chiusura")
    if data_el and "Data chiusura:" in data_el.text:
        data_txt = data_el.text.split("Data chiusura:")[-1].strip()
        data_dt = dateparser.parse(data_txt, languages=['it'])
        if not data_dt or data_dt <= DATA_SOGLIA:
            return None
        data_scadenza_raw = data_txt
    else:
        return None

    allegati = []
    for li in soup.select("ul.docs-list > li"):
        nome_tag = li.select_one("p.card-title a")
        down_tag = li.select_one("ul.list-group a")
        if nome_tag and down_tag:
            name = nome_tag.text.strip()
            link = urljoin(BASE_URL, down_tag["href"])
            allegati.append({"name": name, "link": link})

    descrizione_el = soup.select_one("div.pc_item_descrizione")
    scheda_info = {}
    if descrizione_el:
        paragrafi = descrizione_el.find_all("p")
        for idx, p in enumerate(paragrafi, 1):
            testo = p.get_text(strip=True)
            if testo:
                scheda_info[f"paragrafo_{idx}"] = testo

    return {
        "data_chiusura": data_scadenza_raw,
        "allegati": allegati,
        "scheda_info": scheda_info
    }

def main():
    risultati = []
    pagina = 1

    while True:
        url = URL_TEMPLATE.format(pagina)
        driver.get(url)
        print(f"\nPagina {pagina}: {url}")
        time.sleep(2)

        bandi = estrai_bandi_dalla_pagina()
        if not bandi:
            print(" Nessun bando trovato. Fine.")
            break

        for bando in bandi:
            print(f" Bando: {bando['titolo']}")
            dettagli = estrai_dettagli_bando(bando["url"])
            if dettagli:
                risultati.append({
                    "codice": "",
                    "categoria": bando["categoria"],
                    "titolo": bando["titolo"],
                    "url": bando["url"],
                    "stato": "Aperto",
                    "tipo_utente": bando["tipo_utente"],
                    "data_chiusura": dettagli["data_scadenza"],
                    "allegati": dettagli["allegati"],
                    "scheda_info": dettagli["scheda_info"],
                    "regione": "Liguria"
                })

        pagina += 1

    driver.quit()

    with open("bandi_liguria.json", "w", encoding="utf-8") as f:
        json.dump(risultati, f, ensure_ascii=False, indent=2)

    print(f"\nSalvati {len(risultati)} bandi in 'bandi_liguria.json'")

if __name__ == "__main__":
    main()
