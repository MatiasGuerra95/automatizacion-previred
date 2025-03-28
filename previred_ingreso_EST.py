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

# Configuración de logging: se escribe en automatizacion.log con nivel DEBUG para mayor detalle.
LOG_FILE = "automatizacion.log"
logging.basicConfig(
    filename=LOG_FILE,
    filemode="a",
    level=logging.DEBUG,  # Nivel DEBUG para ver todos los mensajes
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def seleccionar_fecha_jquery_ui(driver, fecha_str):
    logging.debug(f"Iniciando función seleccionar_fecha_jquery_ui con fecha: {fecha_str}")
    try:
        fecha = datetime.strptime(fecha_str, "%d-%m-%Y")
        dia = fecha.day
        mes = fecha.month - 1  # Ajuste para jQuery UI (meses en base 0)
        anio = fecha.year
        logging.debug(f"Fecha descompuesta: dia={dia}, mes={mes}, anio={anio}")
    except Exception as e:
        logging.error("Error al parsear la fecha: " + str(e))
        raise

    try:
        select_year_elem = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//select[@class='ui-datepicker-year']"))
        )
        Select(select_year_elem).select_by_value(str(anio))
        logging.debug("Año seleccionado: " + str(anio))
    except Exception as e:
        logging.error("Error al seleccionar el año: " + str(e))
        raise

    try:
        select_month_elem = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//select[@class='ui-datepicker-month']"))
        )
        Select(select_month_elem).select_by_value(str(mes))
        logging.debug("Mes seleccionado: " + str(mes))
    except Exception as e:
        logging.error("Error al seleccionar el mes: " + str(e))
        raise

    time.sleep(1)
    
    try:
        day_xpath = (
            f"//table[@class='ui-datepicker-calendar']"
            f"//td[@data-handler='selectDay' and @data-month='{mes}' and @data-year='{anio}']/a[text()='{dia}']"
        )
        logging.debug("XPath para seleccionar el día: " + day_xpath)
        day_elem = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, day_xpath))
        )
        day_elem.click()
        logging.debug("Día seleccionado: " + str(dia))
    except Exception as e:
        logging.error("Error al seleccionar el día: " + str(e))
        raise

    time.sleep(1)

def configurar_firefox():
    try:
        profile = FirefoxProfile()
        descarga_dir = "descarga"
        os.makedirs(descarga_dir, exist_ok=True)
        logging.debug(f"Directorio de descargas configurado: {descarga_dir}")

        profile.set_preference("browser.download.folderList", 2)
        profile.set_preference("browser.download.dir", descarga_dir)
        profile.set_preference("browser.download.useDownloadDir", True)
        profile.set_preference("browser.download.manager.showWhenStarting", False)
        profile.set_preference("pdfjs.disabled", True)
        profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf,application/octet-stream")
        logging.debug("Preferencias de descarga configuradas.")

        firefox_options = FirefoxOptions()
        firefox_options.add_argument("--headless")
        firefox_options.profile = profile
        firefox_options.set_preference("dom.webdriver.enabled", False)
        firefox_options.set_preference("useAutomationExtension", False)
        logging.debug("Opciones de Firefox configuradas en modo headless.")

        service = FirefoxService(GeckoDriverManager().install(), timeout=300)
        driver = webdriver.Firefox(service=service, options=firefox_options)
        logging.info("Driver de Firefox iniciado exitosamente.")
        return driver
    except Exception as e:
        logging.error("Error al configurar Firefox: " + str(e))
        raise

def login_previred(driver, user, password):
    try:
        logging.info("Accediendo a la página de login de Previred...")
        driver.get("https://www.previred.com/wPortal/login/login.jsp")
        driver.maximize_window()
        logging.debug("Página de login cargada y ventana maximizada.")

        logging.info("Realizando login en Previred...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "web_rut2"))
        ).send_keys(user)
        driver.find_element(By.ID, "web_password").send_keys(password)
        driver.find_element(By.ID, "login").click()
        logging.info("Botón de login clickeado, esperando confirmación...")
        time.sleep(3)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "empresa"))
        )
        logging.info("Login exitoso. Se detectó la sección 'empresa'.")
    except Exception as e:
        logging.error("Error durante el login: " + str(e))
        driver.quit()
        raise

def seleccionar_empresa(driver):
    try:
        logging.info("Accediendo a la sección 'Empresas'...")
        driver.find_element(By.ID, "empresa").click()
        logging.info("Sección 'Empresas' abierta.")

        logging.info("Seleccionando la empresa '76.333.204-7'...")
        empresa_xpath = "//tr[td[contains(text(),'76.333.204-7')]]//button[@class='ingresar']"
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, empresa_xpath))
        ).click()
        logging.info("Empresa MVS SpA seleccionada.")
    except Exception as e:
        logging.error("Error al seleccionar la empresa: " + str(e))
        driver.quit()
        raise

def acceder_movimiento_personal(driver):
    try:
        logging.info("Accediendo a Movimiento de Personal Retroactivo...")
        mov_personal_xpath = "//div[@class='modulo movPersonal']//button[contains(@id,'regulariza')]"
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, mov_personal_xpath))
        ).click()
        logging.info("Movimiento de Personal Retroactivo accedido.")
        time.sleep(2)

        logging.info("Entrando a 'Ingreso Manual'...")
        ingreso_manual_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "regularizacion_manual"))
        )
        ingreso_manual_btn.click()
        logging.info("'Ingreso Manual' clickeado.")
        time.sleep(3)
    except Exception as e:
        logging.error("Error al acceder a Movimiento de Personal Retroactivo: " + str(e))
        driver.quit()
        raise

def procesar_registro(driver, reg, idx, total):
    try:
        folio_id = reg.get("id", "NOID")
        rut = reg["rut"]
        fecha_str = reg["fecha_ultimo_dia"]  # dd-mm-yyyy
        logging.info(f"Registro {idx+1}/{total}: RUT: {rut}, Fecha Hasta: {fecha_str}, ID: {folio_id}")
    except Exception as e:
        logging.error("Error al leer el registro del JSON: " + str(e))
        return

    try:
        logging.debug("Ingresando RUT en el formulario...")
        rut_input = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "web_rut_trabajador2"))
        )
        rut_input.clear()
        rut_input.send_keys(rut.replace(".", ""))
        rut_input.send_keys(Keys.TAB)
        logging.info("RUT ingresado correctamente.")
        time.sleep(1)
    except Exception as e:
        logging.error(f"Error al ingresar el RUT para el registro {folio_id}: " + str(e))
        return

    try:
        logging.debug("Seleccionando sistema de salud 'FONASA'...")
        salud_select_elem = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "web_combo_codigo_salud"))
        )
        Select(salud_select_elem).select_by_visible_text("FONASA")
        logging.info("Sistema de salud seleccionado: FONASA.")
    except Exception as e:
        logging.error(f"Error al seleccionar el sistema de salud para el registro {folio_id}: " + str(e))
        return

    try:
        logging.debug("Seleccionando causa de movimiento 'Retiro (Cese trabajador)'...")
        movimiento_select_elem = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "web_combo_movimiento_personal"))
        )
        Select(movimiento_select_elem).select_by_visible_text("Retiro (Cese trabajador)")
        logging.info("Causa de movimiento seleccionada: Retiro (Cese trabajador).")
    except Exception as e:
        logging.error(f"Error al seleccionar la causa de movimiento para el registro {folio_id}: " + str(e))
        return

    try:
        logging.debug("Haciendo click en el campo 'Fecha Hasta'...")
        end_date_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "end_date"))
        )
        end_date_input.click()
        logging.info("Campo 'Fecha Hasta' clickeado.")
        time.sleep(1)
    except Exception as e:
        logging.error(f"Error al hacer click en 'Fecha Hasta' para el registro {folio_id}: " + str(e))
        return

    try:
        logging.debug("Seleccionando fecha utilizando el datepicker...")
        seleccionar_fecha_jquery_ui(driver, fecha_str)
        logging.info("Fecha seleccionada correctamente: " + fecha_str)
    except Exception as e:
        logging.error(f"Error al seleccionar la fecha para el registro {folio_id}: " + str(e))
        return

    try:
        logging.debug("Buscando el botón 'Continuar' (primer click)...")
        continuar_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "continuar"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", continuar_btn)
        time.sleep(1)
        try:
            continuar_btn.click()
            logging.info("Botón 'Continuar' clickeado (acción normal).")
        except Exception as e:
            logging.warning(f"Error al hacer click en 'Continuar', intentando con JavaScript: {str(e)}")
            driver.execute_script("arguments[0].click();", continuar_btn)
            logging.info("Botón 'Continuar' clickeado (acción JS).")
        time.sleep(3)
    except Exception as e:
        logging.error(f"Error al interactuar con el botón 'Continuar' para el registro {folio_id}: " + str(e))
        return

    try:
        logging.debug("Buscando checkbox de declaración...")
        chk_declaracion = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "web_chk_declaracion"))
        )
        chk_declaracion.click()
        logging.info("Checkbox de declaración seleccionado.")
    except Exception as e:
        logging.error(f"Error al hacer click en el checkbox de declaración para el registro {folio_id}: " + str(e))
        return

    try:
        logging.debug("Buscando el segundo botón 'Continuar'...")
        continuar2 = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "continuar"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", continuar2)
        continuar2.click()
        logging.info("Segundo botón 'Continuar' clickeado.")
        time.sleep(2)
    except Exception as e:
        logging.error(f"Error al hacer click en el segundo botón 'Continuar' para el registro {folio_id}: " + str(e))
        return

    try:
        logging.debug("Buscando botón 'Imprimir' para descargar el PDF...")
        imprimir_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a/span[@id='imprimir']"))
        )
        imprimir_link.click()
        logging.info("Botón 'Imprimir' clickeado, descarga iniciada.")
        time.sleep(3)
    except Exception as e:
        logging.error(f"Error al hacer click en 'Imprimir' para el registro {folio_id}: " + str(e))
        return

    try:
        logging.debug("Esperando 5 segundos para que la descarga finalice...")
        time.sleep(5)
    except Exception as e:
        logging.error(f"Error durante la espera de descarga para el registro {folio_id}: " + str(e))
        return

    try:
        logging.debug("Renombrando el PDF descargado...")
        nombre_descargado = "CtrlPdf.pdf"  # Ajusta al nombre real si es necesario
        ruta_original = os.path.join("descarga", nombre_descargado)
        ruta_nueva = os.path.join("descarga", f"{folio_id}.pdf")
        if os.path.exists(ruta_original):
            os.rename(ruta_original, ruta_nueva)
            logging.info(f"PDF renombrado a: {ruta_nueva}")
        else:
            logging.warning(f"No se encontró {ruta_original} para renombrar para el registro {folio_id}.")
    except Exception as e:
        logging.error(f"Error al renombrar el PDF para el registro {folio_id}: " + str(e))
        return

    try:
        logging.debug("Buscando el botón 'Continuar' final para volver a 'Ingreso Manual'...")
        continuar_final = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "continuar"))
        )
        continuar_final.click()
        logging.info("Botón 'Continuar' final clickeado.")
    except Exception as e:
        logging.warning(f"Error al hacer click en el botón 'Continuar' final para el registro {folio_id}: " + str(e))
        try:
            driver.back()
            logging.info("Ejecutado fallback: driver.back()")
        except Exception as ex:
            logging.error("Error al ejecutar fallback para el botón 'Continuar' final: " + str(ex))
        time.sleep(3)

    try:
        logging.debug("Buscando botón 'Ingreso Manual' para continuar con el siguiente registro...")
        ingreso_manual_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "regularizacion_manual"))
        )
        ingreso_manual_btn.click()
        logging.info("Botón 'Ingreso Manual' clickeado para el siguiente registro.")
        time.sleep(3)
    except Exception as e:
        logging.warning(f"Error al hacer click en 'Ingreso Manual' para el siguiente registro: " + str(e))
        return

def main():
    logging.info("Inicio de previred_ingreso_EST.py")
    load_dotenv()
    previred_user = os.getenv("PREVIRED_USER")
    previred_pass = os.getenv("PREVIRED_PASS")
    logging.debug("Variables de entorno cargadas: PREVIRED_USER y PREVIRED_PASS.")

    # 1) Cargar el JSON
    try:
        with open("finiquitos_filtrados_EST.json", "r", encoding="utf-8") as f:
            registros = json.load(f)
        logging.info(f"JSON cargado con {len(registros)} registros.")
    except Exception as e:
        logging.error("Error al cargar el archivo JSON: " + str(e))
        return

    # 2) Configurar Firefox para descargas automáticas de PDF
    try:
        driver = configurar_firefox()
    except Exception as e:
        logging.error("Error al configurar el driver de Firefox: " + str(e))
        return

    try:
        login_previred(driver, previred_user, previred_pass)
        seleccionar_empresa(driver)
        acceder_movimiento_personal(driver)

        # Procesar cada registro del JSON
        for idx, reg in enumerate(registros):
            procesar_registro(driver, reg, idx, len(registros))

        logging.info("Proceso de subida completado para todos los registros.")
    except Exception as e:
        logging.error("Error general en previred_ingreso_EST.py: " + str(e))
        logging.error(traceback.format_exc())
        print("Error:", e)
    finally:
        driver.quit()
        logging.info("Driver cerrado y script finalizado.")

if __name__ == "__main__":
    main()
