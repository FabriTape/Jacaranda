"""
Physics calculations for spectrometry and emission line analysis.
Preserves mathematical models from notebook Emision_abs.ipynb.
Adds residual analysis and linear regression calibration diagnostics for systematic error detection.
"""

import numpy as np
import uncertainties as un
from uncertainties import unumpy
from uncertainties.unumpy import sin as unsine
import pandas as pd


def split_redondeado(x):
    """
    Formatea valores ufloat redondeando el error a 1 cifra significativa.
    """
    x_clean = [un.ufloat(val.n, val.s) for val in x]
    return np.array([f"{v:.1u}" for v in x_clean])


def lam(titos, error_angulo, tito_0, d, m):
    """
    Calcula longitudes de onda [nm] a partir de ángulos medidos.
    """
    titos_arr = np.array(titos, dtype=float)
    tito0_arr = np.array(tito_0, dtype=float)
    
    diferencia = np.abs(titos_arr - tito0_arr)
    diferencia_total = diferencia[:, 0] + (diferencia[:, 1] + diferencia[:, 2] / 60.0) / 60.0
    
    diferencia_total_rad = np.array([
        un.ufloat(i, error_angulo / 3600.0) for i in diferencia_total
    ]) * np.pi / 180.0
    
    valores = (d / m) * unsine(diferencia_total_rad)
    err_max = np.max(unumpy.std_devs(valores))
    return np.array([un.ufloat(v.n, err_max) for v in valores])


def ang2lam(np_ang, np_meta):
    """
    Transforma matriz de ángulos y metadatos a longitudes de onda.
    """
    n = float(np_meta[4, 0])  # Rendijas por mm
    d = un.ufloat(1000000.0 / n, 10000.0 / n)
    tito_0 = np_meta[1, :]
    error_angulo = float(np_meta[2][0])
    m = int(np_meta[5, 0])
    
    lambdas = lam(np_ang[:, 0:3], error_angulo, tito_0, d, m)
    lambdas_str = split_redondeado(lambdas)
    df_lambdas = pd.DataFrame(lambdas_str, columns=["(Lambda +/- Error) nm"])
    return df_lambdas, lambdas


def proy_cos(a, b):
    """
    Calcula la proyección del coseno entre dos vectores ufloat.
    """
    return np.dot(a, b) / un.umath_core.sqrt(np.dot(a, a) * np.dot(b, b))


def cos_prod(a, b, delta):
    """
    Calcula la distancia cuadrática entre a+delta y b para una grilla de deltas.
    """
    x = []
    for i in delta:
        va = a + i
        dif = va - b
        x.append(np.sum([j**2 for j in dif])**(1/2))
    return np.array([un.ufloat(val.n, val.s) for val in x])


def find(arr, val, x):
    """
    Busca la posición en x donde arr coincide con val.
    """
    arr_nom = np.array([v.n if hasattr(v, 'n') else v for v in arr])
    val_nom = val.n if hasattr(val, 'n') else val
    
    for i, v in enumerate(arr_nom):
        if v == val_nom:
            return x[i]
        elif i > 0 and (v - val_nom) * (arr_nom[i - 1] - val_nom) < 0:
            return x[i]
    return x[0]


def match_closest_lines(lambdas_med, lambdas_ref, max_tol_nm=15.0):
    """
    Empareja cada línea medida con la línea de referencia más cercana dentro de una tolerancia.
    Retorna arrays emparejados (med_matched, ref_matched).
    """
    med_nom = np.array([v.n if hasattr(v, 'n') else float(v) for v in lambdas_med])
    ref_nom = np.array([v.n if hasattr(v, 'n') else float(v) for v in lambdas_ref])
    
    matched_med = []
    matched_ref = []
    
    for i, m_val in enumerate(med_nom):
        diffs = np.abs(ref_nom - m_val)
        min_idx = np.argmin(diffs)
        if diffs[min_idx] <= max_tol_nm:
            matched_med.append(lambdas_med[i])
            matched_ref.append(lambdas_ref[min_idx])
            
    return np.array(matched_med), np.array(matched_ref)


def proy(lambdas_med_np, lambdas_tab_np):
    """
    Calcula el desplazamiento por mínimos cuadrados (búsqueda de mínima distancia).
    """
    # Si las dimensiones difieren, emparejar líneas más cercanas
    if len(lambdas_med_np) != len(lambdas_tab_np):
        lambdas_med_np, lambdas_tab_np = match_closest_lines(lambdas_med_np, lambdas_tab_np)
        
    x = np.linspace(-30, 30, 90)
    u = cos_prod(lambdas_med_np, lambdas_tab_np, x)
    u_nom = np.array([v.n for v in u])
    
    min_idx = np.argmin(u_nom)
    uu = u[min_idx]
    
    x_min = find(u, uu, x)
    x_min_del = find(u, uu.n + uu.s, x)
    val_x = un.ufloat(x_min, abs(x_min - x_min_del))
    return val_x


def lam2ang(lam_val):
    """
    Convierte desplazamiento en nm a minutos de arco angular.
    """
    d = un.ufloat(10000.0 / 3.0, 100.0 / 3.0)
    return unumpy.arcsin(lam_val / d) * 180.0 * 60.0 / np.pi


def linear_regression_residuals(lambdas_med_np, lambdas_ref_np):
    """
    Diagnóstico científico avanzado de error sistemático:
    1. Regresión Lineal: lambda_med = a + b * lambda_ref
       - Intercepto a: Error constante de cero angular (nm)
       - Pendiente b: Error de escala / dispersión de rendija (ideal = 1.0)
    2. Residuos: delta_lambda_i = lambda_med_i - lambda_ref_i
    """
    med_matched, ref_matched = match_closest_lines(lambdas_med_np, lambdas_ref_np)
    
    y = np.array([v.n for v in med_matched])
    x = np.array([v.n for v in ref_matched])
    
    if len(x) < 2:
        return None
        
    # Regresión lineal por mínimos cuadrados
    slope, intercept = np.polyfit(x, y, 1)
    
    # Coeficiente de determinación R^2
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred)**2)
    ss_tot = np.sum((y - np.mean(y))**2)
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0
    
    residuals = y - x
    
    return {
        "x_ref": x,
        "y_med": y,
        "matched_med": med_matched,
        "matched_ref": ref_matched,
        "slope": slope,
        "intercept": intercept,
        "r_squared": r_squared,
        "residuals": residuals,
        "mean_residual": np.mean(residuals),
        "std_residual": np.std(residuals, ddof=1) if len(residuals) > 1 else 0.0
    }


def error_sist_calc(lambdas_med_np, lambdas_tab_np):
    """
    Ejecuta el análisis completo de error sistemático.
    Acepta arreglos de diferente longitud emparejando por proximidad.
    """
    med_m, tab_m = match_closest_lines(lambdas_med_np, lambdas_tab_np)
    
    if len(med_m) == 0:
        raise ValueError("No se encontraron coincidencias de líneas dentro de la tolerancia aceptable.")
        
    mean_proy = -np.mean(med_m - tab_m)
    mean_proy = un.ufloat(mean_proy.n, mean_proy.s)
    
    val_x = proy(med_m, tab_m)
    
    a_shifted = np.array([un.ufloat(v.n, v.s) for v in (med_m + val_x)])
    
    cos_a = proy_cos(a_shifted, tab_m)
    cos_orig = proy_cos(med_m, tab_m)
    
    # Diagnóstico avanzado de regresión y residuos
    diag = linear_regression_residuals(lambdas_med_np, lambdas_tab_np)
    
    return {
        "val_x": val_x,
        "val_x_ang": lam2ang(val_x),
        "mean_proy": mean_proy,
        "mean_proy_ang": lam2ang(mean_proy),
        "cos_a": cos_a,
        "cos_orig": cos_orig,
        "a_shifted": a_shifted,
        "lambdas_matched_med": med_m,
        "lambdas_matched_tab": tab_m,
        "diagnostic": diag
    }


def wavelength_to_rgb(wavelength, gamma=0.8):
    """
    Convierte longitud de onda (nm) a tupla RGB (r, g, b) para graficación continua.
    """
    wl = float(wavelength)
    if wl < 380 or wl > 750:
        return (0.0, 0.0, 0.0)
    if wl < 440:
        r = -(wl - 440) / (440 - 380)
        g = 0.0
        b = 1.0
    elif wl < 490:
        r = 0.0
        g = (wl - 440) / (490 - 440)
        b = 1.0
    elif wl < 510:
        r = 0.0
        g = 1.0
        b = -(wl - 510) / (510 - 490)
    elif wl < 580:
        r = (wl - 510) / (580 - 510)
        g = 1.0
        b = 0.0
    elif wl < 645:
        r = 1.0
        g = -(wl - 645) / (645 - 580)
        b = 0.0
    else:
        r = 1.0
        g = 0.0
        b = 0.0
        
    if wl < 420:
        factor = 0.3 + 0.7 * (wl - 380) / (420 - 380)
    elif wl > 645:
        factor = 0.3 + 0.7 * (750 - wl) / (750 - 645)
    else:
        factor = 1.0
        
    r = (r * factor) ** gamma
    g = (g * factor) ** gamma
    b = (b * factor) ** gamma
    return (max(0, r), max(0, g), max(0, b))
