# Traffic Lights Arena

The challenge for Cursor Build Night Málaga. Your team has **105 minutes** to control a living city by changing one file: `controller.py`.

## Quick start

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1

pip install -r requirements.txt
python run.py
```

The browser viewer updates whenever you save `controller.py`.

```python
def control(state):
    return {intersection_id: "NS_GREEN" for intersection_id in state["intersections"]}
```

Allowed phases are `NS_GREEN` and `EW_GREEN`. The engine handles minimum green time, amber, all-red, and safe transitions.

## Submit

```bash
python submit.py login MLG-XXXX-XXXX-XXXX-XXXX --url https://YOUR-EVENT-URL
python submit.py
```

You may make up to **20 unique submissions**, with a five-minute cooldown after each accepted submission. Submitting identical controller code returns the existing result without consuming an attempt or restarting the cooldown.

During the challenge, the leaderboard shows a provisional score made from 20% public scenarios and 80% private validation scenarios. When submissions close, each team's best provisional submission is selected automatically and evaluated once on a separate sealed final suite. The twelve final maps form six traffic families. Each family contributes the lower of its two map scores, and those six results are combined geometrically. The final leaderboard uses 20% public score and 80% sealed-final score.

The fixed-time baseline earns 10,000 points per scenario. Each public scenario includes a calibrated gold target worth 25,000 points. Improvement toward gold uses a squared curve: making half of the cost improvement from baseline to gold earns 13,750 points, while reaching gold earns 25,000. Costs better than gold remain capped at 25,000.

Private scenarios can change demand over time and by direction or lane. Your controller receives the same state interface on every map, so build a policy that reacts to current traffic instead of identifying specific scenarios.

---

## Español

Este es el reto de Cursor Build Night Málaga. Tu equipo dispone de **105 minutos** para controlar una ciudad modificando un único archivo: `controller.py`.

1. Crea y activa un entorno virtual.
2. Ejecuta `pip install -r requirements.txt`.
3. Ejecuta `python run.py`.
4. Edita `controller.py`; el navegador se actualizará cada vez que guardes.
5. Inicia sesión con el código de tu mesa y ejecuta `python submit.py`.

Puedes realizar hasta **20 envíos únicos**, con una espera de cinco minutos después de cada envío aceptado. Durante el reto, la clasificación provisional combina un 20% de los mapas públicos y un 80% de mapas privados de validación. Al cerrar los envíos, se selecciona automáticamente el mejor envío provisional de cada equipo y se evalúa una sola vez en doce mapas finales secretos, agrupados en seis familias de tráfico. Cada familia aporta el menor de sus dos scores y esos seis resultados se combinan con media geométrica. La clasificación final combina un 20% de la puntuación pública y un 80% de la puntuación final secreta.

El baseline obtiene 10.000 puntos por escenario y el objetivo gold obtiene 25.000. La mejora usa una curva cuadrática: conseguir la mitad de la reducción de coste entre baseline y gold otorga 13.750 puntos; alcanzar gold otorga 25.000, que también es el máximo.

Vehicle artwork is from Kenney's Racing Pack under CC0. See `viewer/assets/KENNEY-LICENSE.txt`.
