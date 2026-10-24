## Parity: 76.1 / 100

features 76.1  (40 counted, must-haves 12 of 17 done)

Not shippable yet: 5 must-have features are not done.

## By area, weakest first
- historial                     60.0  (2 features)
- ronda                         68.2  (10 features)
- operadores                    68.8  (3 features)
- comparar                      70.0  (3 features)
- mapas                         78.6  (3 features)
- importar                      79.2  (5 features)
- perfil                        79.2  (6 features)
- otros                         83.3  (3 features)
- partida                       90.9  (4 features)
- progreso                     100.0  (1 features)

## Missing, in build order
- [must] importar: Soporte de ranked, unranked y custom, partial  (Match.match_type se importa y la API filtra; falta el selector en Filters.jsx (idea A1))
- [must] mapas: Win rate por sitio de defensa con W-L, partial  (agregados por sitio en el Coach y en el CSV; la pagina de mapas y sitios se retiro a proposito (096fd52))
- [must] operadores: Delta de win rate de un operador contra la base, por mapa y sitio, partial  (Coach compara operador contra tu promedio; el delta por mapa y sitio es la idea O1 y el global O5)
- [must] perfil: Resumen: partidas jugadas, win rate de partida, rondas medias, partidas cerradas y mejor mapa, partial  (Inicio muestra rondas, winrate de rondas, K/D, KPR, aperturas, KST; no winrate de partida, rondas por partida ni mejor mapa (idea R1))
- [must] ronda: Kill feed por ronda con la apertura destacada, partial  (El feed esta y el resumen de la ronda nombra el primer duelo; la linea de la apertura no lleva marca propia en la timeline (idea R4))
- [should] historial: Borrar una partida importada, no  (idea G2 (excluir sin borrar), en decision del humano)
- [should] ronda: Tags o notas por ronda y filtro por tag, no  (idea F2, en decision del humano (POST nuevo))
- [should] comparar: Historial contra un equipo rival concreto, partial  (Rivales repetidos por persona en main; por stack es la idea D4)
- [should] operadores: Ranking de operadores por mapa, partial  (cubierto por O1 (idea))
- [should] partida: Duelos limpios contra trades que se escapan, por equipo, en la partida, partial  (MatchDetail da tus muertes sin trade y trades por jugador; no compara los dos equipos (idea R2))
- [should] ronda: Bajas y muertes en tramos de 30 s (early, mid, late), partial  (Cuando mueres por tramos de 30 s esta en main; cuando matas es la ficha 62; por partida no existe (idea R3))
- [should] ronda: Como cambia la ventaja numerica dentro de la ronda, partial  (el resumen de la ronda da segundos en inferioridad; la tira de vivos es la idea F13)
- [could] importar: Carga manual de resultados de partida, no  (la app solo lee .rec; un POST nuevo seria decision del humano)
- [could] otros: Tema claro u oscuro y color de equipo, no  (la UI tiene un solo tema)
- [could] perfil: Deteccion del rol del jugador, no  (idea O2)
- [could] ronda: Playlists de rondas para revisar, no  (buscador de rondas F1 (idea))
- [could] comparar: Operadores y sitios preferidos del rival, partial  (Duelos por operador rival; meta rival por mapa y sitio es la idea D2)
- [could] ronda: Analisis de ronda en fases early, mid y execute, partial  (tramos de 30 s en Cuando mueres; ver R3)

## Left out on purpose (not scored)
- Importar replays desde Google Drive: nube y cuentas: no-goal de CLAUDE.md
- Subida masiva por API key: cuentas y servicio remoto: no-goal; la importacion local ya es masiva
- Cargar partida desde captura de pantalla (OCR): necesita una dependencia de OCR (CLAUDE.md: sin dependencias nuevas)
- Plants y defuses con el jugador que los hizo: plants y defuses de temporadas nuevas no vienen en el .rec (CLAUDE.md, formato-rec.md); solo plant probable inferido del reloj
- Resultado de la ronda cruzado con el momento del plant: mismo motivo: plants fuera del .rec en temporadas nuevas
- Reporte de preparacion contra un rival: scouting de rivales fuera de tus replays vive en la API de Ubisoft (CLAUDE.md)
- Recorridos de jugadores sobre el plano del mapa: coordenadas: el .rec no las entrega (CLAUDE.md)
- Heatmaps de posiciones: coordenadas: el .rec no las entrega (CLAUDE.md)
- Visor 2D del replay: coordenadas: el .rec no las entrega (CLAUDE.md)
- Visualizador de setups defensivos: necesita posiciones y utilidad, que el .rec no entrega
- Stats de post-plant y retakes: plants fuera del .rec en temporadas nuevas
- Sincronizar audio de Discord con el replay: captura de audio y servicio externo: fuera de alcance
- Dashboard de torneo con overlays de broadcast: overlay: no-goal absoluto de CLAUDE.md
- Hub publico de partidas oficiales: nube y datos fuera de tus replays: no-goal
- Leaderboards globales o por rango: rango y jugadores fuera de tus replays viven en la API de Ubisoft
- Cuenta con login y recuperacion de password: cuentas de la propia app: no-goal
- Espacio de equipo u organizacion con historial compartido: nube y cuentas: no-goal
- Planes pagos y almacenamiento extra: la app no se vende ni guarda nada fuera del PC
- Borrar la cuenta y sus datos: sin cuentas; los datos viven en el PC
- Consentimiento de analytics: telemetria: no-goal
- Revision comunitaria anti-cheat (SiegeWatch): comunidad en la nube; no es analisis de tus replays
