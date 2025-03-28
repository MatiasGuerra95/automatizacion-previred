import os
import time
import json
import logging
import traceback
from datetime import datetime, date
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
# Para esperas explícitas
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Definimos el nombre del archivo de log
LOG_FILE = "automatizacion.log"

# Configuración de logging con modo 'append'
logging.basicConfig(
    filename=LOG_FILE,
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def main():
    load_dotenv()
    usuario = os.getenv("SIGO_USER")
    contraseña = os.getenv("SIGO_PASS")
    
    # 1) FECHA LÍMITE = HOY (automático)
    fecha_limite = date.today()
    
    edge_service = EdgeService(EdgeChromiumDriverManager().install())
    edge_options = EdgeOptions()
    edge_options.add_argument("--headless")
    driver = webdriver.Edge(service=edge_service, options=edge_options)
    
    try:
        driver.get("http://34.56.196.212/MVS_SIGO/")
        driver.maximize_window()
        
        # --- LOGIN ---
        logging.info("Iniciando sesión en SIGO...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "user"))
        ).send_keys(usuario)
        driver.find_element(By.ID, "pass").send_keys(contraseña)
        
        driver.find_element(By.ID, "btnLogn").click()
        time.sleep(3)

        logging.info("Navegando hacia 'Solicitud de finiquitos'...")
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Solicitud de finiquitos"))
        ).click()
        time.sleep(3)

        # ─────────────────────────────────────────────────────────────────────
        # 3️⃣ Seleccionar la empresa en el dropdown
        # ─────────────────────────────────────────────────────────────────────
        try:
            empresa_label = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "label_cliente"))
            )
            empresa_label.click()
            logging.info("📌 Se hizo clic en 'EMPRESA CONTRATANTE'.")

            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "input_cliente"))
            )

            input_cliente = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "input_cliente"))
            )
            input_cliente.click()
            time.sleep(2)

            empresa_opcion_xpath = "//ul[contains(@class, 'dropdown-content')]/li/span[text()='Asesorías e Inversiones MV Services S.A.']"

            try:
                empresa_opcion = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, empresa_opcion_xpath))
                )
                empresa_opcion.click()
            except:
                logging.warning("⚠ Intentando seleccionar Empresa usando JavaScript...")
                driver.execute_script(
                    f"document.evaluate(\"{empresa_opcion_xpath}\", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click();"
                )

            logging.info("✅ Empresa seleccionada correctamente.")

        except Exception as e:
            screenshot_path = os.path.join(os.getcwd(), "error_empresa.png")
            driver.save_screenshot(screenshot_path)
            error_details = traceback.format_exc()
            logging.error(f"❌ Error al seleccionar empresa: {str(e)}\n{error_details}")

        # ─────────────────────────────────────────────────────────────────────
        # 4️⃣ Seleccionar el Estado
        # ─────────────────────────────────────────────────────────────────────
        try:
            estado_label = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "label_estado"))
            )
            estado_label.click()
            logging.info("✅ Se hizo clic en 'ESTADO'.")

            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "input_estado"))
            )

            input_estado = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "input_estado"))
            )
            input_estado.click()
            logging.info("✅ Se hizo clic en input_estado.")

            # Puedes cambiar a "Solicitado" u otro estado deseado
            estado_opcion_xpath = "//ul[contains(@class, 'dropdown-content')]/li/span[text()='Solicitado']"
            try:
                estado_opcion = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, estado_opcion_xpath))
                )
                estado_opcion.click()
            except:
                driver.execute_script(
                    f"document.evaluate(\"{estado_opcion_xpath}\", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click();"
                )

            time.sleep(2)
            logging.info("✅ Estado seleccionado correctamente.")
            
        except Exception as e:
            screenshot_path = os.path.join(os.getcwd(), "error_estado.png")
            driver.save_screenshot(screenshot_path)
            error_details = traceback.format_exc()
            logging.error(f"❌ Error al seleccionar Estado: {str(e)}\n{error_details}")

        # ─────────────────────────────────────────────────────────────────────
        #  ✅ Click 2 veces en FECHA ULTIMO DIA para ordenar
        # ─────────────────────────────────────────────────────────────────────
        try:
            th_fecha = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//th[contains(text(), 'FECHA ULTIMO DIA')]"))
            )
            # Primer click
            th_fecha.click()
            time.sleep(1)
            # Segundo click
            th_fecha.click()
            time.sleep(1)
            logging.info("📌 Se ordenó por FECHA ULTIMO DIA correctamente (doble clic).")
        except Exception as e:
            logging.warning(f"⚠ No se pudo hacer doble clic en la columna FECHA ULTIMO DIA: {str(e)}")

        # ─────────────────────────────────────────────────────────────────────
        # 5️⃣ LEER LA TABLA Y GUARDAR DATOS (con logs de fecha)
        # ─────────────────────────────────────────────────────────────────────
        logging.info(f"Fecha límite (hoy) en el sistema: {fecha_limite}")
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

        lista_resultados = []
        
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) < 12:
                continue  # Evita filas no válidas (encabezados, etc.)
            
            id_str = cols[1].text.strip()
            rut = cols[2].text.strip()
            empresa = cols[8].text.strip()
            fecha_ultimo_dia_str = cols[11].text.strip()  # Formato "dd-mm-yyyy"
            
            # Loguear la cadena original
            logging.info(f"RUT: {rut}, Empresa: {empresa}, Fecha texto: {fecha_ultimo_dia_str}")
            
            # Convertir fecha a datetime para comparar
            try:
                fecha_ultimo_dia = datetime.strptime(fecha_ultimo_dia_str, "%d-%m-%Y").date()
                logging.info(f"Fecha parseada: {fecha_ultimo_dia}, comparándola con: {fecha_limite}")
            except ValueError:
                logging.warning(f"No se pudo parsear la fecha: {fecha_ultimo_dia_str}")
                continue
            
            # Verificar si la fecha es <= fecha_limite (hoy)
            if fecha_ultimo_dia <= fecha_limite:
                lista_resultados.append({
                    "id": id_str,
                    "rut": rut,
                    "empresa": empresa,
                    "fecha_ultimo_dia": fecha_ultimo_dia_str
                })
                logging.info(" => Registro ACEPTADO (fecha <= límite).")
            else:
                logging.info(" => Registro DESCARTADO (fecha > límite).")
        
        # --- GUARDAR EN ARCHIVO JSON ---
        with open("finiquitos_filtrados_Asesorias.json", "w", encoding="utf-8") as f:
            json.dump(lista_resultados, f, indent=4, ensure_ascii=False)
        
        logging.info(f"Se guardó el archivo JSON con {len(lista_resultados)} registros filtrados.")
        
    except Exception as e:
        print(f"Ocurrió un error general en el script: {e}")
        logging.error(f"Error general en el script: {str(e)}")
    finally:
        # Si deseas cerrar el navegador al finalizar, descomenta la línea
        # driver.quit()
        logging.info("Script finalizado.")

if __name__ == "__main__":
    main()
