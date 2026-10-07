import React, { useEffect, useRef } from 'react'

import { PUNTERO, VUELTA, colorGajo, tamanoLetra } from '../ruleta.js'

/**
 * La rueda dibujada en canvas. Recibe el angulo ya calculado: la animacion la
 * lleva la pagina, aca solo se pinta el cuadro que toca.
 */
export default function Rueda({ operadores, angulo, resaltado, onClick, girando }) {
  const canvasRef = useRef(null)
  const wrapRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const wrap = wrapRef.current
    if (!canvas || !wrap) return undefined

    const pintar = () => {
      const lado = Math.max(220, Math.min(wrap.clientWidth, 560))
      const dpr = window.devicePixelRatio || 1
      // el buffer va en pixeles fisicos para que el texto no salga borroso en
      // pantallas con escala
      canvas.width = Math.round(lado * dpr)
      canvas.height = Math.round(lado * dpr)
      canvas.style.width = `${lado}px`
      canvas.style.height = `${lado}px`
      const ctx = canvas.getContext('2d')
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      dibujarRueda(ctx, lado, operadores, angulo, resaltado)
    }

    pintar()
    const observer = new ResizeObserver(pintar)
    observer.observe(wrap)
    return () => observer.disconnect()
  }, [operadores, angulo, resaltado])

  return (
    <div ref={wrapRef} className="rueda-wrap">
      <canvas
        ref={canvasRef}
        className={`rueda ${girando ? 'girando' : ''}`}
        role="button"
        aria-label="Girar la ruleta"
        tabIndex={0}
        onClick={onClick}
        onKeyDown={(e) => {
          if (e.key === 'Enter') onClick?.()
        }}
      />
    </div>
  )
}

export function dibujarRueda(ctx, lado, operadores, angulo, resaltado) {
  const cx = lado / 2
  const cy = lado / 2
  const radio = lado / 2 - 14
  const n = operadores.length

  ctx.clearRect(0, 0, lado, lado)

  // aro exterior
  ctx.beginPath()
  ctx.arc(cx, cy, radio + 8, 0, VUELTA)
  ctx.fillStyle = '#0b0f15'
  ctx.fill()
  ctx.lineWidth = 2
  ctx.strokeStyle = '#263041'
  ctx.stroke()

  if (!n) {
    ctx.beginPath()
    ctx.arc(cx, cy, radio, 0, VUELTA)
    ctx.fillStyle = '#1d2632'
    ctx.fill()
    ctx.fillStyle = '#8b98a9'
    ctx.font = '600 15px "Segoe UI", Inter, system-ui, sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText('Sin operadores en la rueda', cx, cy)
    return
  }

  const gajo = VUELTA / n
  const letra = tamanoLetra(radio, n)

  for (let i = 0; i < n; i += 1) {
    const desde = angulo + gajo * i
    const elegido = i === resaltado
    ctx.beginPath()
    ctx.moveTo(cx, cy)
    ctx.arc(cx, cy, radio, desde, desde + gajo)
    ctx.closePath()
    ctx.fillStyle = elegido ? '#ff8a3d' : colorGajo(i, operadores[i].side)
    ctx.fill()
    ctx.lineWidth = elegido ? 2.5 : 1
    ctx.strokeStyle = elegido ? '#ffffff' : 'rgba(0,0,0,0.35)'
    ctx.stroke()

    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(desde + gajo / 2)
    ctx.textAlign = 'right'
    ctx.textBaseline = 'middle'
    ctx.font = `700 ${letra}px "Segoe UI", Inter, system-ui, sans-serif`
    ctx.lineJoin = 'round'
    ctx.lineWidth = 3
    ctx.strokeStyle = elegido ? 'rgba(255,255,255,0.85)' : 'rgba(0,0,0,0.75)'
    ctx.strokeText(operadores[i].name, radio - 14, 0)
    ctx.fillStyle = elegido ? '#1a1005' : '#f3f6f9'
    ctx.fillText(operadores[i].name, radio - 14, 0)
    ctx.restore()
  }

  // eje
  const eje = Math.max(26, radio * 0.13)
  ctx.beginPath()
  ctx.arc(cx, cy, eje, 0, VUELTA)
  ctx.fillStyle = '#151b24'
  ctx.fill()
  ctx.lineWidth = 3
  ctx.strokeStyle = '#ff8a3d'
  ctx.stroke()
  ctx.fillStyle = '#ff8a3d'
  ctx.font = `700 ${Math.max(10, Math.round(eje * 0.42))}px "Segoe UI", Inter, system-ui, sans-serif`
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText('GIRAR', cx, cy)

  // puntero: un triangulo fijo arriba, apuntando al centro
  const px = cx + Math.cos(PUNTERO) * (radio + 8)
  const py = cy + Math.sin(PUNTERO) * (radio + 8)
  ctx.beginPath()
  ctx.moveTo(px, py + 22)
  ctx.lineTo(px - 13, py - 8)
  ctx.lineTo(px + 13, py - 8)
  ctx.closePath()
  ctx.fillStyle = '#ff8a3d'
  ctx.fill()
  ctx.lineWidth = 2
  ctx.strokeStyle = '#1a1005'
  ctx.stroke()
}
