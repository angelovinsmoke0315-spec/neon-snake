# Neon Snake Versus

## Modos

### Clásico
- Flechas o WASD.
- Manzana dorada cada 5 comidas.
- Combo.
- Niveles.
- Obstáculos.
- TOP 10 en SQLite.

### Versus local
- Jugador 1: WASD.
- Jugador 2: flechas.
- Primera persona que haga chocar al rival gana la ronda.
- Choque cabeza contra cabeza = empate.
- Se puede elegir 1, 2, 3 o 5 victorias para ganar el encuentro.
- Manzana dorada compartida.
- Puntuación independiente para ambos.
- Historial de campeones VS en SQLite.

## Controles

```text
Jugador 1 VS
W = arriba
A = izquierda
S = abajo
D = derecha

Jugador 2 VS
↑ = arriba
← = izquierda
↓ = abajo
→ = derecha

P = pausa
M = activar/desactivar efectos
B = activar/desactivar música
ESC = menú
```

## Ejecutar en Ubuntu / Pop!_OS

```bash
cd neon_snake_versus

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -r requirements.txt

python app.py
```

Después abre:

```text
http://127.0.0.1:5000
```

## Base de datos

El programa crea o reutiliza:

```text
puntuaciones.db
```

Incluye:

```text
puntuaciones
partidas_vs
```

Para verla:

```bash
sqlite3 puntuaciones.db
```

Dentro:

```sql
.headers on
.mode column

SELECT * FROM puntuaciones;

SELECT * FROM partidas_vs;
```

Note: This was created using AI.