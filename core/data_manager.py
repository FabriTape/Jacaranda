"""
Data management module for Jacarandá.
Handles scanning, loading, and saving CSV files and metadata for measured and tabulated spectra.
Maintains exact file format compatibility with the original project.
"""

import os
from datetime import datetime
import numpy as np
import pandas as pd
import uncertainties as un
from core.physics import split_redondeado, ang2lam


def list_available_elements(base_dir="."):
    """
    Lista las carpetas de elementos registradas que comienzan con 'Lab_2_'.
    Devuelve lista de nombres de elementos base (ej. 'Kr', 'Hg', 'He', 'Dióxido de carbono', 'Ar').
    """
    folders = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and d.startswith("Lab_2_")]
    elements = set()
    for f in folders:
        clean_name = f.replace("Lab_2_", "").replace("_Tabulado", "")
        if clean_name:
            elements.add(clean_name)
    return sorted(list(elements))


def leer_csv(nombre_folder, tipo, cols=1, base_dir="."):
    """
    Lee archivos CSV dentro de la carpeta especificada según el tipo ('Angulo', 'Lambda', 'Metadatos').
    """
    folder_path = os.path.join(base_dir, nombre_folder)
    if not os.path.exists(folder_path):
        return None
        
    archivos = [f for f in os.listdir(folder_path) if tipo in f and f.endswith(".csv")]
    if not archivos:
        return None
        
    archivo = os.path.join(folder_path, archivos[0])
    try:
        if cols != -1:
            return np.loadtxt(archivo, delimiter=",", skiprows=1, usecols=[i for i in range(1, cols + 1)], dtype=str)
        else:
            return np.loadtxt(archivo, delimiter=",", skiprows=1, dtype=str)
    except Exception as e:
        print(f"Error leyendo {archivo}: {e}")
        return None


def metadatos(tito_0, nombre_elemento, n, m, error_angulo, base_dir="."):
    """
    Guarda el archivo de metadatos con el formato exacto del proyecto original.
    """
    fecha = datetime.now().strftime("%Y,%m,%d")
    fecha_str = datetime.now().strftime("%d-%m-%Y")
    
    tito_0_str = f"{tito_0[0]},{tito_0[1]},{tito_0[2]}"
    
    contenido = (
        ",0,1,2\n"
        f"0,{fecha}\n"
        f"1,{tito_0_str}\n"
        f"2,{error_angulo},,\n"
        f"3,{nombre_elemento},,\n"
        f"4,{n},,\n"
        f"5,{m},,\n"
    )
    
    folder_path = os.path.join(base_dir, nombre_elemento)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        
    archivo_meta = os.path.join(folder_path, f"Metadatos_{nombre_elemento}_{fecha_str}.csv")
    with open(archivo_meta, "w", encoding="utf-8") as f:
        f.write(contenido)


def guardar_csv(matriz, nombre_elemento, columnas, m=0, base_dir="."):
    """
    Guarda matriz NumPy o lista de datos en un CSV con encabezados.
    """
    folder_path = os.path.join(base_dir, nombre_elemento)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        
    if m == 0:  # Ángulos
        nombre_archivo = os.path.join(folder_path, f"{nombre_elemento}_Angulo_Grados.csv")
        df = pd.DataFrame(matriz, columns=columnas)
    else:  # Lambdas
        nombre_archivo = os.path.join(folder_path, f"{nombre_elemento}_Lambda.csv")
        df = pd.DataFrame(matriz, columns=columnas)
        
    df.to_csv(nombre_archivo, index=False)


def load_element_data(element_name, base_dir="."):
    """
    Carga todos los datos disponibles de un elemento:
    - Datos medidos (metadatos, ángulos, lambdas calculados)
    - Datos tabulados (lambdas tabulados)
    
    Retorna un diccionario con DataFrames y ufloat arrays.
    """
    res = {
        "element": element_name,
        "has_measured": False,
        "has_tabulated": False,
        "metadata_raw": None,
        "angles_df": None,
        "lambdas_med_df": None,
        "lambdas_med_ufloat": None,
        "lambdas_tab_df": None,
        "lambdas_tab_ufloat": None,
    }
    
    folder_med = f"Lab_2_{element_name}"
    folder_tab = f"Lab_2_{element_name}_Tabulado"
    
    # 1. Cargar datos medidos
    if os.path.exists(os.path.join(base_dir, folder_med)):
        angulos_np = leer_csv(folder_med, "Angulo", cols=-1, base_dir=base_dir)
        meta_raw = leer_csv(folder_med, "Metadatos", cols=3, base_dir=base_dir)
        
        if angulos_np is not None and meta_raw is not None:
            res["has_measured"] = True
            meta_reshaped = np.reshape(meta_raw, (6, 3))
            res["metadata_raw"] = meta_reshaped
            
            # DataFrame Ángulos
            if angulos_np.ndim == 1:
                angulos_np = np.reshape(angulos_np, (1, -1))
            res["angles_df"] = pd.DataFrame(angulos_np[:, :3], columns=["Grados", "Minutos", "Segundos"])
            
            # DataFrame Lambdas calculados
            df_lambdas_calc, lambdas_med_np = ang2lam(angulos_np, meta_reshaped)
            res["lambdas_med_df"] = df_lambdas_calc
            res["lambdas_med_ufloat"] = lambdas_med_np
            
    # 2. Cargar datos tabulados
    if os.path.exists(os.path.join(base_dir, folder_tab)):
        mask = leer_csv(folder_tab, "Lambda", cols=-1, base_dir=base_dir)
        if mask is not None:
            res["has_tabulated"] = True
            if isinstance(mask, str):
                mask = np.array([mask])
            lam_ufloats = np.array([un.ufloat_fromstr(l) for l in mask.flatten()])
            lambda_tab_str = split_redondeado(lam_ufloats)
            res["lambdas_tab_df"] = pd.DataFrame(lambda_tab_str, columns=["(Lambda +/- Error) nm"])
            res["lambdas_tab_ufloat"] = np.array([un.ufloat_fromstr(l) for l in lambda_tab_str.flatten()])
            
    return res


def save_new_measured_data(element_name, error_angulo, tito_0, n, m, angles_list, base_dir="."):
    """
    Guarda una nueva medición de espectrómetro:
    - angles_list: lista de tuplas/listas [grados, minutos, segundos]
    - Genera carpeta Lab_2_<Element_name>
    - Guarda Ángulos, Metadatos y Lambdas calculados.
    """
    nombre_folder = f"Lab_2_{element_name}"
    angulos_np = np.array(angles_list, dtype=float)
    
    # 1. Guardar ángulos CSV
    guardar_csv(angulos_np, nombre_folder, ["Grados", "Minutos", "Segundos", "error seg/arc°"][:angulos_np.shape[1]], m=0, base_dir=base_dir)
    
    # 2. Guardar metadatos
    metadatos(tito_0, nombre_folder, n, m, error_angulo, base_dir=base_dir)
    
    # 3. Calcular y guardar Lambdas CSV
    d = un.ufloat(1000000.0 / n, 10000.0 / n)
    from core.physics import lam
    lambdas_med = lam(angulos_np, error_angulo, tito_0, d, m)
    lambdas_str = split_redondeado(lambdas_med)
    guardar_csv(lambdas_str, nombre_folder, ["(Lambda +/- Error) nm"], m=-1, base_dir=base_dir)
    
    return nombre_folder


def save_new_tabulated_data(element_name, error_nm, lambda_values, base_dir="."):
    """
    Guarda un nuevo espectro tabulado:
    - lambda_values: lista de floats con las longitudes de onda en nm
    - Genera carpeta Lab_2_<Element_name>_Tabulado
    """
    nombre_folder = f"Lab_2_{element_name}_Tabulado"
    lambdas_ufloats = [un.ufloat(float(l), float(error_nm)) for l in lambda_values]
    lambdas_str = split_redondeado(np.array(lambdas_ufloats))
    guardar_csv(lambdas_str, nombre_folder, ["(Lambda +/- Error) nm"], m=-1, base_dir=base_dir)
    return nombre_folder
