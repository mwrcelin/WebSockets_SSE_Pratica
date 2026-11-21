import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Prática SSE e WebSocket")

# Cada navegador SSE tem sua própria fila de eventos.
clientes_sse: set[asyncio.Queue[str]] = set()
clientes_websocket: set[WebSocket] = set()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/sse")
async def sse(request: Request):
    fila: asyncio.Queue[str] = asyncio.Queue()
    clientes_sse.add(fila)

    async def enviar_eventos():
        try:
            inicial = {"tipo": "status", "mensagem": "SSE conectado. Aguardando eventos..."}
            yield f"data: {json.dumps(inicial, ensure_ascii=False)}\n\n"
            while not await request.is_disconnected():
                try:
                    dados = await asyncio.wait_for(fila.get(), timeout=15)
                    yield f"data: {dados}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            clientes_sse.discard(fila)

    return StreamingResponse(
        enviar_eventos(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clientes_websocket.add(websocket)
    await websocket.send_json({"tipo": "status", "mensagem": "WebSocket conectado. Aguardando eventos..."})
    try:
        while True:
            mensagem = await websocket.receive_text()
            print(f"Mensagem recebida pelo WebSocket: {mensagem}")
            await websocket.send_json({"tipo": "eco", "mensagem": f"Servidor recebeu: {mensagem}"})
    except WebSocketDisconnect:
        pass
    finally:
        clientes_websocket.discard(websocket)


@app.post("/webhook", status_code=202)
async def webhook(request: Request):
    try:
        corpo = await request.json()
    except (json.JSONDecodeError, ValueError) as erro:
        raise HTTPException(status_code=400, detail="O corpo precisa ser JSON válido.") from erro
    if not isinstance(corpo, dict):
        raise HTTPException(status_code=400, detail="O corpo JSON precisa ser um objeto.")

    evento = {"tipo": "evento", "recebidoEm": datetime.now(timezone.utc).isoformat(), **corpo}
    dados = json.dumps(evento, ensure_ascii=False)
    for fila in tuple(clientes_sse):
        fila.put_nowait(dados)

    desconectados = set()
    for cliente in tuple(clientes_websocket):
        try:
            await cliente.send_text(dados)
        except RuntimeError:
            desconectados.add(cliente)
    clientes_websocket.difference_update(desconectados)

    print(f"Evento distribuído: {evento.get('mensagem', 'sem mensagem')}")
    return {"status": "publicado", "sse": len(clientes_sse), "websocket": len(clientes_websocket)}


# Monte os arquivos estáticos por último para que as rotas da API sejam avaliadas antes.
app.mount("/", StaticFiles(directory=Path(__file__).parent / "public", html=True), name="public")
