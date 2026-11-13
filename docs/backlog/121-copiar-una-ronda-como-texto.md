# 121. Copiar una ronda como texto

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: exportar
area: frontend
prioridad: 3
fuente: ALCANCE.md H10
archivos: -
turnos: po 20261113T1603Z-cHj1H4k

## PR

## Que gana quien usa la app

En la pestaña de una ronda del detalle de partida, un boton copia la ronda
en texto plano (numero, lado, sitio, resultado y la linea de tiempo con
reloj, autor, victima, HS, apertura y trade) para pegarla en Discord al
revisarla con el equipo. Hoy se copia la partida entera (ficha 66) pero no
se baja a una ronda.

## Criterios de aceptacion

- [ ] Funcion pura nueva que arma el texto desde la ronda de
      `/api/matches/<id>/` (`rounds[].events`): primera linea con mapa,
      numero de ronda, lado, sitio y resultado; una linea por baja en orden
      con reloj, autor, victima y marcas (HS, apertura, tradeada); sin HTML
      ni espacios al final de linea. Vitest con una ronda de tres bajas.
- [ ] Una ronda sin bajas copia la primera linea y "Sin bajas"; vitest.
- [ ] Los teamkills y las bajas sin autor (caidas, bomba) salen con la misma
      etiqueta que la linea de tiempo de la pagina; vitest.
- [ ] Sin `navigator.clipboard` el boton avisa que no se pudo copiar, como
      "Copiar resumen" de la partida.
- [ ] e2e: en una partida de `seed_demo`, abrir una ronda, copiar, y el
      texto copiado empieza con la linea de la ronda y contiene el nick de
      una baja de esa ronda; consola limpia.

## Fuera de alcance

- Copiar varias rondas a la vez o un rango.
- Exportar la ronda a archivo o imagen.
- Backend: `/api/matches/<id>/` ya trae todo.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
