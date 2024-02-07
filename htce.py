import asyncio
import os
import tkinter as tk
from tkinter import filedialog
from pyppeteer import launch
from img2pdf import convert
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image

async def capture_full_page(page, output_file, num_captures):
    await asyncio.sleep(5)
    await page.waitForSelector('html')
    htmlHandle = await page.querySelector('html')
    htmlHeight = await page.evaluate('(html) => html.scrollHeight', htmlHandle)
    await page.setViewport({'width': 2000, 'height': htmlHeight})
    
    total_height = htmlHeight
    max_viewport_height = 800

    if total_height < max_viewport_height:
        viewport_height = total_height
    else:
        viewport_height = max_viewport_height

    captures = []
    for i in range(min(num_captures, total_height // viewport_height)):
        y_offset = i * viewport_height
        slice_height = min(viewport_height, total_height - y_offset)
        await page.setViewport({'width': 2000, 'height': slice_height, 'deviceScaleFactor': 2})
        await page.evaluate('window.scrollTo(0, {})'.format(y_offset))
        await page.waitFor(500)
        capture_path = f'{output_file}_{i}.jpeg'
        await page.screenshot({'path': capture_path})
        captures.append(capture_path)

    return captures

def compress_image(input_path, output_path, quality, format):
    with Image.open(input_path) as img:
        rgb_img = img.convert('RGB')
        rgb_img.save(output_path, format=format, quality=quality)

async def compress_images(capture_paths, image_quality=50, image_format='JPEG'):
    compressed_paths = []
    for capture_path in capture_paths:
        compressed_path = f"{os.path.splitext(capture_path)[0]}_compressed.jpeg"
        compress_image(capture_path, compressed_path, quality=image_quality, format=image_format)
        compressed_paths.append(compressed_path)
    return compressed_paths

async def capture_html_to_pdf(html_path, output_pdf_path, num_captures, image_quality=50, image_format='JPEG'):
    browser = await launch(headless=True)
    page = await browser.newPage()
    captures = []
    compressed_paths = []
    
    try:
        await page.goto(f'file://{html_path}')
        captures = await capture_full_page(page, "capture", num_captures)
        
        if not captures:
            print("Error: No se pudo capturar ninguna imagen.")
            return
        
        compressed_paths = await compress_images(captures, image_quality, image_format)

        with open("output.pdf", "wb") as pdf_file:
            pdf_file.write(convert(compressed_paths))
        
        pdf_reader = PdfReader("output.pdf")
        pdf_writer = PdfWriter()
        
        for page_num in range(len(pdf_reader.pages)):
            pdf_writer.add_page(pdf_reader.pages[page_num])
        
        with open(output_pdf_path, "wb") as output_pdf:
            pdf_writer.write(output_pdf)
        
        print(f"PDF guardado y comprimido correctamente en: {output_pdf_path}")

    except Exception as e:
        print(f"Error durante la captura y conversión: {e}")

    finally:
        await browser.close()
        for capture_path, compressed_path in zip(captures, compressed_paths):
            os.remove(capture_path)
            os.remove(compressed_path)
            
        if os.path.exists("output.pdf"):
            os.remove("output.pdf")

def select_html_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("HTML files", "*.html")])
    return file_path

html_file_path = select_html_file()

if html_file_path:
    try:
        num_captures = int(input("Ingrese el número de capturas: "))
        asyncio.get_event_loop().run_until_complete(capture_html_to_pdf(html_file_path, os.path.splitext(os.path.basename(html_file_path))[0] + ".pdf", num_captures))
    except ValueError:
        print("Error: Ingrese un número válido para el número de capturas.")
else:
    print("No se ha seleccionado ningún archivo HTML.")
