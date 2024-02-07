import asyncio
from pyppeteer import launch
import tkinter as tk
from tkinter import filedialog

async def main():
    try:
        browser = await launch()
        page = await browser.newPage()
        file_path = select_html_file()
        if not file_path:
            print("No se ha seleccionado ningún archivo. Saliendo.")
            return

        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        await page.setContent(html_content)
        target_text = input("Ingrese el texto a buscar: ")
        links = await page.querySelectorAll('a')
        for link in links:
            text_content = await page.evaluate('(element) => element.textContent', link)
            if target_text in text_content:
                print(f"Texto encontrado en la etiqueta <a>: {text_content}")
                await link.click()
                await page.screenshot({'path': 'captura_despues_clic.png'})
                print("Captura de pantalla después del clic guardada.")
                break

        if target_text in html_content:
            print(f"Texto encontrado en el HTML general: {target_text}")

    except Exception as e:
        print(f"Error durante la ejecución: {e}")

    finally:
        await browser.close()

def select_html_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("HTML files", "*.html")])
    return file_path

asyncio.get_event_loop().run_until_complete(main())
