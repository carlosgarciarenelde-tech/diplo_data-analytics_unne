"""
LOAD — Quality checks y persistencia   *** PARCIALMENTE RESUELTO ***
=====================================================================

Dos responsabilidades, en este orden:

  1. CHEQUEAR: validar el dataset antes de publicarlo. Si algo crítico
     falla, cortamos: mejor no entregar nada que entregar un reporte roto.
  2. GUARDAR: escribir el CSV (para personas), el resumen JSON (para
     programas) y el log (para auditar).

Te dejamos resuelto el guardado del CSV y dos de los quality checks.
Faltan 4 TODOs (9 a 12), todos cortos.

Idempotencia: el CSV y el JSON van en modo "w", así que correr el pipeline
dos veces deja el mismo resultado. El log va en modo "a" porque un log ES
un historial: ahí sí queremos que crezca.
"""

import csv
import json
import logging
import os
from datetime import datetime

import config
from transform import COLUMNAS


# ======================================================================
# QUALITY CHECKS
# ======================================================================
def chequear_cantidad(filas, minimo=None):
    """¿Tenemos todas las filas que esperábamos?  [RESUELTO — de ejemplo]

    Fijate el patrón: devuelve una tupla (bool, mensaje). Todos los
    checks tienen que devolver lo mismo para que validar() los trate igual.
    """
    if minimo is None:
        minimo = config.MINIMO_FILAS_ESPERADAS
    ok = len(filas) >= minimo
    return ok, f"cantidad: {len(filas)} filas (mínimo esperado {minimo})"


def chequear_columnas(filas):
    """¿Todas las filas tienen exactamente las columnas del contrato?
    [RESUELTO — de ejemplo]
    """
    esperadas = set(COLUMNAS)
    for fila in filas:
        if set(fila.keys()) != esperadas:
            faltan = esperadas - set(fila.keys())
            return False, f"columnas: una fila no cumple el esquema (faltan {faltan})"
    return True, f"columnas: las {len(COLUMNAS)} del contrato en todas las filas"


def chequear_unicidad(filas):
    """¿Hay duplicados? La clave del dataset es (provincia, anio, destino).

    Debe devolver (bool, mensaje), igual que los checks de arriba.
    """
    claves = [(f.get("provincia"), f.get("anio"), f.get("destino")) for f in filas]
    es_unico = len(claves) == len(set(claves))
    if es_unico:
        return True, "unicidad: no hay claves (provincia, año, destino) duplicadas"
    return False, "unicidad: se encontraron claves duplicadas"
    # ---------------------------------------------------------------------


def chequear_rangos(filas):
    """¿Los valores son plausibles?

    Debe devolver (bool, mensaje).
    """
    for f in filas:
        anio = f.get("anio")
        val = f.get("valor_musd")
        if anio is not None and not (1990 <= anio <= 2030):
            return False, f"rangos: año fuera de rango esperado ({anio})"
        if val is not None and val < 0:
            return False, f"rangos: valor_musd negativo ({val})"
    return True, "rangos: años y montos dentro de rangos plausibles"
    # ---------------------------------------------------------------------


def chequear_cobertura(filas):
    """Advertencia (no crítica): ¿cuántos nulos quedaron en las derivadas?
    [RESUELTO]
    """
    sin_variacion = sum(1 for f in filas if f["var_interanual_pct"] is None)
    sin_rubro = sum(1 for f in filas if f["rubro_principal"] is None)
    ok = sin_rubro == 0
    return ok, (f"cobertura: {sin_variacion} filas sin variación interanual "
                f"(esperable en el primer año), {sin_rubro} sin rubro")


def validar(filas):
    """Corre todos los checks.  [RESUELTO]

    Los CRÍTICOS cortan el pipeline lanzando una excepción ("fallar
    temprano y ruidosamente"). La cobertura solo deja una advertencia.

    Retorna una lista de dicts con el detalle, para el resumen JSON.
    """
    criticos = [
        chequear_cantidad(filas),
        chequear_columnas(filas),
        chequear_unicidad(filas),
        chequear_rangos(filas),
    ]

    detalle = []
    for ok, mensaje in criticos:
        detalle.append({"check": mensaje, "estado": "OK" if ok else "FALLO"})
        if ok:
            logging.info("  check OK    | %s", mensaje)
        else:
            logging.error("  check FALLO | %s", mensaje)
            raise ValueError(f"Quality check crítico falló -> {mensaje}")

    ok, mensaje = chequear_cobertura(filas)
    detalle.append({"check": mensaje, "estado": "OK" if ok else "AVISO"})
    if ok:
        logging.info("  check OK    | %s", mensaje)
    else:
        logging.warning("  check AVISO | %s", mensaje)

    return detalle


# ======================================================================
# PERSISTENCIA
# ======================================================================
def guardar_csv(filas, carpeta=None, nombre=None):
    """Escribe el dataset final. Modo 'w': cada corrida lo reemplaza.
    [RESUELTO — usalo de modelo para el resto]
    """
    carpeta = carpeta or config.DIR_PROCESSED
    nombre = nombre or config.ARCHIVO_SALIDA_CSV
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre)

    with open(ruta, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS)
        escritor.writeheader()
        escritor.writerows(filas)

    logging.info("  CSV: %s (%s filas)", ruta, len(filas))
    return ruta


def construir_resumen(filas, detalle):
    """Arma el diccionario con metadatos y estadísticas para resumen.json."""
    anios = [f.get("anio") for f in filas if f.get("anio") is not None]
    valores = [f.get("valor_musd") for f in filas if f.get("valor_musd") is not None]
    provincias = sorted(list(set(f.get("provincia") for f in filas if f.get("provincia"))))
    destinos = sorted(list(set(f.get("destino") for f in filas if f.get("destino"))))

    resumen = {
        "fuente": "INDEC - Comercio Exterior",
        "periodo": {
            "desde": min(anios) if anios else None,
            "hasta": max(anios) if anios else None,
        },
        "cantidad_filas": len(filas),
        "provincias": provincias,
        "destinos": destinos,
        "estadisticas": {
            "total_musd": round(sum(valores), 2) if valores else 0.0,
            "promedio_anual_musd": round(sum(valores) / len(anios), 2) if anios else 0.0,
        },
        "quality_checks": detalle,
    }
    return resumen
    # ---------------------------------------------------------------------


def guardar_resumen(resumen, ruta=None):
    """Guarda el diccionario de resumen en formato JSON."""
    if ruta is None:
        ruta = os.path.join("data", "processed", "resumen.json")

    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)
    # ---------------------------------------------------------------------


def escribir_log_corrida(resumen, carpeta=None, nombre=None):
    """Registra la ejecución en el archivo pipeline.log en modo append."""
    if carpeta is None:
        carpeta = "logs"
    if nombre is None:
        nombre = "pipeline.log"

    os.makedirs(carpeta, exist_ok=True)
    ruta_log = os.path.join(carpeta, nombre)

    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filas = resumen.get("cantidad_filas", 0)
    checks_ok = sum(1 for c in resumen.get("quality_checks", []) if c.get("ok"))
    total_checks = len(resumen.get("quality_checks", []))

    linea = f"[{ahora}] INFO: Pipeline ejecutado exitosamente. Filas procesadas: {filas}. Checks: {checks_ok}/{total_checks} OK\n"

    with open(ruta_log, "a", encoding="utf-8") as f:
        f.write(linea)
    # ---------------------------------------------------------------------


def cargar(filas):
    """CONTRATO: recibe las filas finales; valida y persiste las 3 salidas.
    [RESUELTO]
    """
    logging.info("LOAD: validando")
    detalle = validar(filas)

    logging.info("LOAD: guardando")
    guardar_csv(filas)
    resumen = construir_resumen(filas, detalle)
    guardar_resumen(resumen)
    escribir_log_corrida(resumen)

    logging.info("LOAD OK")
    return resumen
