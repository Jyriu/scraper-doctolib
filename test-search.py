from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import csv
import re
from datetime import datetime
from tqdm import tqdm

# --- Fonctions utilitaires ---
def parse_price(text):
    match = re.findall(r"\d+[\.,]?\d*", text)
    if not match:
        return None
    try:
        return float(match[0].replace(',', '.'))
    except:
        return None

def date_in_range(date_text, start, end):
    months = {
        "janvier": 1, "février": 2, "mars": 3, "avril": 4,
        "mai": 5, "juin": 6, "juillet": 7, "août": 8,
        "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
    }
    try:
        parts = date_text.strip().split()
        if len(parts) == 2:
            day, month_str = parts
            day = int(day)
            month = months.get(month_str.lower())
            if month:
                date_obj = datetime(datetime.now().year, month, day)
                return start <= date_obj <= end
    except:
        pass
    return False

# --- Entrée utilisateur ---
try:
    max_results = int(input("Entrez le nombre de résultats maximum à afficher : "))
except ValueError:
    print("Erreur : vous devez entrer un nombre entier pour le nombre de résultats.")
    exit()

try:
    start_date = datetime.strptime(input("Entrez la date de début (JJ/MM/AAAA) : "), "%d/%m/%Y")
    end_date = datetime.strptime(input("Entrez la date de fin (JJ/MM/AAAA) : "), "%d/%m/%Y")
except ValueError:
    print("Erreur : date invalide.")
    exit()

speciality = input("Entrez la spécialité (ex: 'dermatologue') : ")
insurance_type = input("Type d'assurance ('secteur 1', 'secteur 2', 'non conventionné') : ").lower()
consultation_type = input("Type de consultation ('en visio' ou 'sur place') : ").lower()

try:
    min_price = float(input("Prix minimum (€) : "))
    max_price = float(input("Prix maximum (€) : "))
except ValueError:
    print("Erreur : vous devez entrer des nombres pour les prix.")
    exit()

geo_filter = input("Adresse libre (laisser vide si non applicable) : ")
postal_code = input("Code postal : ")
location = geo_filter if geo_filter else postal_code

# --- Setup navigateur ---
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
wait = WebDriverWait(driver, 20)

# --- Recherche ---
driver.get("https://www.doctolib.fr/")

spec_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.searchbar-input.searchbar-query-input")))
spec_input.clear()
spec_input.send_keys(speciality)
wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "ul.dl-dropdown")))
wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "li[data-type='speciality'] button"))).click()

loc_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.searchbar-input.searchbar-place-input")))
loc_input.clear()
loc_input.send_keys(location)

try:
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "ul.dl-dropdown")))
    suggestions = driver.find_elements(By.CSS_SELECTOR, "button.searchbar-result")
    for suggestion in suggestions:
        if location.lower() in suggestion.text.lower():
            driver.execute_script("arguments[0].click();", suggestion)
            break
    else:
        loc_input.clear()
        loc_input.send_keys(postal_code)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "ul.dl-dropdown")))
        driver.execute_script("arguments[0].click();", driver.find_elements(By.CSS_SELECTOR, "button.searchbar-result")[0])
except Exception as e:
    print(f"Erreur localisation : {e}")
    loc_input.clear()
    loc_input.send_keys(postal_code)
    loc_input.send_keys(Keys.ENTER)

try:
    search_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.searchbar-submit-button-label")))
    driver.execute_script("arguments[0].click();", search_btn)
except Exception as e:
    print("Erreur bouton recherche :", e)
    input("Appuyez sur Entrée pour quitter...")
    driver.quit()
    exit()

try:
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.flex.gap-16.flex-col.w-full")))
except Exception as e:
    print("Erreur chargement résultats :", e)
    input("Appuyez sur Entrée pour quitter...")
    driver.quit()
    exit()

# --- Extraction ---
results = []
processed = 0
print("\nExtraction en cours...\n")

while processed < max_results:
    cards = driver.find_elements(By.CSS_SELECTOR, "div.dl-card[data-design-system-component='Card']")

    for card in tqdm(cards, desc=f"Traitement des praticiens ({processed}/{max_results})"):
        if processed >= max_results:
            break
        try:
            name = card.find_element(By.CSS_SELECTOR, "h2").text.strip()
            href = card.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
            card_text = card.text.lower()

            if insurance_type not in card_text:
                continue
            if consultation_type not in card_text:
                continue

            address = ' '.join([p.text for p in card.find_elements(By.CSS_SELECTOR, "div.flex.flex-wrap p")])

            date_tags = card.find_elements(By.CSS_SELECTOR, "[data-test-id='availabilities-container'] span")
            slot_date = next((span.text.strip() for span in date_tags if date_in_range(span.text.strip(), start_date, end_date)), None)
            if not slot_date:
                continue

            driver.execute_script("window.open(arguments[0], '_blank');", href)
            driver.switch_to.window(driver.window_handles[-1])

            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.p-0 li span.dl-profile-fee-tag")))
                price = parse_price(driver.find_element(By.CSS_SELECTOR, "ul.p-0 li span.dl-profile-fee-tag").text)
            except:
                price = None

            driver.close()
            driver.switch_to.window(driver.window_handles[0])

            if price is None or not (min_price <= price <= max_price):
                continue

            results.append({
                "Nom": name,
                "Adresse": address,
                "Type assurance": insurance_type,
                "Consultation": consultation_type,
                "Prochaine disponibilité": slot_date,
                "Prix": price
            })
            processed += 1
        except Exception:
            continue

    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Page suivante']")
        if "disabled" in next_btn.get_attribute("class"):
            break
        driver.execute_script("arguments[0].scrollIntoView();", next_btn)
        next_btn.click()
        time.sleep(3)
    except:
        break

# --- Export CSV ---
if results:
    with open("medecins_doctolib.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"\n{len(results)} praticiens exportés dans medecins_doctolib.csv")
else:
    print("\nAucun praticien correspondant trouvé.")

input("Appuyez sur Entrée pour quitter...")
driver.quit()