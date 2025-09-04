# Conversational Commerce — PUBLIC DEMO (Render‑ready)

Servei FastAPI que mostra un xat (frontend estàtic) i processa converses per comprar productes d'exemple. Llista per desplegar a **Render (Free)**. Stripe (test) opcional; si no el configures, usa **pagament simulat**.

## Executar en local
```
pip install -r requirements.txt
uvicorn main:app --reload
```
Obre http://127.0.0.1:8000/

Flux de prova:
```
Vull eliminar una colònia de formigues
Eliminar colònia
Sí
Comprar
2
C/ Indústria 12, Granollers
1
Pagar ara
```

## Stripe (opcional)
Exporta `STRIPE_API_KEY` (clau de test). Si no la poses, el bot obrirà un **pagament simulat** a `/static/mock-payment.html`.

## Desplegar a Render
- **Build:** `pip install -r requirements.txt`
- **Start:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
- (Opcional) Variable d'entorn: `STRIPE_API_KEY=sk_test_xxx`
