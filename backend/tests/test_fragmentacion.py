import logging

import pytest

from conocimiento.fragmentacion import fragmentar, tamano_objetivo, tamano_solape

# Con max_tokens_modelo = 72 el tamaño objetivo es 72 - 60 = 12 palabras y el solape 2.
MAX_TOKENS_PEQUENO = 72
OBJETIVO_PEQUENO = 12


def contar_palabras(texto: str) -> int:
    return len(texto.split())


def oracion(numero: int, palabras: int = 4) -> str:
    """Una oración de `palabras` palabras, identificable por su número."""
    relleno = " ".join(["dato"] * (palabras - 2))
    return f"Oración{numero} {relleno} fin."


def oraciones_del_texto(fragmento_texto: str) -> list[str]:
    return [palabra for palabra in fragmento_texto.split() if palabra.startswith("Oración")]


# --- Tamaño objetivo y solape (DEC-009) ---


def test_el_tamano_objetivo_depende_del_modelo():
    # Arrange / Act
    con_e5 = tamano_objetivo(512)
    con_bge_m3 = tamano_objetivo(8192)

    # Assert
    assert con_e5 == 452
    assert con_bge_m3 == 600


def test_el_solape_es_una_sexta_parte_del_tamano():
    assert tamano_solape(450) == 75
    assert tamano_solape(600) == 100


def test_un_modelo_sin_espacio_para_el_margen_es_un_error():
    with pytest.raises(ValueError):
        fragmentar(["Texto."], contar_palabras, 60)


# --- Tamaño de los fragmentos ---


def test_ningun_fragmento_supera_el_tamano_objetivo():
    paginas = [" ".join(oracion(numero) for numero in range(1, 30))]

    fragmentos = fragmentar(paginas, contar_palabras, MAX_TOKENS_PEQUENO)

    assert len(fragmentos) > 1
    assert all(fragmento.tokens <= OBJETIVO_PEQUENO for fragmento in fragmentos)
    assert all(fragmento.tokens == contar_palabras(fragmento.texto) for fragmento in fragmentos)


def test_nunca_corta_una_oracion():
    oraciones = [oracion(numero, palabras=3 + numero % 4) for numero in range(1, 25)]
    paginas = [" ".join(oraciones)]

    fragmentos = fragmentar(paginas, contar_palabras, MAX_TOKENS_PEQUENO)

    for fragmento in fragmentos:
        assert fragmento.texto.startswith("Oración")
        assert fragmento.texto.endswith("fin.")


def test_todo_el_texto_queda_en_algun_fragmento():
    paginas = [" ".join(oracion(numero) for numero in range(1, 20))]

    fragmentos = fragmentar(paginas, contar_palabras, MAX_TOKENS_PEQUENO)

    vistas = {nombre for fragmento in fragmentos for nombre in oraciones_del_texto(fragmento.texto)}
    assert vistas == {f"Oración{numero}" for numero in range(1, 20)}


def test_un_texto_corto_queda_en_un_solo_fragmento():
    paginas = ["Primera oración corta. Segunda oración corta."]

    fragmentos = fragmentar(paginas, contar_palabras, 512)

    assert len(fragmentos) == 1
    assert fragmentos[0].texto == "Primera oración corta. Segunda oración corta."
    assert fragmentos[0].tokens == 6


# --- Solape ---


def test_el_fragmento_siguiente_empieza_con_la_ultima_oracion_del_anterior():
    # Oraciones de 2 palabras: el solape de 2 tokens cabe exactamente en una.
    paginas = [" ".join(f"Oración{numero} fin." for numero in range(1, 20))]

    fragmentos = fragmentar(paginas, contar_palabras, MAX_TOKENS_PEQUENO)

    for anterior, siguiente in zip(fragmentos, fragmentos[1:]):
        assert oraciones_del_texto(siguiente.texto)[0] == oraciones_del_texto(anterior.texto)[-1]


def test_sin_solape_si_la_ultima_oracion_es_mas_larga_que_el_solape():
    paginas = [" ".join(oracion(numero, palabras=4) for numero in range(1, 10))]

    fragmentos = fragmentar(paginas, contar_palabras, MAX_TOKENS_PEQUENO)

    for anterior, siguiente in zip(fragmentos, fragmentos[1:]):
        assert oraciones_del_texto(siguiente.texto)[0] != oraciones_del_texto(anterior.texto)[-1]


# --- Páginas y orden ---


def test_cada_fragmento_guarda_su_pagina_de_inicio_y_de_fin():
    paginas = [
        f"{oracion(1, 5)} {oracion(2, 5)}",
        f"{oracion(3, 5)} {oracion(4, 5)}",
        "",
        f"{oracion(5, 5)}",
    ]

    fragmentos = fragmentar(paginas, contar_palabras, MAX_TOKENS_PEQUENO)

    paginas_por_fragmento = [(f.pagina_inicio, f.pagina_fin) for f in fragmentos]
    assert paginas_por_fragmento == [(1, 1), (2, 2), (4, 4)]


def test_un_fragmento_puede_abarcar_dos_paginas():
    paginas = [oracion(1), oracion(2), oracion(3)]

    fragmentos = fragmentar(paginas, contar_palabras, 512)

    assert len(fragmentos) == 1
    assert (fragmentos[0].pagina_inicio, fragmentos[0].pagina_fin) == (1, 3)


def test_el_orden_es_consecutivo_desde_cero():
    paginas = [" ".join(oracion(numero) for numero in range(1, 30))]

    fragmentos = fragmentar(paginas, contar_palabras, MAX_TOKENS_PEQUENO)

    assert [fragmento.orden for fragmento in fragmentos] == list(range(len(fragmentos)))


def test_documento_de_una_sola_pagina():
    paginas = [" ".join(oracion(numero) for numero in range(1, 10))]

    fragmentos = fragmentar(paginas, contar_palabras, MAX_TOKENS_PEQUENO)

    assert all((f.pagina_inicio, f.pagina_fin) == (1, 1) for f in fragmentos)


def test_documento_sin_texto_no_produce_fragmentos():
    assert fragmentar(["", "  \n\n "], contar_palabras, 512) == []


def test_dos_llamadas_no_comparten_texto():
    primero = fragmentar(["Texto del primer documento."], contar_palabras, 512)

    segundo = fragmentar(["Texto del segundo documento."], contar_palabras, 512)

    assert "primer" not in segundo[0].texto
    assert segundo[0].orden == 0


# --- Oraciones largas ---


def test_una_oracion_mas_larga_que_el_objetivo_queda_sola_y_se_advierte(caplog):
    larga = oracion(2, palabras=20)
    paginas = [f"{oracion(1)} {larga} {oracion(3)}"]

    with caplog.at_level(logging.WARNING, logger="conocimiento.fragmentacion"):
        fragmentos = fragmentar(paginas, contar_palabras, MAX_TOKENS_PEQUENO)

    assert [f.texto for f in fragmentos] == [oracion(1), larga, oracion(3)]
    assert fragmentos[1].tokens == 20
    assert "supera el tamaño objetivo" in caplog.text


def test_sin_oraciones_largas_no_hay_advertencias(caplog):
    paginas = [" ".join(oracion(numero) for numero in range(1, 10))]

    with caplog.at_level(logging.WARNING, logger="conocimiento.fragmentacion"):
        fragmentar(paginas, contar_palabras, MAX_TOKENS_PEQUENO)

    assert caplog.records == []


# --- Límites de oración, párrafo y página ---


def test_no_corta_en_abreviaturas_ni_iniciales():
    paginas = ["La roya (H. vastatrix) la estudió el Dr. Gómez, ver Fig. 3. Otra oración."]

    fragmentos = fragmentar(paginas, contar_palabras, 512)

    assert fragmentos[0].texto == paginas[0]


def test_conserva_los_parrafos_y_reune_la_oracion_partida_por_la_pagina():
    paginas = [
        "Primer párrafo completo.\n\nUna oración que sigue en la",
        "página siguiente. Y otra más.",
    ]

    fragmentos = fragmentar(paginas, contar_palabras, 512)

    assert fragmentos[0].texto == (
        "Primer párrafo completo.\n\nUna oración que sigue en la página siguiente. Y otra más."
    )
