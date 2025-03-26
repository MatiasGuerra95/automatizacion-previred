import os
import time
import json
import logging
import traceback
from datetime import datetime
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile

LOG_FILE = "previred_mov_personal.log"
logging.basicConfig(
    filename=LOG_FILE,
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def seleccionar_fecha_jquery_ui(driver, fecha_str):
    """
    Selecciona 'fecha_str' (formato dd-mm-yyyy) en el datepicker jQuery UI que ya está visible.
    """
    fecha = datetime.strptime(fecha_str, "%d-%m-%Y")
    dia = fecha.day
    mes = fecha.month - 1
    anio = fecha.year

    select_year_elem = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//select[@class='ui-datepicker-year']"))
    )
    Select(select_year_elem).select_by_value(str(anio))

    select_month_elem = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//select[@class='ui-datepicker-month']"))
    )
    Select(select_month_elem).select_by_value(str(mes))

    time.sleep(1)
    
    day_xpath = (
        f"//table[@class='ui-datepicker-calendar']"
        f"//td[@data-handler='selectDay' and @data-month='{mes}' and @data-year='{anio}']/a[text()='{dia}']"
    )
    day_elem = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, day_xpath))
    )
    day_elem.click()
    time.sleep(1)

def main():
    load_dotenv()
    previred_user = os.getenv("PREVIRED_USER")
    previred_pass = os.getenv("PREVIRED_PASS")

    # 1) Cargar el JSON
    with open("finiquitos_filtrados_Asesorias.json", "r", encoding="utf-8") as f:
        registros = json.load(f)

    # 2) Configurar Firefox para descargas automáticas de PDF
    profile = FirefoxProfile()
    descarga_dir = "descarga"
    os.makedirs(descarga_dir, exist_ok=True)

    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.dir", descarga_dir)
    profile.set_preference("browser.download.useDownloadDir", True)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("pdfjs.disabled", True)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf,application/octet-stream")

    firefox_options = FirefoxOptions()
    firefox_options.add_argument("--headless")
    firefox_options.profile = profile
    firefox_options.set_preference("dom.webdriver.enabled", False)
    firefox_options.set_preference("useAutomationExtension", False)

    service = FirefoxService(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=firefox_options)

    try:
        # 3) Login Previred
        driver.get("https://www.previred.com/wPortal/login/login.jsp")
        driver.maximize_window()
        logging.info("Accediendo a Previred...")

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "web_rut2"))
        ).send_keys(previred_user)
        driver.find_element(By.ID, "web_password").send_keys(previred_pass)
        driver.find_element(By.ID, "login").click()
        logging.info("Credenciales enviadas...")

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "empresa"))
        )
        logging.info("Inicio de sesión exitoso.")

        # 4) Sección Empresas
        driver.find_element(By.ID, "empresa").click()
        logging.info("Sección 'Empresas' abierta.")

        # 5) Elegir la Empresa
        empresa_xpath = "//tr[td[contains(text(),'76.071.027-K')]]//button[@class='ingresar']"
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, empresa_xpath))
        ).click()
        logging.info("Entrando a Empresa MV Business")

        # 6) Movimiento de Personal Retroactivo
        mov_personal_xpath = "//div[@class='modulo movPersonal']//button[contains(@id,'regulariza')]"
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, mov_personal_xpath))
        ).click()
        logging.info("Accediendo a Movimiento de Personal Retroactivo...")
        time.sleep(2)

        # 7) Ingreso Manual (primera vez)
        ingreso_manual_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "regularizacion_manual"))
        )
        ingreso_manual_btn.click()
        logging.info("Entrando a 'Ingreso Manual'...")
        time.sleep(3)

        # 8) Bucle para todos los registros
        for idx, reg in enumerate(registros):
            folio_id = reg.get("id", "NOID")
            rut = reg["rut"]
            fecha_str = reg["fecha_ultimo_dia"]  # dd-mm-yyyy

            logging.info(f"Procesando RUT: {rut}, Fecha Hasta: {fecha_str}, ID: {folio_id}")

            # a) Ingresar RUT
            rut_input = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, "web_rut_trabajador2"))
            )
            rut_input.clear()
            rut_input.send_keys(rut.replace(".", ""))
            rut_input.send_keys(Keys.TAB)
            time.sleep(1)

            # b) Seleccionar Sistema de Salud
            salud_select_elem = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "web_combo_codigo_salud"))
            )
            Select(salud_select_elem).select_by_visible_text("FONASA")

            # c) Causa de Movimiento
            movimiento_select_elem = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "web_combo_movimiento_personal"))
            )
            Select(movimiento_select_elem).select_by_visible_text("Retiro (Cese trabajador)")

            # d) Fecha Hasta
            end_date_input = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "end_date"))
            )
            end_date_input.click()
            time.sleep(1)
            seleccionar_fecha_jquery_ui(driver, fecha_str)

            # e) Botón Continuar #1
            continuar_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, "continuar"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", continuar_btn)
            time.sleep(1)
            try:
                continuar_btn.click()
            except:
                driver.execute_script("arguments[0].click();", continuar_btn)
            time.sleep(3)

            # f) Checkbox Declaración
            chk_declaracion = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "web_chk_declaracion"))
            )
            chk_declaracion.click()

            # g) Botón Continuar #2
            continuar2 = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "continuar"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", continuar2)
            continuar2.click()
            time.sleep(2)

            # h) Botón Imprimir => descarga PDF
            imprimir_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a/span[@id='imprimir']"))
            )
            imprimir_link.click()
            logging.info("Click en 'Imprimir'.")
            time.sleep(3)

            # Esperar la descarga
            time.sleep(5)

            # Renombrar PDF
            nombre_descargado = "CtrlPdf.pdf"  # Ajusta al nombre real
            ruta_original = os.path.join(descarga_dir, nombre_descargado)
            ruta_nueva = os.path.join(descarga_dir, f"{folio_id}.pdf")

            if os.path.exists(ruta_original):
                os.rename(ruta_original, ruta_nueva)
                logging.info(f"PDF renombrado a: {ruta_nueva}")
            else:
                logging.warning(f"No se encontró {ruta_original} para renombrar.")

            # i) Botón "Continuar" final => vuelve a la pantalla que tiene el botón "Ingreso Manual"
            try:
                continuar_final = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "continuar"))
                )
                continuar_final.click()
            except:
                logging.warning("No se encontró el botón 'Continuar'. Intentando fallback...")
                # Por ejemplo: driver.back() o driver.refresh() o volver a un menú principal
                driver.back()
                time.sleep(3)

            # j) Hacer clic en "Ingreso Manual" de nuevo para el siguiente RUT
            try:
                ingreso_manual_btn = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.ID, "regularizacion_manual"))
                )
                ingreso_manual_btn.click()
                logging.info("Listo para procesar siguiente registro: Ingreso Manual clicado.")
                time.sleep(3)
            except:
                logging.warning("No se encontró el botón 'regularizacion_manual' al volver. Revisar flujo.")

        logging.info("Proceso completado para todos los registros.")

    except Exception as e:
        logging.error(f"Error: {str(e)}\n{traceback.format_exc()}")
        print(f"Error: {e}")
    finally:
        driver.quit()  # Descomenta para cerrar el navegador al terminar
        logging.info("Script finalizado.")

if __name__ == "__main__":
    main()
