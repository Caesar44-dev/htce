import asyncio
import os
import tkinter as tk
from tkinter import filedialog
from pyppeteer import launch
from img2pdf import convert
from PIL import Image


async def main():
    browser = None
    try:
        browser = await launch()

        page = await browser.newPage()

        file_path = select_html_file()

        if not file_path:
            print("No se ha seleccionado ningún archivo. Saliendo.")
            return

        with open(file_path, "r", encoding="utf-8") as file:
            html_content = file.read()

        await page.setContent(html_content)

        num_captures = int(
            input("Ingrese el número de capturas para la pantalla completa: ")
        )
        target_text = input("Ingrese el texto a buscar y hacer clic: ")
        links = await page.querySelectorAll("a")
        for link in links:
            text_content = await page.evaluate("(element) => element.textContent", link)
            if target_text in text_content:
                print(f"Texto encontrado en la etiqueta <a>: {text_content}")
                await link.click()
                original_paths, compressed_paths = await capture_and_compress(
                    page, target_text, num_captures
                )
                pdf_output_path = f"{target_text}.pdf"
                await convert_images_to_pdf(compressed_paths, pdf_output_path)
                print(f"PDF guardado en: {pdf_output_path}")
                remove_captures(original_paths + compressed_paths)
                print("Capturas de pantalla y archivos temporales eliminados.")
                break

    except Exception as e:
        print(f"Error durante la ejecución: {e}")

    finally:
        if browser:
            await browser.close()
            print("Navegador cerrado.")


async def capture_and_compress(
    page, output_file, num_captures, image_quality=50, image_format="JPEG"
):
    await asyncio.sleep(5)
    await page.waitForSelector("html")
    htmlHandle = await page.querySelector("html")
    htmlHeight = await page.evaluate("(html) => html.scrollHeight", htmlHandle)
    await page.setViewport({"width": 2000, "height": htmlHeight})

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
        await page.setViewport(
            {"width": 2000, "height": slice_height, "deviceScaleFactor": 2}
        )
        await page.evaluate("window.scrollTo(0, {})".format(y_offset))
        await page.waitFor(500)
        capture_path = f"{output_file}_{i}.jpeg"
        await page.screenshot({"path": capture_path})
        captures.append(capture_path)

    compressed_paths = []
    for capture_path in captures:
        compressed_path = f"{os.path.splitext(capture_path)[0]}_compressed.jpeg"
        await compress_image(
            capture_path, compressed_path, quality=image_quality, format=image_format
        )
        compressed_paths.append(compressed_path)

    return captures, compressed_paths


async def compress_image(input_path, output_path, quality, format):
    with Image.open(input_path) as img:
        rgb_img = img.convert("RGB")
        rgb_img.save(output_path, format=format, quality=quality)


async def convert_images_to_pdf(image_paths, output_pdf_path):
    with open(output_pdf_path, "wb") as pdf_file:
        pdf_file.write(convert(image_paths))


def remove_captures(capture_paths):
    for path in capture_paths:
        try:
            os.remove(path)
            print(f"Archivo eliminado: {path}")
        except FileNotFoundError:
            print(f"El archivo no existe: {path}")
        except Exception as e:
            print(f"Error al eliminar el archivo {path}: {e}")


def select_html_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Seleccione un archivo HTML", filetypes=[("HTML files", "*.html")]
    )
    return file_path


asyncio.get_event_loop().run_until_complete(main())
