"""Parada de la cola ante errores reales de acceso/login; solo clientes simulados, sin configuracion externa."""
import asyncio
import json
import time
from types import SimpleNamespace

import pytest

import devmcp_extract as dx


CERRADO = "McpError: BrowserType.launch_persistent_context: Target page, context or browser has been closed"


def herramienta(nombre="getInterface", paginada=False):
    props = {"uuid": {"type": "string"}}
    if paginada:
        props["offset"] = {"type": "integer"}
    return SimpleNamespace(name=nombre, description="", annotations=None,
                           inputSchema={"properties": props, "required": ["uuid"]})


def extractor(cliente, carpeta=None, **kw):
    ex = dx.Extractor(cliente, dx.Policy(dx.DEFAULT_POLICY), carpeta, retry_delay=0, **kw)
    ex.catalog = [herramienta()]
    ex.classify(ex.base_type_phrases())
    return ex


@pytest.mark.parametrize("error", [CERRADO, "playwright._impl._errors.TargetClosedError: connection reset",
    "Browser authentication timed out.", "HTTP 403", "HTTP/1.1 401", "Client error '403 Forbidden' for url",
    "status_code=401", "Browser login appeared to succeed but no Appian session cookies were captured."])
def test_login_terminal_prevalece_sobre_retry(error):
    assert dx.terminal_auth_error(error)
    assert not dx.is_transient(error)


def test_cancelacion_corta_cola_concurrente_sin_cachear_no_intentadas(tmp_path):
    async def caso():
        class Cliente:
            def __init__(self):
                self.calls = []
                self.tres = asyncio.Event()

            async def call(self, name, args):
                self.calls.append(args["uuid"])
                if len(self.calls) == 3:
                    self.tres.set()
                await self.tres.wait()
                if args["uuid"] == "demo-0":
                    return dx.CallResult(False, error=CERRADO)
                await asyncio.sleep(0.01)
                return dx.CallResult(True, {"uuid": args["uuid"]})

        cliente = Cliente()
        ex = extractor(cliente, tmp_path, concurrency=3)
        objetos = [{"uuid": f"demo-{n}", "name": f"DEM_{n}", "type": "interface"} for n in range(12)]
        resultados = await asyncio.gather(*(ex.run_call(ex.tools[0], "object", obj=o) for o in objetos))
        assert len(cliente.calls) == 3  # las tres en curso pueden acabar; ninguna de las nueve en cola empieza
        assert sum(not r.attempted for r in resultados) == 9
        assert len(list(ex.raw.rglob("getInterface.json"))) == 3
        assert len(ex.errors) == 1
        assert ex.stats["getInterface"]["notAttempted"] == 9
        assert not ex.disabled

        class Reanudado:
            calls = []

            async def call(self, name, args):
                self.calls.append(args["uuid"])
                return dx.CallResult(True, {"uuid": args["uuid"]})

        nuevo = extractor(Reanudado(), tmp_path)
        await asyncio.gather(*(nuevo.run_call(nuevo.tools[0], "object", obj=o) for o in objetos))
        assert len(nuevo.sess.calls) == 10  # conserva las dos correctas; vuelve a intentar el error y las nueve pendientes
        assert nuevo.interruption is None
    asyncio.run(caso())


@pytest.mark.parametrize("error", ["HTTP 500 Internal Server Error", "HTTP 429 Too Many Requests"])
def test_500_y_429_siguen_reintentando(error):
    class Cliente:
        n = 0

        async def call(self, name, args):
            self.n += 1
            return dx.CallResult(self.n > 1, error=error if self.n == 1 else None)
    ex = extractor(Cliente())
    assert asyncio.run(ex.call_with_retry("getInterface", {})).ok
    assert ex.sess.n == 2 and ex.interruption is None


def test_error_403_detiene_reintento_que_ya_esperaba():
    async def caso():
        class Cliente:
            calls = []

            async def call(self, name, args):
                self.calls.append(name)
                return dx.CallResult(False, error="HTTP 500" if name == "primero" else "HTTP 403")
        ex = extractor(Cliente(), concurrency=1)
        ex.retry_delay = 0.01
        resultados = await asyncio.gather(ex.call_with_retry("primero", {}), ex.call_with_retry("segundo", {}))
        assert ex.sess.calls == ["primero", "segundo"]
        assert all(r.attempted for r in resultados)
        assert resultados[0].interrupted and ex.interruption["error"] == "HTTP 403"
    asyncio.run(caso())


def test_pagina_interrumpida_conserva_datos_sin_declarar_lista_completa():
    class Cliente:
        n = 0

        async def call(self, name, args):
            self.n += 1
            return (dx.CallResult(True, {"items": [{"uuid": "demo-primero"}], "total": 2}) if self.n == 1
                    else dx.CallResult(False, error="HTTP 403"))
    ex = extractor(Cliente())
    ex.catalog = [herramienta("listInterfaceVersions", paginada=True)]
    ex.classify(ex.base_type_phrases())
    # Esta lista se pagina como metadatos normales, independientemente del rol de versiones.
    ex.tools[0].role = "other"
    res = asyncio.run(ex.call_paginated(ex.tools[0], {"uuid": "demo-objeto"}))
    assert not res.ok and res.interrupted
    assert res.data["items"] == [{"uuid": "demo-primero"}]
    assert ex.sess.n == 2


def test_extract_parcial_no_dice_terminada_ni_objeto_ausente(tmp_path, monkeypatch, capsys):
    class Cliente:
        async def call(self, name, args):
            return dx.CallResult(False, error="HTTP 403 Forbidden")
    ex = extractor(Cliente(), tmp_path, concurrency=1)
    objetos = [{"uuid": "demo-interface", "name": "DEM_Interfaz", "type": "interface"}]

    async def preparado(*_):
        return {"uuid": "demo-app", "name": "Demo"}, objetos, ex.plan_object_calls(objetos)
    monkeypatch.setattr(dx, "prepare", preparado)
    args = SimpleNamespace(refresh=False, yes=True, json=False)
    choice = dx.ServerChoice("mock", "mock", "", [], {"LCP_URL": "https://demo.invalid"})
    code = asyncio.run(dx.plan_o_extrae(ex, args, True, choice, dx.now_iso(), time.monotonic()))
    report = json.loads((dx.work_dir(tmp_path) / "extraction_report.json").read_text(encoding="utf-8"))
    assert code == dx.EXIT_START and report["status"] == "partial"
    assert report["interruption"]["error"] == "HTTP 403 Forbidden"
    assert report["objectCount"] == 1 and not report["disabledAfterProbe"]
    assert "Extraccion terminada" not in capsys.readouterr().out


def test_lista_interrumpida_no_reemplaza_inventario_anterior(tmp_path, monkeypatch):
    ex = extractor(None, tmp_path)
    anterior = ex.raw / "_objects.json"
    anterior.parent.mkdir(parents=True)
    anterior.write_text('{"objects": [{"uuid": "demo-conservado"}]}', encoding="utf-8")
    contenido = anterior.read_bytes()

    async def interrumpido(*_):
        ex.interruption = {"tool": "listInterfaces", "error": CERRADO, "at": dx.now_iso()}
        ex.check_interrupted()
    monkeypatch.setattr(dx, "prepare", interrumpido)
    args = SimpleNamespace(refresh=False)
    choice = dx.ServerChoice("mock", "mock", "", [], {})
    code = asyncio.run(dx.plan_o_extrae(ex, args, True, choice, dx.now_iso(), time.monotonic()))
    report = json.loads((dx.work_dir(tmp_path) / "extraction_interrupted.json").read_text(encoding="utf-8"))
    assert code == dx.EXIT_START and report["status"] == "partial" and not report["objectListComplete"]
    assert anterior.read_bytes() == contenido


@pytest.mark.parametrize("comando", ["verificar", "deriva"])
def test_comandos_conservan_resultado_anterior_sin_inventar_ausencias(comando, tmp_path, monkeypatch):
    class Cliente:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        async def call(self, name, args):
            return dx.CallResult(False, error="HTTP 403 Forbidden")

    async def interrumpido(ex, *_):
        await ex.call_with_retry("listInterfaces", {})
        ex.check_interrupted()
    monkeypatch.setattr(dx, "prepare", interrumpido)
    choice = dx.ServerChoice("mock", "mock", "", [], {})
    monkeypatch.setattr(dx, "open_session", lambda *_: (Cliente(), choice, 0, ""))
    salida = tmp_path / "datos/deriva.json" if comando == "deriva" else tmp_path / "verificacion.json"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text('{"resultadoAnterior": true}', encoding="utf-8")
    anterior = salida.read_bytes()
    dx.write_json(dx.work_dir(tmp_path, crear=True) / "mcp_raw/_objects.json",
                  {"application": {"uuid": "demo-app", "name": "Demo"}, "objects": []})
    args = SimpleNamespace(objetos="DEM_Objeto", esperado=None, ignorar=None, registro=False,
                           policy=dx.DEFAULT_POLICY, out=str(tmp_path if comando == "deriva" else salida))
    code = asyncio.run(getattr(dx, "cmd_" + comando)(args))
    parcial = json.loads(salida.with_name(salida.stem + ".interrumpido.json").read_text(encoding="utf-8"))
    assert code == 13 and salida.read_bytes() == anterior
    assert parcial["status"] == "partial" and not parcial["previousResultIsCurrent"]
    assert not any(k in parcial for k in ("objetos", "faltan", "retirados"))


def test_deriva_no_devuelve_retirados_si_el_historial_falla_por_acceso(tmp_path):
    class Cliente:
        async def call(self, *_):
            return dx.CallResult(False, error="HTTP 401 Unauthorized")
    ex = extractor(Cliente())
    ex.catalog = [herramienta("listObjectVersions")]
    ex.classify(ex.base_type_phrases())
    existente = {"uuid": "demo-presente", "name": "DEM_Presente", "type": "interface"}
    previo = {"objects": [existente, {"uuid": "demo-otro", "name": "DEM_Otro", "type": "interface"}]}
    with pytest.raises(dx.ExtractionInterrupted):
        asyncio.run(dx.deriva_de(ex, previo, [existente], [], {}, tmp_path, None))


def test_verifica_no_devuelve_falta_tras_una_lectura_terminal():
    ex = extractor(None)
    ex.interruption = {"error": CERRADO}
    with pytest.raises(dx.ExtractionInterrupted):
        asyncio.run(dx.verifica(ex, {}, [], ["DEM_Objeto"], ligero=True))


def test_reanudacion_completa_supera_marcador_parcial(tmp_path, monkeypatch):
    class Cliente:
        async def call(self, name, args):
            return dx.CallResult(True, {"uuid": args["uuid"]})
    ex = extractor(Cliente(), tmp_path)
    objetos = [{"uuid": "demo-interface", "name": "DEM_Interfaz", "type": "interface"}]

    async def preparado(*_):
        return {"uuid": "demo-app", "name": "Demo"}, objetos, ex.plan_object_calls(objetos)
    monkeypatch.setattr(dx, "prepare", preparado)
    marca = dx.work_dir(tmp_path) / "extraction_interrupted.json"
    dx.write_json(marca, {"status": "partial", "interruption": {"error": CERRADO}})
    args = SimpleNamespace(refresh=False, yes=True, json=False)
    choice = dx.ServerChoice("mock", "mock", "", [], {})
    assert asyncio.run(dx.plan_o_extrae(ex, args, True, choice, dx.now_iso(), time.monotonic())) == 0
    assert json.loads(marca.read_text(encoding="utf-8"))["status"] == "superseded"
    assert json.loads((marca.parent / "extraction_report.json").read_text(encoding="utf-8"))["status"] == "complete"


def test_refresh_conserva_respuesta_correcta_previa_sin_usarla_como_actual(tmp_path):
    class Cliente:
        def __init__(self, ok):
            self.ok = ok

        async def call(self, name, args):
            return dx.CallResult(self.ok, {"name": "DEM_Anterior"} if self.ok else None,
                                 None if self.ok else "HTTP 403")
    objeto = {"uuid": "demo-interface", "name": "DEM_Interfaz", "type": "interface"}
    bien = extractor(Cliente(True), tmp_path)
    asyncio.run(bien.run_call(bien.tools[0], "object", obj=objeto))
    fichero = bien.target_file(bien.tools[0], "object", objeto)
    anterior = json.loads(fichero.read_text(encoding="utf-8"))
    for _ in range(2):
        mal = extractor(Cliente(False), tmp_path, refresh=True)
        asyncio.run(mal.run_call(mal.tools[0], "object", obj=objeto))
        guardado = json.loads(fichero.read_text(encoding="utf-8"))
        assert not guardado["_meta"]["ok"] and guardado["_meta"]["interrupted"]
        assert guardado["previousSuccessfulResponse"] == anterior
        assert guardado["response"] is None
    reanudado = extractor(Cliente(True), tmp_path)
    assert asyncio.run(reanudado.run_call(reanudado.tools[0], "object", obj=objeto)).ok
    assert not reanudado.stats["getInterface"]["cached"]
