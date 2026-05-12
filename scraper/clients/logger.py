import logging
import sys

def setup_logger(name='scraper', level=logging.INFO):
    """
    Configurar logger con handler de consola
    
    Args:
        name: Nombre del logger
        level: Nivel de logging
        
    Returns:
        Instancia de logger configurada
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Evitar duplicar handlers si ya existe
    if logger.handlers:
        return logger
    
    # Formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger
