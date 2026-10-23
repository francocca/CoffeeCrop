import pytest

from conocimiento.extraccion.limpieza import (
    TIPO_AVANCE,
    TIPO_MANUAL,
    cortar_bibliografia,
    limpiar_paginas,
    normalizar_texto_corrido,
    quitar_encabezados_repetidos,
    quitar_portada_administrativa,
)

ENCABEZADO = "cafetero colombiano"


def paginas_de_contenido(cantidad: int) -> list[str]:
    return [f"Contenido único de la página {numero}." for numero in range(1, cantidad + 1)]


def con_encabezado_en(paginas: list[str], indices: range | list[int]) -> list[str]:
    return [
        f"{ENCABEZADO}\n{pagina}" if posicion in indices else pagina
        for posicion, pagina in enumerate(paginas)
    ]


# --- Encabezados repetidos ---


def test_quita_el_encabezado_que_se_repite_en_la_mayoria_de_las_paginas():
    paginas = con_encabezado_en(paginas_de_contenido(10), range(5))

    resultado = quitar_encabezados_repetidos(paginas)

    assert all(ENCABEZADO not in pagina for pagina in resultado)
    assert "Contenido único de la página 1." in resultado[0]
    assert "Contenido único de la página 10." in resultado[9]


def test_el_limite_es_el_40_por_ciento_de_las_paginas():
    en_el_limite = con_encabezado_en(paginas_de_contenido(10), range(4))
    debajo_del_limite = con_encabezado_en(paginas_de_contenido(10), range(3))

    quitado = quitar_encabezados_repetidos(en_el_limite)
    conservado = quitar_encabezados_repetidos(debajo_del_limite)

    assert all(ENCABEZADO not in pagina for pagina in quitado)
    assert sum(ENCABEZADO in pagina for pagina in conservado) == 3


def test_no_toca_documentos_de_menos_de_4_paginas():
    paginas = con_encabezado_en(paginas_de_contenido(3), range(3))

    resultado = quitar_encabezados_repetidos(paginas)

    assert resultado == paginas


def test_conserva_lineas_de_contenido_que_aparecen_una_o_dos_veces():
    paginas = paginas_de_contenido(10)
    paginas[2] += "\nLa roya se controla con variedades resistentes."
    paginas[7] += "\nLa roya se controla con variedades resistentes."

    resultado = quitar_encabezados_repetidos(paginas)

    assert resultado == paginas


def test_cuenta_paginas_distintas_y_no_repeticiones_dentro_de_una_pagina():
    paginas = paginas_de_contenido(10)
    paginas[0] += "\nsí\nsí\nsí\nsí\nsí"

    resultado = quitar_encabezados_repetidos(paginas)

    assert "sí" in resultado[0]


def test_no_quita_lineas_largas_aunque_se_repitan():
    linea_larga = "Esta línea es muy larga para ser un encabezado: " + "x" * 40
    paginas = [f"{linea_larga}\n{pagina}" for pagina in paginas_de_contenido(10)]

    resultado = quitar_encabezados_repetidos(paginas)

    assert resultado == paginas


def test_reconoce_el_encabezado_aunque_cambien_los_espacios():
    paginas = paginas_de_contenido(10)
    paginas = [
        f"{ENCABEZADO}  \n{pagina}" if posicion % 2 else f"  {ENCABEZADO}\n{pagina}"
        for posicion, pagina in enumerate(paginas)
    ]

    resultado = quitar_encabezados_repetidos(paginas)

    assert all(ENCABEZADO not in pagina for pagina in resultado)


def test_conserva_el_numero_de_paginas_al_quitar_encabezados():
    paginas = [ENCABEZADO] * 6 + paginas_de_contenido(2)

    resultado = quitar_encabezados_repetidos(paginas)

    assert len(resultado) == 8
    assert resultado[0].strip() == ""


# --- Texto corrido ---


def test_une_las_lineas_de_un_mismo_parrafo():
    pagina = "Suelos susceptibles a la erosión necesitan\nincorporar sistemas agroforestales\ny prácticas de conservación."

    resultado = normalizar_texto_corrido([pagina])

    assert resultado == [
        "Suelos susceptibles a la erosión necesitan incorporar sistemas agroforestales y prácticas de conservación."
    ]


def test_la_linea_en_blanco_separa_los_parrafos():
    pagina = "Primer párrafo\ncontinúa aquí.\n\nSegundo párrafo\ncontinúa allá."

    resultado = normalizar_texto_corrido([pagina])

    assert resultado == ["Primer párrafo continúa aquí.\n\nSegundo párrafo continúa allá."]


def test_normaliza_espacios_ligaduras_y_espacios_especiales():
    pagina = "El  ﬁltro\t de   café y el ﬂujo​ de agua­."

    resultado = normalizar_texto_corrido([pagina])

    assert resultado == ["El filtro de café y el flujo de agua."]


def test_descarta_lineas_sueltas_de_3_caracteres_o_menos():
    pagina = "Texto de la página.\n\n35\n\na\n\ny 45\n\nOtro texto."

    resultado = normalizar_texto_corrido([pagina])

    assert resultado == ["Texto de la página.\n\ny 45\n\nOtro texto."]


def test_no_descarta_una_linea_corta_que_cierra_un_parrafo():
    pagina = "Las plántulas se siembran en la\nmitad de la\nera"

    resultado = normalizar_texto_corrido([pagina])

    assert resultado == ["Las plántulas se siembran en la mitad de la era"]


def test_cada_vineta_empieza_un_parrafo_nuevo():
    pagina = "Recomendaciones prácticas\n\x83\x83 Siembre solo chapolas sanas.\n\x83\x83 Use suelo desinfectado."

    resultado = normalizar_texto_corrido([pagina])

    assert resultado == [
        "Recomendaciones prácticas\n\n• Siembre solo chapolas sanas.\n\n• Use suelo desinfectado."
    ]


def test_quita_otros_caracteres_de_control_sueltos():
    pagina = "Texto con \x83 un símbolo raro."

    resultado = normalizar_texto_corrido([pagina])

    assert "\x83" not in resultado[0]
    assert resultado[0].startswith("Texto con")


def test_quita_el_numero_de_pagina_pegado_a_la_primera_linea():
    pagina = "\n\n30\nLo anterior demuestra cómo mejorar la producción.\nSegunda línea."

    resultado = normalizar_texto_corrido([pagina])

    assert resultado == ["Lo anterior demuestra cómo mejorar la producción. Segunda línea."]


def test_solo_quita_un_numero_al_comienzo_de_la_pagina():
    pagina = "Texto de apertura.\n\n7\nLa dosis es de\n12\ngramos por planta."

    resultado = normalizar_texto_corrido([pagina])

    assert resultado == ["Texto de apertura.\n\n7 La dosis es de 12 gramos por planta."]


def test_no_quita_una_primera_linea_con_letras_aunque_sea_corta():
    pagina = "Año\nde la cosecha principal."

    resultado = normalizar_texto_corrido([pagina])

    assert resultado == ["Año de la cosecha principal."]


def test_conserva_el_numero_de_paginas_y_las_paginas_vacias():
    paginas = ["Primera página con texto.", "", "   \n\n  ", "Cuarta página."]

    resultado = normalizar_texto_corrido(paginas)

    assert resultado == ["Primera página con texto.", "", "", "Cuarta página."]


# --- Las dos etapas juntas ---


def test_limpiar_paginas_quita_encabezados_y_une_lineas():
    cuerpo = [f"La broca ataca el fruto número {numero}\nen la página {numero}." for numero in range(1, 9)]
    paginas = con_encabezado_en(cuerpo, range(8))

    resultado = limpiar_paginas(paginas, TIPO_MANUAL)

    assert resultado[0] == "La broca ataca el fruto número 1 en la página 1."
    assert len(resultado) == 8


def test_limpiar_paginas_rechaza_un_tipo_desconocido():
    with pytest.raises(ValueError):
        limpiar_paginas(["texto"], "folleto")


# --- Portada administrativa (solo Avances) ---
# Extractos de portadas y créditos reales de los Avances Técnicos de Cenicafé.

PORTADA_ANTIGUA = (
    "ISSN - 0120 - 0178\n"
    "265\n"
    "Gerencia Técnica / Programa de Investigación Científica / Julio de 1999\n"
    "LAS AVES EN LA ZONA CAFETERA DE COLOMBIA\n"
    "Jorge E. Botero*; Juan C. Verhelst*; David Fajardo*\n"
    "El estudio de aves en las zonas cafeteras es uno de los proyectos de Cenicafé.\n"
    "* Investigador Científico y Biólogos, respectivamente. Programa Biología de\n"
    "la Conservación. Centro Nacional de Investigaciones de Café, Cenicafé. Chinchiná, Caldas, Colombia.\n"
    "https://doi.org/10.38141/10779/0265"
)

PORTADA_DUPLICADA = (
    "IISSSSNN -- 00112200 -- 00117788\n"
    "323\n"
    "Gerencia Técnica / Programa de Investigación Científica / Mayo de 2004\n"
    "LA CALIDAD FÍSICA Y EL RENDIMIENTO DEL CAFÉ\n"
    "Ilde Fernando Fajardo Peña*; Juan Rodrigo Sanz Uribe **\n"
    "El proceso de beneficio tiene marcada influencia sobre la calidad del café."
)

PORTADA_RECIENTE = (
    "Diciembre de 2015 Gerencia Técnica / Programa de Investigación Científica Fondo Nacional del Café\n"
    "Uso del selector de arvenses en cultivos de café\n"
    "Recomendaciones prácticas\n"
    "Cerca del 25% de los caficultores no realizan el Manejo Integrado de Arvenses."
)

CREDITOS_ANTIGUOS = (
    "El sombrío debe mantenerse entre el 35 y el 45 %.\n"
    "Edición:\n"
    "Diagramación: Fotografía:\n"
    "Héctor Fabio Ospina Ospina\n"
    "Angela C. Miranda C. Thomas McNish\n"
    "Jorge Eduardo Botero Gonzalo Hoyos S.\n"
    "Los trabajos suscritos por el personal técnico del Centro Nacional de Investigaciones de Café "
    "son parte de las investigaciones realizadas por la Federación Nacional de Cafeteros de Colombia. "
    "Sin embargo, tanto en este caso como en el de personas no pertenecientes a este Centro, las ideas "
    "emitidas por los autores son de su exclusiva responsabilidad y no expresan necesariamente las "
    "opiniones de la Entidad.\n"
    'Centro Nacional de Investigaciones de Café "Pedro Uribe Mejía"\n'
    "Chinchiná, Caldas, Colombia Tel. (968)506550 Fax. (968)504723\n"
    "A.A. 2427 Manizales cenicafe@cafedecolombia.com"
)

CREDITOS_RECIENTES = (
    "Edición Sandra Milena Marín López\n"
    "Archivo Cenicafé\n"
    "Fotografías\n"
    "Diagramación Carmenza Bacca Ramírez\n"
    "Imprenta\n"
    "Gerencia Técnica Fondo Nacional del Café\n"
    "ISSN-0120-0178 ISSN-2145-3691 (En línea)\n"
    "Manizales, Caldas, Colombia - Tel. (606) 8500707 www.cenicafe.org\n"
    "Licencia Creative Commons CC de Atribución - sin derivar - no comercial.\n"
    "© FNC - Cenicafé"
)


def lineas_de(pagina: str) -> list[str]:
    return pagina.split("\n")


def test_quita_issn_doi_afiliacion_y_autores_de_la_portada_conservando_titulo_y_cuerpo():
    resultado = quitar_portada_administrativa([PORTADA_ANTIGUA])[0]

    assert "ISSN" not in resultado
    assert "doi.org" not in resultado
    assert "Gerencia Técnica" not in resultado
    assert "Botero*" not in resultado
    assert "Investigador Científico" not in resultado
    assert "Chinchiná" not in resultado
    assert "LAS AVES EN LA ZONA CAFETERA DE COLOMBIA" in lineas_de(resultado)
    assert "El estudio de aves en las zonas cafeteras es uno de los proyectos de Cenicafé." in resultado


def test_quita_la_portada_con_letras_duplicadas_y_autores_con_dos_asteriscos():
    resultado = quitar_portada_administrativa([PORTADA_DUPLICADA])[0]

    assert "IISSSSNN" not in resultado
    assert "Sanz Uribe" not in resultado
    assert "LA CALIDAD FÍSICA Y EL RENDIMIENTO DEL CAFÉ" in lineas_de(resultado)
    assert "El proceso de beneficio tiene marcada influencia sobre la calidad del café." in resultado


def test_quita_la_linea_de_gerencia_tecnica_de_las_portadas_recientes():
    resultado = quitar_portada_administrativa([PORTADA_RECIENTE])[0]

    assert "Gerencia Técnica" not in resultado
    assert lineas_de(resultado) == [
        "Uso del selector de arvenses en cultivos de café",
        "Recomendaciones prácticas",
        "Cerca del 25% de los caficultores no realizan el Manejo Integrado de Arvenses.",
    ]


def test_quita_autores_separados_por_barras():
    pagina = "MAYO 2025 Duque-Dussán, E.| Ramírez, C. A. |Sanz-Uribe, J. R.\nSecadores solares modulares de café"

    resultado = quitar_portada_administrativa([pagina])[0]

    assert resultado == "Secadores solares modulares de café"


def test_quita_lineas_administrativas_largas_que_pdftotext_junto_en_una_sola():
    linea_junta = (
        "ISSN - 0120 - 0178 https://doi.org/10.38141/10779/0405 Los trabajos suscritos por el "
        "personal técnico del Centro Nacional de Investigaciones de Café son parte de las "
        "investigaciones realizadas por la Federación Nacional de Cafeteros de Colombia. Sin embargo, "
        "tanto en este caso como en el de personas no pertenecientes a este Centro, las ideas emitidas."
    )
    afiliacion_larga = (
        "∗ Asistente de Investigación. Fitotecnia. Centro Nacional de Investigaciones de Café, "
        "Cenicafé. Chinchiná, Caldas, Colombia. ∗∗ Asistente de Investigación. Subestación "
        "Santander. Programa de Experimentación, Centro Nacional de Investigaciones de Café, Cenicafé. "
        "Chinchiná, Caldas, Colombia. https://doi.org/10.38141/10779/0363"
    )
    assert len(linea_junta) > 220 and len(afiliacion_larga) > 220

    resultado = quitar_portada_administrativa(["Portada", f"El cuerpo.\n{linea_junta}\n{afiliacion_larga}"])[1]

    assert resultado == "El cuerpo."


def test_no_quita_una_linea_larga_de_cuerpo_que_solo_menciona_un_doi_en_medio():
    linea = (
        "Los resultados completos del experimento, con todos los detalles de la metodología empleada "
        "en las parcelas de campo y los análisis estadísticos, se pueden consultar en la publicación "
        "original (https://doi.org/10.1000/ejemplo), que describe además los costos de producción."
    )

    resultado = quitar_portada_administrativa(["Portada", linea])[1]

    assert resultado == linea


def test_solo_busca_autores_en_la_primera_pagina():
    pagina = "Jaime Arcila Pulgarín*; Álvaro Jaramillo Robledo**\nIndividual Rotación***"

    primera = quitar_portada_administrativa([pagina])[0]
    segunda = quitar_portada_administrativa(["Texto de la portada.", pagina])[1]

    assert primera.strip() == ""
    assert segunda == pagina


def test_conserva_notas_de_tablas_y_celdas_con_asterisco_en_el_cuerpo():
    pagina = (
        "Tabla 2. Efecto del fungicida.\n"
        "* DDS. Días después de la siembra.\n"
        "*Promedios con distinta letra presentan diferencia estadística.\n"
        "*Para cada estación experimental, letras no comunes indican diferencia según Cenicafé.\n"
        "mancozeb semanal*\n"
        "Coloide*,"
    )

    resultado = quitar_portada_administrativa(["Portada", pagina])[1]

    assert resultado == pagina


def test_quita_la_nota_al_pie_con_la_afiliacion_de_los_autores():
    pagina = (
        "* Investigador Científico III, Ingeniería Agrícola, Centro Nacional de Investigaciones de Café\n"
        "** Asistente de Investigación. Subestación Experimental La Catalina.\n"
        "∗ Investigador Científico II y Asistente de Investigación, respectivamente. Suelos. Cenicafé.\n"
        "El cuerpo sigue aquí."
    )

    resultado = quitar_portada_administrativa(["Portada", pagina])[1]

    assert resultado == "El cuerpo sigue aquí."


def test_quita_creditos_y_direccion_del_pie_de_los_avances_antiguos():
    resultado = quitar_portada_administrativa([CREDITOS_ANTIGUOS])[0]

    assert resultado == "El sombrío debe mantenerse entre el 35 y el 45 %."


def test_quita_creditos_y_licencia_del_pie_de_los_avances_recientes():
    resultado = quitar_portada_administrativa([CREDITOS_RECIENTES])[0]

    assert resultado.strip() == ""


def test_quita_la_linea_de_creditos_larga_y_la_lista_de_autores_con_orcid():
    creditos = (
        "Edición Sandra Milena Marín López Fotografías Luis Fernando Salazar Gutiérrez Archivo Cenicafé "
        "Diagramación Carmenza Bacca Ramírez Imprenta"
    )
    autores = (
        "Zulma Nancy Gil Palacio Investigador Científico II https://orcid.org/0000-0001-7013-1231 "
        "Luis Miguel Constantino Chaure Investigador Científico II https://orcid.org/0000-0002-1111-2222 "
        "Pablo Benavides Machado Investigador Principal https://orcid.org/0000-0003-3333-4444"
    )
    assert len(creditos) > 120 and len(autores) > 220

    resultado = quitar_portada_administrativa(["Portada", f"El cuerpo.\n{creditos}\n{autores}"])[1]

    assert resultado == "El cuerpo."


def test_no_quita_lineas_de_cuerpo_que_empiezan_con_una_palabra_de_credito():
    pagina = "Edición de la tercera cosecha se realiza a los ocho meses.\nLa impresión general es positiva."

    resultado = quitar_portada_administrativa([pagina])[0]

    assert resultado == pagina


def test_no_quita_nombres_que_siguen_a_una_linea_normal():
    pagina = "Recomendaciones del autor\nJuan Carlos Pérez Gómez\nLa broca se controla con recolección."

    resultado = quitar_portada_administrativa([pagina])[0]

    assert resultado == pagina


def test_no_quita_lineas_largas_de_cuerpo_que_mencionan_el_centro_de_investigaciones():
    linea = (
        "Los resultados se obtuvieron en el Centro Nacional de Investigaciones de Café, "
        "en pruebas de campo realizadas durante dos años consecutivos en la zona cafetera."
    )
    pagina = f"{linea}\nOtra línea del cuerpo."

    resultado = quitar_portada_administrativa([pagina])[0]

    assert linea in resultado


def test_quitar_portada_conserva_el_numero_de_paginas():
    resultado = quitar_portada_administrativa([PORTADA_ANTIGUA, "", CREDITOS_ANTIGUOS])

    assert len(resultado) == 3
    assert resultado[1] == ""


# --- Bibliografía (solo Avances) ---


def test_descarta_desde_literatura_citada_hasta_el_final_del_documento():
    paginas = [
        "Cuerpo de la página uno.",
        "Final del cuerpo.\nLiteratura citada\n1. AGATE, A.D. Role of yeasts. 1966.",
        "2. BRAVERMAN, J.B.S. Introducción a la bioquímica. 1980.",
    ]

    resultado = cortar_bibliografia(paginas)

    assert resultado == ["Cuerpo de la página uno.", "Final del cuerpo.", ""]


@pytest.mark.parametrize(
    "encabezado",
    ["LITERATURA CITADA", "literatura citada", "Literatura Citada", "Literatura citada:", "Literatura consultada"],
)
def test_reconoce_el_encabezado_con_cualquier_combinacion_de_mayusculas(encabezado):
    paginas = [f"Texto del cuerpo.\n{encabezado}\nREFERENCIA UNO"]

    resultado = cortar_bibliografia(paginas)

    assert resultado == ["Texto del cuerpo."]


def test_el_encabezado_puede_traer_la_primera_referencia_en_la_misma_linea():
    paginas = ["Cuerpo.\nLiteratura citada 1. AGATE, A.D. Role of yeasts. 1966."]

    resultado = cortar_bibliografia(paginas)

    assert resultado == ["Cuerpo."]


def test_sin_encabezado_de_bibliografia_no_cambia_nada():
    paginas = ["Primera página.", "Segunda página con referencias (Pérez, 2010)."]

    resultado = cortar_bibliografia(paginas)

    assert resultado == paginas


def test_no_corta_por_una_frase_que_solo_menciona_la_literatura_citada():
    paginas = ["Como indica la literatura citada en este trabajo, la broca se controla.\nMás texto."]

    resultado = cortar_bibliografia(paginas)

    assert resultado == paginas


def test_bibliografia_al_comienzo_de_la_primera_pagina_deja_todo_vacio():
    paginas = ["Literatura citada\n1. UNA REFERENCIA", "2. OTRA REFERENCIA"]

    resultado = cortar_bibliografia(paginas)

    assert resultado == ["", ""]


# --- Avance frente a Manual ---


def documento_con_portada_y_bibliografia() -> list[str]:
    return [
        PORTADA_ANTIGUA,
        "El cuerpo continúa con recomendaciones de manejo.",
        "Literatura citada\n1. ALVAREZ L., H. Introducción a las Aves de Colombia. 1979\n" + CREDITOS_ANTIGUOS,
    ]


def test_en_un_avance_se_aplican_portada_y_bibliografia():
    resultado = limpiar_paginas(documento_con_portada_y_bibliografia(), TIPO_AVANCE)

    assert len(resultado) == 3
    assert "ISSN" not in resultado[0]
    assert "LAS AVES EN LA ZONA CAFETERA DE COLOMBIA" in resultado[0]
    assert resultado[1] == "El cuerpo continúa con recomendaciones de manejo."
    assert resultado[2] == ""


def test_en_el_manual_no_se_aplica_ninguna_de_las_dos_reglas():
    paginas = documento_con_portada_y_bibliografia()

    resultado = limpiar_paginas(paginas, TIPO_MANUAL)

    assert "ISSN" in resultado[0]
    assert "Literatura citada" in resultado[2]
    assert "ALVAREZ L., H." in resultado[2]
    assert "Tel. (968)506550" in resultado[2]
