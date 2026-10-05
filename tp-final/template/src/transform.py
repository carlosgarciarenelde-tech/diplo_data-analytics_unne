"""
TRANSFORM — De datos crudos a un dataset analítico   *** ACÁ TRABAJÁS VOS ***
=============================================================================

Este es el corazón del TP. El Extract ya te trae los datos y el Load ya
sabe guardarlos: lo que falta es convertir lo crudo en algo analizable.

El recorrido es:

    formato ANCHO (como llega de la API)
        fecha        China   Brasil   ...   __TOTAL__
        1993-01-01    12.3     45.6   ...      120.0

              |  ancho_a_largo()          <- TODO 1
              v

    formato LARGO / "tidy" (una fila por observación)
        anio  provincia  destino  valor_musd  total_provincia_musd
        1993  Chaco      China          12.3                 120.0
        1993  Chaco      Brasil         45.6                 120.0

              |  + columnas derivadas     <- TODO 2, 3, 4, 5, 6
              |  + join con rubros        <- TODO 7, 8
              v

    dataset final de 13 columnas

CÓMO TRABAJAR
-------------
Hay 8 TODOs numerados. Hacelos EN ORDEN: cada uno usa el anterior.
Después de cada TODO corré los tests para ver si vas bien:

    python tests/test_transform.py

Las funciones ya tienen su docstring con el CONTRATO (qué recibe, qué
devuelve). Respetalo: el resto del pipeline cuenta con eso.
"""

import logging

import config

# Nombre reservado que usa extract.py para la serie del total provincial
CLAVE_TOTAL = "__TOTAL__"

# Orden final de las columnas del CSV. Es un contrato: el Load lo respeta
# y la consigna del TP lo exige. NO lo modifiques.
COLUMNAS = [
    "anio",
    "provincia",
    "destino",
    "region_destino",
    "valor_musd",
    "total_provincia_musd",
    "participacion_pct",
    "var_interanual_pct",
    "decada",
    "ranking_destino",
    "es_top3",
    "rubro_principal",
    "pp_participacion_pct",
]


# ======================================================================
# 1) ANCHO -> LARGO
# ======================================================================
def extraer_anio(fecha_texto):
    """Convierte '1993-01-01' en el entero 1993.

    Esta te la dejamos resuelta como ejemplo del estilo que esperamos:
    una función corta, con nombre de verbo y un solo trabajo.
    """
    return int(fecha_texto[:4])


def ancho_a_largo(paquetes_destino):
    """CONTRATO: recibe los paquetes crudos de destino; devuelve una lista
    de dicts con una fila por (año, provincia, destino).

    Cada dict debe tener exactamente estas 5 claves:
        anio                  (int)
        provincia             (str)
        destino               (str)
        valor_musd            (float, redondeado a 2 decimales)
        total_provincia_musd  (float, redondeado a 2 decimales)

    Cada paquete tiene esta forma:
        {
          "provincia": "Chaco",
          "orden_columnas": ["China", "Brasil", ..., "__TOTAL__"],
          "data": [["1993-01-01", 12.3, 45.6, ..., 120.0], ...]
        }

    En cada fila de 'data', el elemento 0 es la fecha y los siguientes
    son los valores, EN EL MISMO ORDEN que 'orden_columnas'.

    Ojo con tres cosas:
      - La columna CLAVE_TOTAL no es un destino: no genera fila propia,
        pero su valor va en 'total_provincia_musd' de todas las filas
        de ese año.
      - Si un valor es None, salteá esa observación (patrón 'continue').
      - Redondeá los valores a 2 decimales con round().
    """
    filas = []

def ancho_a_largo(paquetes_destino):
    filas = []

    for paquete in paquetes_destino:
        provincia = paquete["provincia"]
        columnas = paquete["orden_columns"] if "orden_columns" in paquete else paquete["orden_columnas"]
        indice_total = columnas.index(CLAVE_TOTAL)

        for fila_cruda in paquete["data"]:
            fecha = fila_cruda[0]
            anio = extraer_anio(fecha)
            valores = fila_cruda[1:]

            total_provincia = valores[indice_total]
            if total_provincia is None:
                continue
            total_provincia_musd = round(float(total_provincia), 2)

            for destino, valor in zip(columnas, valores):
                if destino == CLAVE_TOTAL or valor is None:
                    continue

                filas.append({
                    "anio": anio,
                    "provincia": provincia,
                    "destino": destino,
                    "valor_musd": round(float(valor), 2),
                    "total_provincia_musd": total_provincia_musd,
                })

    logging.info("  ancho_a_largo: %s filas", len(filas))
    return filas


# ======================================================================
# 2) COLUMNAS DERIVADAS SIMPLES
# ======================================================================
def clasificar_region(destino):
    """Devuelve la región geoeconómica de un país de destino.

    Ejemplos:  'Brasil' -> 'Mercosur'   |   'China' -> 'Asia'

    El mapeo está en config.REGIONES. Si el país NO está en el
    diccionario, devolvé config.REGION_POR_DEFECTO en lugar de romper.
    """
    # TODO 2 --------------------------------------------------------------
    # Una sola línea. Pista: el método .get() de los diccionarios acepta
    # un segundo argumento con el valor por defecto (lo viste en la Clase 3).
    return config.REGIONES.get(destino, config.REGION_POR_DEFECTO)
    # ---------------------------------------------------------------------


def calcular_decada(anio):
    """Devuelve la década de un año como texto.

    Ejemplos:  1993 -> '1990s'   |   2024 -> '2020s'
    """
    # TODO 3 --------------------------------------------------------------
    # Pista: la división entera // te da el inicio de la década.
    #        ¿Cuánto vale (1993 // 10) * 10 ?
    #        Después armá el texto con una f-string.
    decada_inicio = (anio // 10) * 10
    return f"{decada_inicio}s"
    # ---------------------------------------------------------------------


def calcular_participacion(valor, total):
    """Qué porcentaje del total exportado representa este destino.

    Ejemplo:  valor=110.93, total=401.74  ->  27.61

    Devolvé None si el total es cero o None: dividir por cero rompe el
    programa, y un dato ausente es más honesto que un cero inventado.
    Redondeá a 2 decimales.
    """
    # TODO 4 --------------------------------------------------------------
    if total is None or total == 0:
        return None
    porcentaje = (valor / total) * 100
    return round(porcentaje, 2)
    # ---------------------------------------------------------------------


def agregar_derivadas_simples(filas):
    """Agrega region_destino, decada y participacion_pct a cada fila.

    CONTRATO: modifica y devuelve la misma lista de filas.
    """
    for fila in filas:
        fila["region_destino"] = clasificar_region(fila["destino"])
        fila["decada"] = calcular_decada(fila["anio"])
        fila["participacion_pct"] = calcular_participacion(
            fila["valor_musd"], fila["total_provincia_musd"]
        )
    return filas


# ======================================================================
# 3) VARIACIÓN INTERANUAL
# ======================================================================
def calcular_variacion(actual, anterior):
    """Variación porcentual entre dos valores.

    Fórmula:  (actual - anterior) / anterior * 100
    Ejemplo:  actual=110.93, anterior=75.79  ->  46.36

    Devolvé None si 'anterior' es None o cero. Redondeá a 2 decimales.
    """
    # TODO 5 --------------------------------------------------------------
    if anterior is None or anterior == 0:
        return None
    variacion = ((actual - anterior) / anterior) * 100
    return round(variacion, 2)
    # ---------------------------------------------------------------------


def agregar_variacion_interanual(filas):
    """Calcula la variación porcentual respecto al año anterior para cada (provincia, destino)."""
    agrupado = {}
    for f in filas:
        clave = (f.get("provincia"), f.get("destino"))
        agrupado.setdefault(clave, []).append(f)

    for serie in agrupado.values():
        serie.sort(key=lambda x: x.get("anio", 0))
        valores_por_anio = {f.get("anio"): f.get("valor_musd") for f in serie}

        for f in serie:
            anio_actual = f.get("anio")
            val_actual = f.get("valor_musd")
            val_previo = valores_por_anio.get(anio_actual - 1)

            if val_previo is not None and val_previo > 0 and val_actual is not None:
                f["variacion_interanual_pct"] = round(((val_actual - val_previo) / val_previo) * 100, 2)
            else:
                f["variacion_interanual_pct"] = None

    return filas
    # ---------------------------------------------------------------------


# ======================================================================
# 4) RANKING DE DESTINOS
# ======================================================================
def agregar_ranking(filas, top_n=None):
    """Agrega ranking_destino (1 = el que más exportó) y es_top3 (bool).

    El ranking se calcula DENTRO de cada grupo (provincia, año): ser el
    destino #1 de Chaco en 2024 no dice nada sobre Misiones en 1998.

    CONTRATO: modifica y devuelve la misma lista de filas.
    """
    if top_n is None:
        top_n = config.TOP_N

    # TODO 7 --------------------------------------------------------------
    # Estrategia sugerida:
    #   1. Agrupá las filas en un dict cuya clave sea (provincia, anio).
    #      Pista: dict.setdefault(clave, []).append(fila)
    #   2. Para cada grupo, ordenalo por valor_musd de mayor a menor:
    #      sorted(grupo, key=lambda f: f["valor_musd"], reverse=True)
    #   3. Recorré el grupo ordenado con enumerate(..., start=1) y asigná
    #      'ranking_destino' y 'es_top3' (un booleano: posición <= top_n).
    grupos = {}
    for f in filas:
        clave = (f["provincia"], f["anio"])
        grupos.setdefault(clave, []).append(f)

    for clave, grupo in grupos.items():
        grupo_ordenado = sorted(grupo, key=lambda f: f["valor_musd"], reverse=True)
        for posicion, f in enumerate(grupo_ordenado, start=1):
            f["ranking_destino"] = posicion
            f["es_top3"] = posicion <= top_n

    return filas
    # ---------------------------------------------------------------------


# ======================================================================
# 5) JOIN CON LOS RUBROS
# ======================================================================
def construir_indice_rubros(paquetes_rubro):
    """CONTRATO: recibe los paquetes crudos de rubro; devuelve un índice."""
    indice = {}

    for paquete in paquetes_rubro:
        prov = paquete.get("provincia")
        columnas = paquete.get("orden_columnas", [])
        filas_data = paquete.get("data", [])

        for fila in filas_data:
            fecha_str = str(fila[0])
            anio = int(fecha_str.split("-")[0])

            valores = {}
            for col_nombre, val in zip(columnas, fila[1:]):
                if val is not None:
                    valores[col_nombre] = float(val)

            if not valores:
                continue

            total = sum(valores.values())
            rubro_ppal = max(valores, key=valores.get)
            pp_val = valores.get("Productos primarios", 0.0)
            pp_pct = round((pp_val / total) * 100, 2) if total > 0 else None

            indice[(prov, anio)] = {
                "rubro_principal": rubro_ppal,
                "pp_participacion_pct": pp_pct,
            }

    logging.info("  índice de rubros: %s claves (provincia, año)", len(indice))
    return indice

def unir_con_rubros(filas, indice_rubros):
    """Join por clave compuesta (provincia, anio).

    Debe ser un LEFT JOIN: si una combinación no está en el índice, las
    dos columnas quedan en None, pero LA FILA NO SE PIERDE.
    """
    for f in filas:
        clave = (f.get("provincia"), f.get("anio"))
        datos_rubro = indice_rubros.get(clave)

        if datos_rubro is not None:
            f["rubro_principal"] = datos_rubro.get("rubro_principal")
            f["pp_participacion_pct"] = datos_rubro.get("pp_participacion_pct")
        else:
            f["rubro_principal"] = None
            f["pp_participacion_pct"] = None

    return filas
    # ---------------------------------------------------------------------


# ======================================================================
# ORQUESTACIÓN DEL TRANSFORM  (ya resuelta: no hace falta tocarla)
# ======================================================================
def ordenar_columnas(filas):
    """Devuelve las filas con las claves en el orden definido por COLUMNAS."""
    return [{columna: fila.get(columna) for columna in COLUMNAS} for fila in filas]


def transformar(datos_crudos):
    """CONTRATO: recibe {'destino': [...], 'rubro': [...]} crudos;
    devuelve la lista de filas finales, ordenadas y con las 13 columnas.

    Fijate cómo esta función 'directora' solo llama a las otras en orden.
    Eso es diseño modular: si mañana cambia una regla, tocás una función.
    """
    logging.info("TRANSFORM: iniciando")

    filas = ancho_a_largo(datos_crudos["destino"])
    filas = agregar_derivadas_simples(filas)
    filas = agregar_variacion_interanual(filas)
    filas = agregar_ranking(filas)

    indice = construir_indice_rubros(datos_crudos["rubro"])
    filas = unir_con_rubros(filas, indice)

    filas.sort(key=lambda f: (f["provincia"], f["anio"], f["ranking_destino"]))
    filas = ordenar_columnas(filas)

    logging.info("TRANSFORM OK: %s filas x %s columnas", len(filas), len(COLUMNAS))
    return filas
