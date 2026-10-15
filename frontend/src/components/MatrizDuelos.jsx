import React, { useState } from 'react'

import { celda, matrizDeDuelos } from '../matrizDuelos.js'

/** Una tabla de la matriz: filas el que mata, columnas el que muere. */
function Tabla({ titulo, matriz, filas, columnas }) {
  return (
    <>
      <h3>{titulo}</h3>
      <div className="matriz-scroll">
        <table className="matriz">
          <thead>
            <tr>
              <th />
              {columnas.map((victima) => (
                <th key={victima} scope="col">{victima}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filas.map((autor) => (
              <tr key={autor}>
                <th scope="row">{autor}</th>
                {columnas.map((victima) => {
                  const { bajas, headshots } = celda(matriz, autor, victima)
                  return (
                    <td
                      key={victima}
                      className={bajas ? 'con-dato' : ''}
                      title={`${autor} mató a ${victima} ${bajas} ${bajas === 1 ? 'vez' : 'veces'}`}
                    >
                      {bajas || '·'}
                      {headshots ? <small> ({headshots} HS)</small> : null}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

export default function MatrizDuelos({ rounds, miEquipo }) {
  const [soloAperturas, setSoloAperturas] = useState(false)
  const matriz = matrizDeDuelos(rounds, { soloAperturas, miEquipo })

  return (
    <>
      <div className="round-tabs">
        {[
          [false, 'Todas'],
          [true, 'Solo aperturas'],
        ].map(([valor, etiqueta]) => (
          <button
            key={etiqueta}
            className={`round-tab ${soloAperturas === valor ? 'active' : ''}`}
            onClick={() => setSoloAperturas(valor)}
          >
            <span className="n">{etiqueta}</span>
          </button>
        ))}
      </div>
      {matriz.total === 0 ? (
        <p className="note">Esta partida no registró bajas entre equipos.</p>
      ) : (
        <>
          <Tabla
            titulo="Tu equipo contra el rival"
            matriz={matriz}
            filas={matriz.mios}
            columnas={matriz.rivales}
          />
          <Tabla
            titulo="El rival contra tu equipo"
            matriz={matriz}
            filas={matriz.rivales}
            columnas={matriz.mios}
          />
        </>
      )}
    </>
  )
}
