from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd

# Demander les entrées à l'utilisateur via le terminal
postal_code = input("Entrez le code postal pour la recherche : ")
start_date = input("Entrez la date de début de disponibilité (JJ/MM/AAAA) : ")
end_date = input("Entrez la date de fin de disponibilité (JJ/MM/AAAA) : ")
speciality = input("Entrez la spécialité médicale (ex: 'dermatologue') : ")
consultation_type = input("Entrez le type de consultation ('sur place' ou 'visio') : ")
price_min = int(input("Entrez le prix minimum (€) : "))
price_max = int(input("Entrez le prix maximum (€) : "))

# Initialisation de Selenium
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.get("https://www.doctolib.fr/")
wait = WebDriverWait(driver, 20)

# Remplir le champ de recherche avec le code postal
place_input = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "input.searchbar-input.searchbar-place-input"))
)
place_input.clear()
place_input.send_keys(postal_code)
place_input.send_keys(Keys.ENTER)

# Remplir les autres filtres avec les entrées du terminal
start_date_input = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='start_date']"))
)
start_date_input.clear()
start_date_input.send_keys(start_date)

end_date_input = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='end_date']"))
)
end_date_input.clear()
end_date_input.send_keys(end_date)

search_query_input = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='speciality']"))
)
search_query_input.clear()
search_query_input.send_keys(speciality)
search_query_input.send_keys(Keys.ENTER)

# Type de consultation
consultation_type_input = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='consultation_type']"))
)
consultation_type_input.clear()
consultation_type_input.send_keys(consultation_type)

# Plage de prix
min_price_input = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='price_min']"))
)
min_price_input.clear()
min_price_input.send_keys(str(price_min))

max_price_input = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='price_max']"))
)
max_price_input.clear()
max_price_input.send_keys(str(price_max))

# Lancer la recherche après avoir rempli les filtres
search_query_input.send_keys(Keys.ENTER)

# Extraire les résultats des praticiens
practitioners = wait.until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.practitioner-card"))
)

# Collecter les données des praticiens
data = []
for practitioner in practitioners:
    name = practitioner.find_element(By.CSS_SELECTOR, "h2.practitioner-name").text
    availability = practitioner.find_element(By.CSS_SELECTOR, "div.availability").text
    consultation_type = practitioner.find_element(By.CSS_SELECTOR, "span.consultation-type").text
    insurance_sector = practitioner.find_element(By.CSS_SELECTOR, "span.insurance-sector").text
    price = practitioner.find_element(By.CSS_SELECTOR, "span.price").text
    address = practitioner.find_element(By.CSS_SELECTOR, "div.address").text
    
    data.append([name, availability, consultation_type, insurance_sector, price, address])

# Sauvegarder les données dans un fichier CSV
df = pd.DataFrame(data, columns=["Nom", "Disponibilité", "Type de consultation", "Secteur d'assurance", "Prix", "Adresse"])
df.to_csv("praticiens.csv", index=False)

# Fermer le navigateur
driver.quit()