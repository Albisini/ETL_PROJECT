import sys
import logging
from selenium.webdriver.remote.remote_connection import LOGGER
LOGGER.setLevel(logging.WARNING)
sys.path.insert(0,'/usr/lib/chromium-browser/chromedriver')
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from tqdm.notebook import tqdm
import pandas
import json
import pprint
from chromedriver_py import binary_path

chrome_options = webdriver.ChromeOptions()  # Initialize Chrome options
chrome_options.add_argument('--headless')  # Run Chrome in headless mode - In our local notebook we can remove the `--headless` option.
chrome_options.add_argument('--no-sandbox')  # Disable Chrome’s default sandboxing behavior
chrome_options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems
chrome_options.add_argument("window-size=1900,800")  # Set the window size for the browser
chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")  # Set a custom user agent

service = Service(executable_path=binary_path)  # Create a Service object with the path to the ChromeDriver executable
wd = webdriver.Chrome(service=service, options=chrome_options)  # Initialize the WebDriver with the specified service and options

wd.get("https://bandi.regione.piemonte.it/")

wd.save_screenshot('screenshot.png')


import matplotlib.pyplot as plt
import matplotlib.image as mpimg

img = mpimg.imread('/content/screenshot.png')
plt.figure(figsize=(20, 10))
imgplot = plt.imshow(img)
plt.xticks([])
plt.yticks([])
plt.show()


import time
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Navigate to the website
wd.get("https://bandi.regione.piemonte.it/")

# Wait for the page to load
N = 5
print(f'Sleeping for {N} seconds ...')
time.sleep(N)

# Stampa i bottoni presenti
buttons = wd.find_elements(By.TAG_NAME, "button")
print(type(buttons))
for b in buttons:
    print(b.text)

# Save screenshot
screenshot = wd.save_screenshot("check_browser.png")
print(screenshot)

# Show screenshot (se vuoi, altrimenti commenta)
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

#img = mpimg.imread('check_browser.png')
#plt.figure(figsize=(20, 10))
#plt.imshow(img)
#plt.xticks([])
#plt.yticks([])
#plt.show()

# Gestione click cookie
if len(buttons) > 0:
    print("I see the Cookie button... YUM!")
    try:
        # Qui metti il bottone giusto per i cookie (adatta l'indice se serve)
        buttons[2].click()
        print("Cookie button clicked")
    except Exception as e:
        print("Errore cliccando il bottone cookie:", e)
else:
    print("No cookie button found or already accepted")

wait = WebDriverWait(wd, 20)

# Aspetta che il banner cookie sparisca o rimuovilo con JS se resta
try:
    print("Waiting for cookie banner to disappear...")
    wait.until(EC.invisibility_of_element_located((By.ID, "cconsent-bar")))
    print("Cookie banner is gone")
except:
    print("Cookie banner still visible, removing with JS...")
    wd.execute_script("document.getElementById('cconsent-bar').style.display = 'none';")

# Aspetta il form filtri
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.views-exposed-form")))

# Trova il filtro 'Stato'
select_el = wait.until(EC.presence_of_element_located((By.NAME, "field_stato_target_id")))
select = Select(select_el)

print("Opzioni disponibili:")
for opt in select.options:
    print(" -", opt.text)

# Seleziona "Aperto"
select.select_by_visible_text("Aperto")

# Trova e clicca il bottone "Applica"
submit_btn = wait.until(EC.element_to_be_clickable((By.ID, "edit-submit-ricerca--2")))
submit_btn.click()
print("Filtro applicato correttamente")
# Aspetta qualche secondo per caricare i risultati
time.sleep(10)

# Screenshot della pagina dopo il click
#post_screenshot = wd.save_screenshot("after_apply.png")
#print("Screenshot dopo l'applicazione del filtro salvato:", post_screenshot)

# Mostra screenshot risultato (opzionale)
#img = mpimg.imread('after_apply.png')
#plt.figure(figsize=(20, 10))
#plt.imshow(img)
#plt.xticks([])
#plt.yticks([])
#plt.show()

#Vediamo quante pagine sono
#num_pages = wd.find_elements(By.CSS_SELECTOR, 'nav[aria-label="Page navigation"] ul.pagination li.page-item:not(.next):not(.last) a.page-link')
#print(type(num_pages))
#print(len(num_pages))

# Vediamo il nuovo numero di pagine
page_items = wd.find_elements(By.CSS_SELECTOR, 'nav[aria-label="Page navigation"] ul.pagination li.page-item .page-link')

page_numbers = []
for item in page_items:
    text = item.text.strip()
    if text.isdigit():
        page_numbers.append(int(text))

max_page = max(page_numbers)
print("🔢 Numero totale di pagine:", max_page)

# Lunghezza 8
bandi = []  # Initialize an empty list to store room details
num_pages = 10  # Number of pages to scrape
page = 1

# Vediamo se riusciamo a recuperare tutti i titoli della prima pagina
list_titles = wd.find_elements(By.CSS_SELECTOR, "dd.field__item > h2")
print("Visualizziamo la lunghezza della classe titoli")
print(len(list_titles))
# 12 titoli
# Facciamoci stampare il primo
print("Visualizziamo il primo titolo")
print(list_titles[0].text)
# Recuperiamo url e titoli associati
cards = wd.find_elements(By.CSS_SELECTOR, "div.cardRp.cardBandiStato")

print(f"Trovate {len(cards)} card.")
# 12 card
print(type(cards))
print("Visualizziamo il primo elemento della lista card")
print(cards[0].text)


bandi_info = []

diz_selectors = {
    "titolo": "dd.field__item > h2",
    "url": "span.node-readmore.nav-link > a"
}



while True:
    # Aspetta la presenza delle card
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.cardRp.cardBandiStato")))

    cards = wd.find_elements(By.CSS_SELECTOR, "div.cardRp.cardBandiStato")
    print(f"Trovate {len(cards)} card nella pagina")

    for i, card in enumerate(cards, 1):
        try:
            titolo = card.find_element(By.CSS_SELECTOR, diz_selectors["titolo"]).text.strip()
            link = card.find_element(By.CSS_SELECTOR, diz_selectors["url"]).get_attribute("href")
            print(f"{i}. {titolo}")
            print(f"   ➜ {link}")
            bandi_info.append({"titolo": titolo, "url": link})
        except Exception as e:
            print(f"{i}. ❌ Errore nella card: {e}")

    # Verifica se esiste il pulsante Next
    next_buttons = wd.find_elements(By.CSS_SELECTOR, "li.page-item.next > a.page-link")
    if next_buttons:
        try:
            old_card = cards[0]  # Riferimento per aspettare staleness
            next_button = next_buttons[0]

            # Scrolla e clicca su "Next"
            wd.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
            time.sleep(0.5)
            next_button.click()

            # Aspetta che la pagina cambi
            WebDriverWait(wd, 10).until(EC.staleness_of(old_card))
            time.sleep(2)  # Piccola pausa extra
        except Exception as e:
            print("⚠️ Errore cliccando 'Next':", e)
            break
    else:
        print("✅ Fine pagine.")
        break

print("Visualizziamo bandi info")
print(bandi_info)
import pandas as pd
ds_bandi_info = pd.DataFrame(bandi_info)
ds_bandi_info.head()

#Numero totale di bandi
print(ds_bandi_info.shape[0])
#Salviamo in un csv
ds_bandi_info.to_csv('ds_bandi_piemonte.csv', index=False,encoding='utf-8')

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re


bandi_details = []  # Initialize an empty list to store detailed room information
# possiamo sempre fare un dizionario fuori con i selettori
diz_selectors_details = {
    "tipologia_di_contenuto" : "dd.field__item"
}

for _ , bandi in ds_bandi_info.iterrows():
    link = bandi["url"]
    #print(link)
    # Qui parte Selenium
    wd.set_window_size(1920, 1080)  # Set the browser window size
    wd.get(link)  
    time.sleep(2)  # Attendi il caricamento

    # Titolo
    titolo_pagina = wd.title.split("|")[0].strip()
    print(titolo_pagina)

    scheda_info = []

    # Tipologia_contenuto
    try:
      tipologia_elements = wd.find_elements(By.CSS_SELECTOR, "div.content-type dd.field__item")
      tipologie_testo = [el.text.strip() for el in tipologia_elements]
      tipologie_testo = "; ".join(tipologie_testo)
      print(tipologie_testo)
      scheda_info.append({'tipologia_contenuto' : tipologie_testo})
    except:
      tipologie_testo = ""
      print("Tipologia contenuto non trovato")

    # Oggetto
    try:
      oggetto = wd.find_element(By.CSS_SELECTOR, "dl.field--name-field-oggetto-bando dd.field__item").text.strip()
      print("Oggetto del bando:", oggetto)
      scheda_info.append({'oggetto_del_bando' : oggetto})
    except:
      oggetto = ""
      print("Oggetto del bando non trovato")


    # Data inizio
    try:
      data_inizio_elem = wd.find_element(By.CSS_SELECTOR, ".SecondoSottogruppoInfo .field--name-field-data-inizio time")
      data_inizio = data_inizio_elem.get_attribute("datetime")[:10]
      print("Data inizio del bando:", data_inizio)
    except:
      data_inizio = ""
      print("Data inizio del bando non trovata")

    # Scadenza
    try:
      data_scadenza_elem = wd.find_element(By.CSS_SELECTOR, ".SecondoSottogruppoInfo .field--name-field-data-scadenza time")
      data_scadenza = data_scadenza_elem.get_attribute("datetime")[:10]
      print("Data scandenza del bando:", data_scadenza)
    except:
      data_scadenza = ""
      print("Data scadenza del bando non trovata")

    # Temi
    try:
      temi_elements = wd.find_elements(By.CSS_SELECTOR, ".PrimoSottogruppoInfo .field--name-field-temi dd.field__item")
      temi = [el.text for el in temi_elements]
      print(temi)
      tema = ",".join(temi)
      print("Tema del bando:", tema)
    except:
      tema = ""
      print("Tema del bando non trovato")

    # Rivolto a
    try:
      rivolto_a_elements = wd.find_elements(By.CSS_SELECTOR, ".PrimoSottogruppoInfo .field--name-field-target dd.field__item ")
      rivolto_a = [el.text for el in rivolto_a_elements]
      tipo_utente = ",".join(rivolto_a)
      print("Tipo utente:", tipo_utente)
    except:
      tipo_utente = ""
      print("Tipo utente non trovato")

    # Risorse
    try:
      risorse_elements = wd.find_elements(By.CSS_SELECTOR, ".PrimoSottogruppoInfo .field--name-field-risorse dd.field__item")
      risorse_list = [el.text for el in risorse_elements]
      risorse = ",".join(risorse_list)
      print("Risorse:", risorse)
      scheda_info.append({'risorse' : risorse})

    except:
      risorse = ""
      print("Risorse non trovate")

    # Procedura
    try:
      procedura_descrizione = wd.find_element(By.CSS_SELECTOR, "div.box-procedura div.field--name-body")
      testo_descrizione = procedura_descrizione.text.strip()
      testo_descrizione = " ".join(testo_descrizione.split())
      print("Procedura:", testo_descrizione)
      scheda_info.append({'procedura' : testo_descrizione})
    except:
      testo_descrizione = ""
      print("Procedura non trovata")

    # Chiarimenti
    # Qui ho un primo pdf eventualmente da usare con un chatbot che me li riassuma
    try:
      pdf_element = wd.find_element(By.CSS_SELECTOR, ".box-chiarimenti a[href$='.pdf']")
      pdf_url = pdf_element.get_attribute("href")
      print("PDF chiarimenti:", pdf_url)
      scheda_info.append({'chiarimenti' : pdf_url})
    except:
      pdf_url = ""
      print("PDF chiarimenti non trovato:")

    # Chi può partecipare ?
    # --- Chi può partecipare ---
    try:
      summary_chi = wd.find_element(By.XPATH, "//summary[contains(text(), 'Chi può partecipare')]")
      wd.execute_script("arguments[0].click();", summary_chi)
      time.sleep(0.3)  # attesa per espansione
      chi_elem = wd.find_element(By.CSS_SELECTOR, ".field--name-field-chi-puo-partecipare")
      chi_puo_text = chi_elem.text.strip()
      print("Chi può partecipare:", chi_puo_text)
      scheda_info.append({'partecipanti' : chi_puo_text})
    except:
      chi_puo_text = ""
      print("Chi può partecipare non trovato")

    # Dotazione finanziaria con estrazione importo
    try:
      summary_dotazione = wd.find_element(By.XPATH, "//summary[contains(text(), 'Dotazione finanziaria')]")
      wd.execute_script("arguments[0].click();", summary_dotazione)
      time.sleep(0.3)
      dotazione_elem = wd.find_element(By.CSS_SELECTOR, ".field--name-field-importo")
      dotazione_text = dotazione_elem.text.strip()
      # Estraggo solo la parte con il simbolo € e numero
      match = re.search(r"(€\s?[\d\.\,]+)", dotazione_text)
      if match:
          dotazione_importo = match.group(1)
      else:
          dotazione_importo = dotazione_text  # fallback
      print("Dotazione finanziaria:", dotazione_importo)
      scheda_info.append({'dotazione_finanziaria' : dotazione_importo})
    except:
      dotazione_importo = ""
      print("Dotazione finanziari non trovata")

    # Come presentare la domanda
    try:
      summary_domanda = wd.find_element(By.XPATH, "//summary[contains(text(),'Come presentare domanda')]")
      wd.execute_script("arguments[0].click();", summary_domanda)
      time.sleep(0.3)

      note_domanda_elem = wd.find_element(
        By.XPATH,
        "//summary[contains(text(),'Come presentare domanda')]/following-sibling::div//div[contains(@class,'field--name-field-note-presentazione-domanda')]"
      )
      note_domanda_text = note_domanda_elem.text.strip()
      print("Come presentare domanda:", note_domanda_text)
      scheda_info.append({'come_presentare_domanda' : note_domanda_text})
    except:
      note_domanda_text = ""
      print("Come presentare la domanda non trovata")



    # Allegati
    # Apri il dettaglio "Allegato testo procedura" per assicurarti che il contenuto sia visibile
    try:
      summary_allegati = wd.find_element(By.XPATH, "//summary[contains(text(),'Allegato testo procedura')]")
      wd.execute_script("arguments[0].click();", summary_allegati)
      time.sleep(0.3)
    except:
      print("Errore nell'apertura della sezione Allegato testo procedura:")

    # Ora seleziona tutti gli allegati all'interno del div corrispondente
    allegati = []
    try:
      # Trova il contenitore degli allegati dentro details-wrapper
      container = wd.find_element(By.CSS_SELECTOR, "details.js-form-wrapper div.field--name-field-testo-procedura")
      # Trova tutti i div.field__item (ogni allegato)
      allegati_items = container.find_elements(By.CSS_SELECTOR, "div.field__item")

      for item in allegati_items:
        try:
            a_tag = item.find_element(By.CSS_SELECTOR, "dl.field__items dt a")
            href = a_tag.get_attribute("href")
            nome = a_tag.text.strip()
            titolo = a_tag.get_attribute("title")
            allegati.append({
                "nome": nome,
                "titolo": titolo,
                "url": href
            })
        except:
            print(f"Errore lettura allegato in un item")
            continue
    except:
      print("Errore nell'estrazione degli allegati:")

    print("Allegati trovati:", allegati)

# Alla fine del tuo dict di dettaglio bandi, aggiungi:


    bandi_details.append({'codice' : '',
                         'titolo': titolo_pagina,
                         'categoria' : tema,
                         'url': link,
                         'stato' : 'APERTO',
                         'tipo_utente' : tipo_utente,
                         'data_chiusura' : data_scadenza,
                         'allegati': allegati,
                         #'tipologia_contenuto' : tipologie_testo,
                         #'oggetto_del_bando' : oggetto,
                         #'data_inizio' : data_inizio,
                         #'data_chiusura' : data_scadenza,
                         #'risorse' : risorse,
                         #'procedura' : testo_descrizione,
                         #'chiarimenti' : pdf_url,
                         #'partecipanti' : chi_puo_text,
                         #'dotazione_finanziaria' : dotazione_importo,
                         #'come_presentare_domanda' : note_domanda_text,
                          'scheda_info' : scheda_info,
                          'regione' : 'Piemonte'
                          })
    print(bandi_details)
    import json

    # Salva la lista bandi_details in un file JSON
    with open("bandi_details.json", "w", encoding="utf-8") as f:
      json.dump(bandi_details, f, ensure_ascii=False, indent=4)

    print("File JSON salvato come 'bandi_details.json'")










