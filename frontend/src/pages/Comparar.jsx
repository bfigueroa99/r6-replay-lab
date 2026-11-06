import React from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { useApi } from '../api.js'
import { ErrorBox, Loading, NoExiste, Panel } from '../components/ui.jsx'
import { filasDeComparacion, opcionesParaComparar } from '../compararPartidas.js'

export default function Comparar() {
  const { a, b } = useParams()
  // la key es solo A: cambiar B desde el selector no vuelve a pedir A ni el listado
  return <Pagina key={a} a={a} b={b} />
}

function Pagina({ a, b }) {
  const navigate = useNavigate()
  const partidaA = useApi(`/matches/${a}/`)
  // el listado lo pide solo quien compara, no cada visita al detalle; 200 es el tope de match_list
  const listado = useApi('/matches/', { limit: 200 })

  if (partidaA.status === 404) return <NoExiste titulo="Esa partida no existe" a="/partidas" texto="Ver tus partidas" />
  if (partidaA.error) return <ErrorBox error={partidaA.error} />
  if (!partidaA.data) return <Loading />

  const actual = partidaA.data.match
  const { mismoMapa, otras } = opcionesParaComparar(listado.data?.matches, actual)

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Comparar partidas</h1>
          <p>
            Partida A: {actual.map} · {actual.score} · {actual.played_at.slice(0, 16).replace('T', ' ')}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <select
            aria-label="Comparar con"
            value={b || ''}
            onChange={(e) => e.target.value && navigate(`/comparar/${a}/${e.target.value}`)}
            disabled={!listado.data}
          >
            <option value="">{listado.data ? 'Elegí una partida…' : 'Cargando partidas…'}</option>
            {/* B fuera de las 200 del listado (o la misma A) igual tiene que verse elegida */}
            {b && listado.data && !mismoMapa.concat(otras).some((o) => String(o.id) === String(b)) ? (
              <option value={b}>Partida {b}</option>
            ) : null}
            {mismoMapa.length ? (
              <optgroup label="Mismo mapa">
                {mismoMapa.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.texto}
                  </option>
                ))}
              </optgroup>
            ) : null}
            {otras.length ? (
              <optgroup label="Otras">
                {otras.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.texto}
                  </option>
                ))}
              </optgroup>
            ) : null}
          </select>
          <Link className="btn small" to={`/partidas/${a}`}>
            Ver partida A
          </Link>
          {b ? (
            <Link className="btn small" to={`/partidas/${b}`}>
              Ver partida B
            </Link>
          ) : null}
        </div>
      </div>
      {listado.error ? <ErrorBox error={listado.error} /> : null}

      {b ? (
        // con key: sin ella, al cambiar B se veria la comparacion vieja mientras carga la nueva
        <ConB key={b} b={b} datosA={partidaA.data} />
      ) : (
        <p className="note">Elegí la partida con la que comparar.</p>
      )}
    </>
  )
}

function ConB({ b, datosA }) {
  const partidaB = useApi(`/matches/${b}/`)
  if (partidaB.status === 404) return <NoExiste titulo="Esa partida no existe" a="/partidas" texto="Ver tus partidas" />
  if (partidaB.error) return <ErrorBox error={partidaB.error} />
  if (!partidaB.data) return <Loading />
  const filas = filasDeComparacion(datosA, partidaB.data)

  return (
    <Panel title="Lado a lado" hint="La diferencia se lee desde A: verde si A sale mejor, rojo si sale mejor B.">
      <div className="table-wrap">
        <table className="comparar">
          <thead>
            <tr>
              <th scope="col" className="plain" />
              <th scope="col" className="plain">Partida A</th>
              <th scope="col" className="plain">Partida B</th>
              <th scope="col" className="plain">Diferencia</th>
            </tr>
          </thead>
          <tbody>
            {filas.map((f) => (
              <tr key={f.clave}>
                <th scope="row" className="plain">{f.etiqueta}</th>
                <td>{f.a}</td>
                <td>{f.b}</td>
                <td className={`comparar-dif${f.mejor ? ` mejor-${f.mejor}` : ''}`}>{f.diferencia}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  )
}
