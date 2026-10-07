import React from 'react'
import { Link } from 'react-router-dom'

import { destinoInsight } from '../filtros.js'

/**
 * El enlace "ver esas rondas" de una senal del coach. Lleva al Resumen con los
 * filtros que respaldan la frase (el mapa, el lado, el operador) encima de los
 * activos, o a Duelos si la senal es de un rival. Si la senal no tiene filtro
 * posible, no se dibuja nada.
 */
export function EnlaceInsight({ insight, filters, children = 'Ver esas rondas →' }) {
  const destino = destinoInsight(insight, filters)
  if (!destino) return null
  return (
    <Link className="insight-link" to={destino}>
      {children}
    </Link>
  )
}
