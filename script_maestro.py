import os
import subprocess
import logging
import datetime
import shutil

previred_user = os.environ["PREVIRED_USER"]
previred_pass = os.environ["PREVIRED_PASS"]
sigo_user = os.environ["SIGO_USER"]
sigo_pass = os.environ["SIGO_PASS"]

descarga_dir = "/home/matias/Previred/descarga"
os.makedirs(descarga_dir, exist_ok=True)

LOG_FILE = "automatizacion.log"
logging.basicConfig(
    filename=LOG_FILE,
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logging.info("Borrando PDF antiguos antes de iniciar ...")
for f in os.listdir(descarga_dir):
    if f.lower().endswith(".pdf"):
        os.remove(os.path.join(descarga_dir, f))

def run_script(script_path):
    """
    Ejecuta un script de Python y loguea el resultado.
    """
    logging.info(f"Iniciando: {script_path}")
    try:
        subprocess.check_call(["python", script_path])
        logging.info(f"Finalizado con éxito: {script_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error en {script_path}: {str(e)}")


def main():
    logging.info("==== INICIO AUTOMATIZACION ====")

    # Asesorias
    run_script("sigo_login_Asesorias.py")       # Genera finiquitos_filtrados_Asesorias.json
    run_script("previred_ingreso_Asesorias.py") # Descarga PDFs
    run_script("sigo_upload_Asesorias.py")      # Sube PDFs

    # Business
    run_script("sigo_login_Business.py")       # Genera finiquitos_filtrados_Business.json
    run_script("previred_ingreso_Business.py") # Descarga PDFs
    run_script("sigo_upload_Business.py")      # Sube PDFs

    # EST
    run_script("sigo_login_EST.py")       # Genera finiquitos_filtrados_EST.json
    run_script("previred_ingreso_EST.py") # Descarga PDFs
    run_script("sigo_upload_EST.py")      # Sube PDFs

    logging.info("==== FIN AUTOMATIZACION ====")

if __name__ == "__main__":
    main()
