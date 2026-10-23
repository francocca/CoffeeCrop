from conocimiento.extraccion.limpieza import (
    limpiar_paginas,
    normalizar_texto_corrido,
    quitar_encabezados_repetidos,
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

    resultado = limpiar_paginas(paginas)

    assert resultado[0] == "La broca ataca el fruto número 1 en la página 1."
    assert len(resultado) == 8
