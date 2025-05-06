from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
from datetime import datetime
import locale
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException


service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.get("https://www.doctolib.fr/")

wait = WebDriverWait(driver, 20)

try:
    consent_button = wait.until(
        EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
    )
    consent_button.click()
except Exception as e:
    print("Pas de popup Didomi détecté ou déjà fermé.")

wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.searchbar-input.searchbar-query-input")))

wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.searchbar-input.searchbar-query-input")))
speciality_input = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "input.searchbar-input.searchbar-query-input")))

speciality_input.clear()
speciality_input.send_keys("dentiste")

wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "ul.dl-dropdown")))
wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "li[data-type='speciality'] button"))).click()

wait.until(
    EC.presence_of_element_located((By.CSS_SELECTOR,
        "input.searchbar-input.searchbar-place-input")))

place_input = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR,
        "input.searchbar-input.searchbar-place-input")))

place_input.clear()
place_input.send_keys("94000")

wait.until(
    EC.text_to_be_present_in_element_value((By.CSS_SELECTOR,
         "input.searchbar-input.searchbar-place-input"),
         "94000"))

place_input.send_keys(Keys.ENTER)

time.sleep(5)

# Attendre que le bouton "Page suivante" soit présent dans le DOM
next_page = wait.until(
    EC.presence_of_element_located((By.XPATH, "//a[span[contains(text(), 'Page suivante')]]"))
)

# Scroller jusqu'au bouton "Page suivante" pour charger toutes les cards de praticiens
driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_page)
time.sleep(2)  # Laisse le temps au chargement dynamique de s'effectuer

# get les dates disponibles

date_debut_str = "12/05/2025"
date_fin_str = "19/05/2025"
date_debut = datetime.strptime(date_debut_str, "%d/%m/%Y")
date_fin = datetime.strptime(date_fin_str, "%d/%m/%Y")

try:
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, "fr_FR")
    except locale.Error:
        print("⚠️ Locale française non disponible, le parsing des dates risque d'échouer.")

# Récupérer toutes les cards praticiens de la page
cards = driver.find_elements(By.CSS_SELECTOR, "div.dl-card.dl-card-bg-white.dl-card-variant-shadow-3")

trouve = False
for card in cards:
    try:
        # Chercher le span qui contient "Prochain RDV le"
        span_rdv = card.find_element(By.XPATH, ".//span[contains(text(), 'Prochain RDV le')]")
        # Extraire la date du <strong> à l'intérieur
        strong = span_rdv.find_element(By.XPATH, ".//strong")
        date_str = strong.text.strip()  # ex: "13 mai 2025"
        # Convertir la date en datetime (mois en toutes lettres en français)
        date_dispo = datetime.strptime(date_str, "%d %B %Y")
        # Vérifier si la date est dans la plage
        if date_debut <= date_dispo <= date_fin:
            print("Praticien trouvé dans la plage :\n", card.text)
            # Cliquer sur le bouton "Prochain RDV le ..."
            # On remonte au bouton parent du span
            bouton_rdv = span_rdv.find_element(By.XPATH, "./ancestor::button")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", bouton_rdv)
            time.sleep(1)
            bouton_rdv.click()
            time.sleep(1)
            trouve = True
    except Exception as e:
        continue  # Si pas de date ou format inattendu, on passe à la card suivante

if not trouve:
    print("Aucun praticien avec un RDV dans la plage demandée.")

# Parcours de toutes les cards praticiens de la page
cards = driver.find_elements(By.CSS_SELECTOR, "div.dl-card.dl-card-bg-white.dl-card-variant-shadow-3")

for card in cards:
    try:
        # Chercher le bouton "Voir plus de créneaux" dans la card
        voir_plus_btn = card.find_element(By.XPATH, ".//button[span[contains(text(), 'Voir plus de créneaux')]]")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", voir_plus_btn)
        time.sleep(0.3)
        voir_plus_btn.click()
        print("Bouton 'Voir plus de créneaux' cliqué pour une card.")
        time.sleep(0.5)
    except (NoSuchElementException, StaleElementReferenceException):
        # Si le bouton n'existe pas ou n'est plus accessible, on ignore cette card
        continue
    except Exception as e:
        print("Erreur lors du clic sur 'Voir plus de créneaux' :", e)
        continue

# total_results = wait.until(EC.presence_of_element_located((
#     By.CSS_SELECTOR,
#     "div[data-test='total-number-of-results']"
# )))
# print("Found results : ", total_results.text)

time.sleep(25)
driver.quit()