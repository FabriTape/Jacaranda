"""
NIST ASD API integration service.
Fetches discrete atomic emission line data from NIST ASD via astroquery for direct comparison.
Robustly parses formatted strings with symbols (e.g., '380.16215+', '30*', '30hl').
"""

import numpy as np
import astropy.units as u
from astroquery.nist import Nist
import uncertainties as un


def _clean_float(val):
    """
    Convierte una celda de astropy/numpy (que puede contener símbolos como '+', '*', 'hl')
    a un número float válido.
    """
    if val is None or np.ma.is_masked(val):
        return None
    s = str(val).strip()
    if not s:
        return None
    
    # Extraer caracteres numéricos, punto decimal o signo negativo
    clean_s = ''.join(c for c in s if c.isdigit() or c in '.-')
    if clean_s:
        try:
            return float(clean_s)
        except ValueError:
            return None
    return None


def query_nist_spectrum(especie="H I", wl_min=380.0, wl_max=750.0):
    """
    Consulta líneas de emisión en NIST ASD y devuelve la lista discreta de líneas.
    
    Retorna un diccionario con:
    - especie: str
    - wl_min, wl_max: float
    - wavelengths: np.array de floats [nm]
    - intensities: np.array de floats (normalizados 0..100)
    - lambdas_ufloat: np.array de ufloats (con incertidumbre estimada en NIST de ~0.05 nm)
    """
    try:
        tabla = Nist.query(float(wl_min) * u.nm, float(wl_max) * u.nm, linename=str(especie))
    except Exception as e:
        raise RuntimeError(f"Error consultando NIST ASD: {str(e)}")
        
    if tabla is None or len(tabla) == 0:
        raise ValueError(f"No se encontraron líneas para '{especie}' en el rango [{wl_min}, {wl_max}] nm.")

    wavelengths = []
    intensities = []

    for row in tabla:
        # Prioridad Observed -> Ritz (limpiando símbolos astrofísicos de NIST)
        wl_obs = _clean_float(row['Observed']) if 'Observed' in row.colnames else None
        wl_ritz = _clean_float(row['Ritz']) if 'Ritz' in row.colnames else None
        
        wl_val = wl_obs if wl_obs is not None else wl_ritz
        rel_int = _clean_float(row['Rel.']) if 'Rel.' in row.colnames else None
        
        # Si la intensidad no está especificada, asignar valor por defecto 1.0
        if rel_int is None:
            rel_int = 1.0
            
        if wl_val is not None and wl_val > 0:
            wavelengths.append(wl_val)
            intensities.append(rel_int)

    wavelengths = np.array(wavelengths)
    intensities = np.array(intensities)

    if len(intensities) == 0:
        raise ValueError(f"No se pudieron extraer líneas válidas de NIST para '{especie}'.")

    # Normalización a 100
    max_i = np.max(intensities)
    if max_i > 0:
        intensities = (intensities / max_i) * 100.0

    # Ordenar por longitud de onda ascendente
    sort_idx = np.argsort(wavelengths)
    wavelengths = wavelengths[sort_idx]
    intensities = intensities[sort_idx]

    # Crear arreglo ufloats con error predeterminado de 0.05 nm
    lambdas_ufloat = np.array([un.ufloat(wl, 0.05) for wl in wavelengths])

    return {
        "especie": especie,
        "wl_min": wl_min,
        "wl_max": wl_max,
        "wavelengths": wavelengths,
        "intensities": intensities,
        "lambdas_ufloat": lambdas_ufloat
    }
