import os
import time
import json
import logging
import traceback
from datetime import date
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.service import Service as EdgeService

# Para esperas explícitas
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuración de logging
LOG_FILE = "sigo_finiquitos.log"
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
    
    # Iniciar Edge con webdriver_manager
    edge_service = EdgeService(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=edge_service)
    
    try:
        # 1. Acceder a SIGO y maximizar
        driver.get("http://34.56.196.212/MVS_SIGO/")
        driver.maximize_window()
        logging.info("Accediendo a SIGO...")
        
        # --- LOGIN ---
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "user"))
        ).send_keys(usuario)
        driver.find_element(By.ID, "pass").send_keys(contraseña)
        driver.find_element(By.ID, "btnLogn").click()
        time.sleep(3)
        
        # --- Navegar a 'Solicitud de finiquitos' ---
        logging.info("Navegando hacia 'Solicitud de finiquitos'...")
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Solicitud de finiquitos"))
        ).click()
        time.sleep(3)
        
        # ================================
        # SECCIÓN: SUBIR ARCHIVOS A SIGO
        # ================================
        descarga_dir = "/home/matias/Previred/descarga"  # Carpeta donde se encuentran los PDFs
        registros_file = "finiquitos_filtrados_Business.json"
        
        with open(registros_file, "r", encoding="utf-8") as f:
            lista_resultados = json.load(f)
        
        logging.info(f"Se encontraron {len(lista_resultados)} registros en {registros_file}.")
        
        for reg in lista_resultados:
            record_id = reg["id"]
            logging.info(f"Procesando subida para ID: {record_id}")
            
            # 0) Asegurarse de que el campo de filtro (filtro_id) esté visible.
            # Si no lo está, intentar hacer click en "label_id" o forzar su visualización.
            try:
                filtro_input = driver.find_element(By.ID, "filtro_id")
                if not filtro_input.is_displayed():
                    try:
                        label = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.ID, "label_id"))
                        )
                        label.click()
                        logging.info("Se hizo click en 'label_id' para mostrar el filtro.")
                    except Exception:
                        # Forzar visualización usando JavaScript
                        driver.execute_script("document.getElementById('label_id').style.display = 'block';")
                        time.sleep(1)
                        label = driver.find_element(By.ID, "label_id")
                        label.click()
                        logging.info("Forzado click en 'label_id' via JS para mostrar el filtro.")
                    time.sleep(1)
            except Exception as e:
                logging.warning(f"No se pudo verificar la visibilidad del filtro: {str(e)}")
            
            # 1) Ingresar el número de ID en el campo de filtro
            filtro_input = WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((By.ID, "filtro_id"))
            )
            try:
                filtro_input.clear()
            except Exception:
                driver.execute_script("arguments[0].value = '';", filtro_input)
            time.sleep(1)
            filtro_input.send_keys(record_id)
            logging.info(f"Ingresado ID {record_id} en el filtro.")
            
            # 2) Esperar a que aparezca la celda con ese ID en la tabla
            try:
                cell = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, f"//table//td[text()='{record_id}']"))
                )
                logging.info(f"Registro con ID {record_id} visible en la tabla.")
            except Exception as e:
                logging.warning(f"El registro con ID {record_id} no apareció en la tabla. Se omite este registro.")
                continue
            time.sleep(2)
            
            # 2.1) Hacer clic en la fila (o la celda) que contiene el ID
            row_element = cell.find_element(By.XPATH, "./..")
            row_element.click()
            logging.info(f"Clic en la fila del ID {record_id}.")
            time.sleep(2)
            
            # 3) Ubicar el input para subir archivo (id="notificacion_afc")
            upload_input = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "notificacion_afc"))
            )
            file_path = os.path.join(descarga_dir, f"{record_id}.pdf")
            if os.path.exists(file_path):
                upload_input.send_keys(file_path)
                logging.info(f"Archivo {file_path} subido para ID {record_id}.")
            else:
                logging.warning(f"Archivo {file_path} no encontrado para ID {record_id}. Se omite este registro.")
                continue
            
            # 4) Clic en "GUARDAR" (id="btnguarda")
            try:
                guardar_btn = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.ID, "btnguarda"))
                )
                guardar_btn.click()
                logging.info(f"Clic en 'Guardar' para ID {record_id}.")
                time.sleep(2)
            except Exception as e:
                logging.warning(f"No se encontró el botón 'Guardar' (btnguarda). {str(e)}")
            
            # 5) Clic en "Avanzar a calculo" (id="btnrgt2")
            avanzar_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, "btnrgt2"))
            )
            avanzar_btn.click()
            logging.info(f"Clic en 'Avanzar a calculo' para ID {record_id}.")
            time.sleep(5)  # Espera a que se procese la subida
            
            # 6) Limpiar el campo de filtro para el siguiente registro
            filtro_input = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "filtro_id"))
            )
            try:
                filtro_input.clear()
            except Exception:
                driver.execute_script("arguments[0].value = '';", filtro_input)
            time.sleep(2)
        
        logging.info("Proceso de subida completado para todos los registros.")
        
    except Exception as e:
        logging.error(f"Ocurrió un error en el script: {str(e)}\n{traceback.format_exc()}")
        print(f"Error: {e}")
    finally:
        driver.quit()
        logging.info("Script finalizado.")

if __name__ == "__main__":
    main()
