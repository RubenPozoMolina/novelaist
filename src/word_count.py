import sys
import os
import logging

# Configure logging for the script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("word_count")

def count_words(file_path):
    """
    Cuenta el número de palabras en un archivo de texto.
    """
    if not os.path.exists(file_path):
        logger.error(f"El archivo '{file_path}' no existe.")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            words = content.split()
            return len(words)
    except Exception as e:
        logger.error(f"Error al leer el archivo: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        logger.info("Uso: python src/word_count.py <ruta_del_fichero>")
    else:
        file_path = sys.argv[1]
        count = count_words(file_path)
        if count is not None:
            logger.info(f"El archivo '{file_path}' tiene {count} palabras.")
