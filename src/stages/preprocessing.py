import pandas as pd
import boto3
import os
from src.utils import load_config
import os
import logging
import sys
import argparse
import re
import numpy as np

logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger("preprocessing")


def main(config_path):
    config = load_config(config_path)
    input_path = config['concatenation']['output_path']
    input_filename = input_path + "/" + config['concatenation']['output_filename']
    data = pd.read_csv(input_filename,index_col=0)
    final_data = data.pipe(process_general).pipe(get_info_from_name).pipe(process_yamaha).pipe(final_filter)
    final_data.to_csv(config['preprocessing']['output_file'])
    return final_data

def process_yamaha(data):
    reemplazos_modelos = {
        'Nmax': 'N-Max',
        'N-max': 'N-Max',
        'N': 'N-Max',
        'Bws': 'BWS',
        'Bwis': 'BWS',
        'Xmax': 'X-Max',
        'X-max': 'X-Max',
        'X': 'X-Max',
        'Super': 'Super-Tenere'
    }
    cilindradas = {
        'N-Max': 155,
        'Fz-25': 250,
        'Fz-2.0': 150,
        'R3': 320,
        'Aerox': 155,
        'X-Max': 300,
        'Ycz': 110,
        'Super-Tenere': 1200,
        'R1': 1000,
        'Tracer': 900
    }
    
    # Filtrar solo los vehículos Yamaha
    yamaha = data[data['vehicle_make'] == 'Yamaha'].copy()
    
    # Aplicar reemplazos de nombres de modelos
    yamaha['vehicle_line'] = yamaha['vehicle_line'].replace(reemplazos_modelos)
    
    # Actualizar cilindradas solo donde hay NA
    for modelo, cilindraje in cilindradas.items():
        mask = (yamaha['vehicle_line'] == modelo) & (yamaha['cilindraje'].isna())
        yamaha.loc[mask, 'cilindraje'] = cilindraje
    
    return yamaha

def process_general(data):
    # Diccionario con todos los reemplazos necesarios
    reemplazos = {
        'Royal Enfield': 'Royal-Enfield',
        'Harley Davidson': 'Harley-Davidson',
        'Mt 15': 'Mt-15',
        'Mt15': 'Mt-15',
        'Mt 09': 'Mt-09',
        'Mt09': 'Mt-09',
        'Mt 07': 'Mt-07',
        'Mt 03': 'Mt-03',
        'Mt03': 'Mt-03',
        'Fz 25': 'Fz-25',
        'Fz 2.5': 'Fz-25',
        'Fz 2.0': 'Fz-2.0',
        'Fz 16': 'Fz-16',
        'Fz25': 'Fz-25'
    }
    data['product'] = data['product'].replace(reemplazos)
    data['cilindraje'] = extraer_cilindraje(data['product'])
    return data

def get_info_from_name(data):
    product_serie = data['product'].str.split(' ')
    data['vehicle_make'] = product_serie.str[0].str.strip()
    data['vehicle_line'] = product_serie.str[1].str.strip()
    data['version'] = product_serie.str[2].str.strip()
    return data


def extraer_cilindraje(descripciones):
    """
    Extrae el cilindraje (CC) de una lista de descripciones de motocicletas.

    Args:
        descripciones (list): Lista de descripciones de motocicletas.

    Returns:
        list: Lista de cilindrajes extraídos como enteros.
    """
    cilindrajes = []
    for descripcion in descripciones:
        # Buscar un número de 2 a 4 dígitos seguido de "cc" o aislado, evitando años comunes (1900-2024)
        matches = re.findall(r'\b(?:[a-zA-Z]*)(\d{2,4})(?:[a-zA-Z]*)(?:\s?cc)?\b', descripcion, re.IGNORECASE)
        
        if matches:
            # Convertir los resultados a enteros
            posibles_cilindrajes = [int(m) for m in matches if not (int(m) < 100 or int(m) >= 1900)]
            if posibles_cilindrajes:
                # Si hay candidatos válidos, tomar el primero
                cilindrajes.append(posibles_cilindrajes[0])
            else:
                # Si todos los números encontrados parecen ser años, devolver None
                cilindrajes.append(None)
        else:
            cilindrajes.append(None)  # En caso de no encontrar ningún número
    return cilindrajes

def final_filter(data):
    lineas = data['vehicle_line'].value_counts()
    linead_filter = lineas[lineas>10].index
    data  = data[(data['vehicle_line'].isin(linead_filter)) & (data['vehicle_line']!='') & (data['cilindraje'].notna()) & (data['kilometraje']>0)]
    return data

if __name__ == "__main__":
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("--config", dest="config", required=True)
    args = args_parser.parse_args()
    final_data = main(args.config)