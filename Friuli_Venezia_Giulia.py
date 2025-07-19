
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin

def main():
    base_url = "https://www.regione.fvg.it"
    start_url = base_url + "/rafvg/cms/RAFVG/MODULI/bandi_avvisi/"

    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 15)
    risultati = []

    def process_page(url):
        driver.get(url)
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.box-link.box-bando a")))
        bandi_links = driver.find_elements(By.CSS_SELECTOR, "div.box-link.box-bando a")
        bandi_info = []
        for bando in bandi_links:
            titolo = bando.find_element(By.CSS_SELECTOR, "div.box-titolo h3").text.strip()
            href = bando.get_attribute("href")
            bandi_info.append((titolo, href))

        for i, (titolo, href) in enumerate(bandi_info, start=1):
            print(f"[+] Titolo: {titolo}")
            print("    ↳ Link dettaglio:", href)

            driver.get(href)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.box-descrizione")))

            # DESCRIZIONE
            descrizione_div = driver.find_element(By.CSS_SELECTOR, "div.box-descrizione")
            descrizione_testo = descrizione_div.text.strip()
            scheda_info = {"descrizione": descrizione_testo}

            # DATA SCADENZA
            data_scadenza = ""
            span_elements = driver.find_elements(By.CSS_SELECTOR, "span.box-header-important")
            for i in range(len(span_elements) - 1):
                if "scadenza" in span_elements[i].text.lower():
                    data_scadenza = span_elements[i + 1].text.strip()
                    break
            categoria = ""
            try:
                categoria_div = driver.find_element(By.CSS_SELECTOR, "div.box-campo")
                categoria = categoria_div.text.strip()
            except Exception:
                pass
            # ALLEGATI
            allegati = []
            try:
                allegati_links = driver.find_elements(By.CSS_SELECTOR, "div.box-allegati ul.box-allegati-list a.file")
                for link in allegati_links:
                    name = link.text.strip()
                    href_file = link.get_attribute("href")
                    if href_file and name:
                        full_link = href_file if href_file.startswith("http") else urljoin(base_url, href_file)
                        allegati.append({"name": name, "link": full_link})
            except Exception:
                pass

            risultati.append({
                "codice": "",
                "titolo": titolo,
                "categoria": categoria,
                "link_dettaglio": href,
                "stato": "Aperto",
                "tipo_utente": "",
                "data_apertura": "",
                "data_chiusura": data_scadenza,
                "allegati": allegati,
                "scheda_informativa": scheda_info,
                "regione": "Friuli Venezia Giulia"
            })

    try:
        # Vai alla prima pagina
        driver.get(start_url)
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.pagination-regione li a")))

        # Raccogli tutti i link delle pagine
        pag_links = driver.find_elements(By.CSS_SELECTOR, "ul.pagination-regione li a")
        unique_pages = set()
        for link in pag_links:
            href = link.get_attribute("href")
            if href:
                full_url = href if href.startswith("http") else urljoin(base_url, href)
                unique_pages.add(full_url)

        # Aggiungi anche la prima pagina manualmente
        unique_pages.add(start_url)

        # Ordina per numero pagina
        sorted_pages = sorted(list(unique_pages), key=lambda x: int(x.split("pag=")[-1]) if "pag=" in x else 1)

        print(f"Trovate {len(sorted_pages)} pagine da processare...")

        for page_url in sorted_pages:
            print(f"\n Visitando: {page_url}")
            process_page(page_url)

        # Salva il risultato
        with open("bandi_Friuli_Venezia.json", "w", encoding="utf-8") as f:
            json.dump(risultati, f, ensure_ascii=False, indent=2)

        print("File salvato come 'bandi_fvg.json'.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
