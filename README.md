# Prática: SSE e WebSocket

Demonstração de comunicação em tempo real com dois serviços em Docker:

- `servidor`: aplicação Python (FastAPI) com página web, conexão SSE, conexão WebSocket e rota HTTP `POST /webhook`.
- `emissor`: serviço Python que envia um evento ao servidor a cada 3 segundos.

## Executar

Com Docker Desktop aberto, na raiz deste projeto rode:

```sh
docker compose up --build
```

Abra [http://localhost:3000](http://localhost:3000). Eventos automáticos aparecem nas duas colunas. Clique em **Enviar mensagem ao servidor** para enviar uma mensagem pelo WebSocket e receber o eco.

Para encerrar, use `Ctrl+C`. Para remover os containers, rode `docker compose down`.

## Acompanhar os serviços

Em outro terminal:

```sh
docker compose logs -f servidor emissor
```

O emissor faz um POST para `http://servidor:3000/webhook`, usando o nome do serviço na rede interna do Compose. O servidor repassa o evento às conexões abertas. SSE usa HTTP e envia eventos em uma direção; WebSocket mantém uma conexão persistente e aceita mensagens nos dois sentidos.

O backend e os dois containers da prática usam Python. O pequeno trecho JavaScript em `servidor/public/index.html` fica no navegador porque `WebSocket` e `EventSource` são APIs do navegador usadas para demonstrar os protocolos.

## Comparação rápida

| Tecnologia | Direção | Conexão | Exemplo adequado |
| --- | --- | --- | --- |
| Polling | Cliente consulta o servidor | Várias requisições HTTP | Verificações periódicas simples |
| SSE | Servidor envia ao cliente | HTTP aberto; `EventSource` reconecta automaticamente | Notificações, feeds e progresso |
| WebSocket | Cliente e servidor enviam | Conexão persistente e bidirecional | Chat, jogos e colaboração |

Polling é simples, mas pode gerar requisições sem novidades e trazer atualizações com atraso. SSE só envia do servidor ao cliente e trabalha sobre HTTP. WebSocket permite tráfego nos dois sentidos; a aplicação gerencia a conexão e os eventos.
