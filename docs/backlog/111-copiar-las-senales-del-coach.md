# 111. Copiar las señales del Coach como texto

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: exportar
area: frontend
prioridad: 3
fuente: ALCANCE.md H6
archivos: -
turnos: po 20261112T1128Z-cKKCvKD

## PR

## Que gana quien usa la app

Un boton en Coach copia al portapapeles las señales que se ven (titulo,
numero, muestra y consejo) en texto plano, con los filtros activos en la
primera linea, para pegarlas en el chat del equipo o mandarselas a quien te
entrena. Nada sale de la PC: es el portapapeles, como "Copiar resumen" de la
partida y de la sesion.

## Criterios de aceptacion

- [ ] Funcion pura nueva (p. ej. `frontend/src/textoCoach.js`) que arma el
      texto desde la respuesta de `/api/coach/` y los filtros: primera
      linea con los filtros activos (o "Sin filtros"), una linea o bloque por
      señal en el orden que se muestran, sin HTML. Vitest con dos señales,
      con y sin filtros.
- [ ] Sin señales, el boton no aparece (o queda deshabilitado con la razon
      en `title`). Vitest de la funcion con lista vacia.
- [ ] Sin `navigator.clipboard` (http que no es localhost) el boton avisa
      que no se pudo copiar en vez de romper, igual que el de la partida.
- [ ] e2e: en `/coach` con el seed, el boton copia y el texto copiado
      (leido con `page.evaluate` sobre `navigator.clipboard.readText` con
      el permiso de Chromium, como el e2e que ya prueba "Copiar resumen", o
      espiando `writeText`) contiene el titulo de una señal del seed;
      consola limpia.

## Fuera de alcance

- Exportar a archivo o imagen.
- Copiar las señales del Inicio (el mismo texto puede reusarse despues).
- Backend: `build_insights` ya devuelve todo.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
