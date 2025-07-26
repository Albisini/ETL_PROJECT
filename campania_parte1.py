import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
from collections import OrderedDict
import random
BASE_URL = "https://agricoltura.regione.campania.it/"
START_URL = urljoin(BASE_URL, "bandi.html")

def estrai_scheda_info(link):
    scheda_info = OrderedDict()
    allegati = []

    try:
        res = requests.get(link, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, "html.parser")
        content = soup.select_one("div.col-md-8")

        if not content:
            return OrderedDict(), []

        current_section = None

        for tag in content.find_all(["h2", "h3", "p", "ul", "ol"]):
            if tag.name in ["h2", "h3"]:
                current_section = tag.get_text(strip=True)
                scheda_info[current_section] = ""
            elif tag.name == "p" and current_section:
                text = tag.get_text(" ", strip=True)
                if text:
                    scheda_info[current_section] += " " + text
            elif tag.name in ["ul", "ol"] and current_section:
                for li in tag.find_all("li"):
                    scheda_info[current_section] += " - " + li.get_text(strip=True)

            # Allegati PDF
            if tag.name == "p" and tag.find("a", href=True):
                a = tag.find("a")
                if a["href"].lower().endswith(".pdf"):
                    allegati.append({
                        "name": a.get_text(strip=True),
                        "link": urljoin(link, a["href"])
                    })

    except Exception as e:
        print(f"Errore in {link}: {e}")

    return scheda_info, allegati

# -------- PARTE PRINCIPALE --------

response = requests.get(START_URL)
soup = BeautifulSoup(response.content, "html.parser")
table_rows = soup.select("table.table tbody tr")

bandi = []
current_section = None

for row in table_rows:
    cols = row.find_all("td")

    if len(cols) == 1 and "colspan" in cols[0].attrs:
        current_section = cols[0].get_text(strip=True)
        continue

    if len(cols) == 2:
        codice_bando = "CA" + str(random.randint(100000000000, 999999999999))

        bando = OrderedDict()
        bando["codice"] = codice_bando
        bando["categora"] = "Agricoltura"
        bando["titolo"] = cols[0].get_text(strip=True)
        link_tag = cols[0].find("a")
        if link_tag:
            bando["link"] = urljoin(BASE_URL, link_tag["href"])
        else:
            bando["link"] = None

        bando["stato"] = "Aperto"
        bando["tipo_utente"] = ""
        bando["data_chiusura"] = cols[1].get_text(strip=True)
        # Estrazione scheda e allegati
        scheda_info = OrderedDict()
        allegati = []
        if bando["link"]:
            scheda_info, allegati = estrai_scheda_info(bando["link"])
        bando["allegati"] = allegati

        # Infine: regione, scheda_info
        bando["regione"] = "Campania"
        bando["scheda_info"] = scheda_info

        bandi.append(bando)

# Salvataggio
with open("campania1.json", "w", encoding="utf-8") as f:
    json.dump(bandi, f, ensure_ascii=False, indent=2)

print(f"✅ Salvati {len(bandi)} bandi in 'bandi.json'")
