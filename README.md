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

Your best valid submission remains on the leaderboard. Total score is 40% public scenarios and 60% hidden scenarios.

---

## Español

Este es el reto de Cursor Build Night Málaga. Tu equipo dispone de **105 minutos** para controlar una ciudad modificando un único archivo: `controller.py`.

1. Crea y activa un entorno virtual.
2. Ejecuta `pip install -r requirements.txt`.
3. Ejecuta `python run.py`.
4. Edita `controller.py`; el navegador se actualizará cada vez que guardes.
5. Inicia sesión con el código de tu mesa y ejecuta `python submit.py`.

El baseline obtiene 10.000 puntos por escenario. Reduce la espera y los vehículos sin terminar para superarlo.

Vehicle artwork is from Kenney's Racing Pack under CC0. See `viewer/assets/KENNEY-LICENSE.txt`.
