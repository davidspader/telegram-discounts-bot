import time
import asyncio
import pandas as pd
from telegram import Bot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import dotenv_values

config = dotenv_values('.env')

async def main():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920x1080')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    min_discount = config.get('MIN_DISCOUNT')

    driver.get(f'https://www.kabum.com.br/ofertas/cybermonday?pagina=1&desconto_minimo=' + min_discount + '&desconto_maximo=100')

    while(len(driver.find_elements(By.CLASS_NAME, 'nameCard'))) == 0:
        time.sleep(1)

    nameCards = driver.find_elements(By.CLASS_NAME, 'nameCard')
    priceCard = driver.find_elements(By.CLASS_NAME, 'priceCard')
    oldPriceCards = driver.find_elements(By.CLASS_NAME, 'oldPriceCard')
    discountTagCards = driver.find_elements(By.CLASS_NAME, 'discountTagCard')
    productLinks = driver.find_elements(By.CLASS_NAME, 'productLink')

    telegram_token = config.get('TELEGRAM_TOKEN')
    chat_id = config.get('CHAT_ID')

    bot = Bot(token=telegram_token)

    csv_file = 'sent_products.csv'
    try:
        existing_data = pd.read_csv(csv_file)
        sent_products = set(existing_data['Nome'])
    except (FileNotFoundError, KeyError):
        existing_data = pd.DataFrame(columns=['Nome', 'Preço', 'Preço Antigo', 'Desconto', 'Link do Produto'])
        sent_products = set()

    for i in range(len(nameCards)):
        product_name = nameCards[i].text
        if product_name not in sent_products:
            message = f'''
<b>🚨 {product_name.upper()}</b>
<b>Com {discountTagCards[i].text} de desconto:</b>

De: <s>{oldPriceCards[i].text}</s> | Por: <b>{priceCard[i].text}</b>

<b>Link do Produto:</b>
<a href="{productLinks[i].get_attribute('href')}">{product_name}</a>
            '''

            await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')

            new_data = pd.DataFrame({
                'Nome': [product_name],
                'Preço': [priceCard[i].text],
                'Preço Antigo': [oldPriceCards[i].text],
                'Desconto': [discountTagCards[i].text],
                'Link do Produto': [productLinks[i].get_attribute('href')]
            })
            existing_data = pd.concat([existing_data, new_data], ignore_index=True)
            existing_data.to_csv(csv_file, index=False)

if __name__ == "__main__":
    asyncio.run(main())
