import sys
sys.path.insert(0, ".")
import sqlalchemy as sa
from backend.app.auth.database import engine

with engine.connect() as c:
    r = c.execute(sa.text(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name='partidos' ORDER BY ordinal_position"
    ))
    rows = r.fetchall()

print("Columnas de 'partidos':")
for col, dtype in rows:
    print(f"  - {col}  ({dtype})")

expected = [
    "id", "id_jugador_1", "id_jugador_2", "id_ganador",
    "id_usuario_creador", "marcador_final", "duracion_minutos",
    "fecha_jugado", "superficie", "formato_sets", "tiebreak_ultimo_set", "activo"
]
missing = [c for c in expected if c not in [r[0] for r in rows]]
if missing:
    print(f"\nFALTAN columnas: {missing}")
else:
    print("\nEsquema OK - todas las columnas presentes")
