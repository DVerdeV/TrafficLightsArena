# Traffic Lights Arena

The challenge for Cursor Build Night Málaga. Your team has **105 minutes** to control a living city by changing one file: `controller.py`.

## Requirements

- Python 3.12 or newer.
- A current version of Chrome, Edge, Firefox, or Safari for the local viewer.

## Quick start by operating system

Download and extract this folder, then open a terminal inside `TrafficLightsArena`.

### macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run.py
```

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run.py
```

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py
```

The browser viewer opens automatically and updates whenever you save `controller.py`. Keep `run.py` open while you work and press `Ctrl+C` to stop it.

## Your one function

Only edit `controller.py`. On every simulation tick, the engine calls `control(state)` and expects a dictionary that maps any junctions you want to update to `"NS_GREEN"` or `"EW_GREEN"`.

```python
def control(state):
    return {intersection_id: "NS_GREEN" for intersection_id in state["intersections"]}
```

Omitted junctions keep their previous request. Unknown junction IDs, invalid phases, exceptions, and return values other than a dictionary invalidate an evaluation. The engine enforces a minimum green of 5 ticks and inserts 2 yellow ticks followed by 1 all-red tick before the next green.

## The `state` dictionary

You do not create `state`; the engine provides it. Map dimensions and junction IDs vary, so iterate over `state["intersections"]` instead of hard-coding IDs.

```python
{
    "tick": 42,
    "remaining_ticks": 858,
    "map": {"rows": 2, "cols": 2},
    "intersections": {
        "A1": {
            "phase": "NS_GREEN",
            "phase_age": 8,
            "can_switch": True,
            "queues": {"N": 3, "S": 1, "E": 5, "W": 4},
            "oldest_wait": {"N": 7, "S": 2, "E": 14, "W": 11},
        }
    },
    "links": {
        "A1->A2": {
            "from": "A1", "to": "A2", "vehicles": 2, "capacity": 8
        }
    },
    "vehicles": {"spawned": 96, "active": 18, "completed": 78},
}
```

`phase` can also be `YELLOW` or `ALL_RED`. Empty links may be absent. You may keep module-level memory between calls and use NumPy, but your strategy must work with every map size and traffic pattern.

## Test every public map

Run one command at a time; the viewer includes 0.25× and 0.5× playback for inspecting decisions.

```bash
python run.py --scenario balanced-grid
python run.py --scenario northbound-morning
python run.py --scenario city-rush
```

The local result is a development aid. The event server performs the authoritative evaluation in an isolated environment.

## Scoring

For each map:

```text
cost = wait_ticks + (unfinished_vehicles × 300)
score = 10,000 × baseline_cost / your_cost
```

The baseline earns 10,000 points and each map is capped at 25,000. The final score combines the geometric mean of the 3 public maps at 40% and the geometric mean of the 5 hidden maps at 60%. The leaderboard uses each team's best valid total submission.

## Submit

```bash
python submit.py login MLG-XXXX-XXXX-XXXX-XXXX --url https://YOUR-EVENT-URL
python submit.py
```

Log in once with the team code supplied by the organizer. Each later `python submit.py` uploads only `controller.py`, waits for the 8-scenario evaluation, prints the result, and opens its public replay. Identical code reuses its previous result, and new code may be submitted at most once per minute while the event is live.

---

## Español

Este es el reto de Cursor Build Night Málaga. Tu equipo dispone de **105 minutos** para controlar una ciudad modificando un único archivo: `controller.py`.

1. Crea y activa un entorno virtual.
2. Ejecuta `pip install -r requirements.txt`.
3. Ejecuta `python run.py`.
4. Edita `controller.py`; el navegador se actualizará cada vez que guardes.
5. Inicia sesión con el código de tu mesa y ejecuta `python submit.py`.

Las instrucciones completas en español están siempre disponibles en la página «El reto» de la web del evento. El baseline obtiene 10.000 puntos por escenario. Reduce la espera y los vehículos sin terminar para superarlo.

Vehicle artwork is from Kenney's Racing Pack under CC0. See `viewer/assets/KENNEY-LICENSE.txt`.
