import React, { useState } from 'react'

import { post, useApi } from '../api.js'
import { DataTable, ErrorBox, Loading, Panel } from '../components/ui.jsx'

/**
 * Lo que antes pedia editar un .env o abrir una consola: la carpeta de
 * replays, la importacion automatica y las copias de la base. Todo se guarda en
 * el mismo .env y se aplica sin reiniciar.
 *
 * En la app de escritorio el preload expone un selector de carpetas nativo y
 * un "abrir en el Explorador"; en el navegador esos botones no aparecen y la
 * ruta se escribe a mano.
 */

const ORIGEN = {
  elegida: 'Elegida por ti',
  detectada: 'Encontrada sola',
  no_encontrada: 'No encontrada',
}

const mb = (bytes) => `${(bytes / (1024 * 1024)).toFixed(1)} MB`
const hora = (iso) => (iso ? iso.slice(11, 19) : '—')
const plural = (n, uno, varios) => `${n} ${n === 1 ? uno : varios}`

export default function Ajustes({ onCambio }) {
  const ajustes = useApi('/settings/')
  // los POST ya devuelven el estado completo: se usa ese y no se recarga, asi
  // el input no muestra la ruta vieja mientras llega la respuesta del GET
  const [estado, setEstado] = useState(null)
  const [borrador, setBorrador] = useState(null)
  const [ocupado, setOcupado] = useState(null)
  const [flash, setFlash] = useState(null)
  const escritorio = window.r6desktop

  if (ajustes.error) return <ErrorBox error={ajustes.error} />
  if (ajustes.loading && !ajustes.data) return <Loading />

  const data = estado ?? ajustes.data
  const carpeta = borrador ?? data.replay_dir
  const auto = data.auto_import
  const copias = data.backups

  /** Corre una accion, muestra su resultado y refresca lo que se ve. */
  const accion = async (cual, fn) => {
    setOcupado(cual)
    setFlash(null)
    try {
      setFlash({ ok: true, text: await fn() })
    } catch (err) {
      setFlash({ ok: false, text: err.message })
    } finally {
      setOcupado(null)
    }
  }

  const guardarCarpeta = (ruta) =>
    accion('carpeta', async () => {
      const nuevo = await post('/settings/', undefined, { replay_dir: ruta })
      setEstado(nuevo)
      setBorrador(null)
      // la cabecera y el Resumen miran si la carpeta existe: que se enteren
      onCambio?.()
      if (nuevo.replay_dir_source !== 'elegida') {
        return nuevo.replay_dir_exists
          ? `La encontré sola: ${nuevo.replay_dir}`
          : 'No la encontré sola. Elígela a mano.'
      }
      return (
        `Carpeta guardada: ${nuevo.replay_dir}. ` +
        `${plural(nuevo.replay_dir_folders, 'partida', 'partidas')} adentro.`
      )
    })

  const elegirCarpeta = async () => {
    const ruta = await escritorio.elegirCarpeta(data.replay_dir_exists ? data.replay_dir : undefined)
    if (ruta) guardarCarpeta(ruta)
  }

  const abrir = async (cual) => {
    const error = await escritorio.abrirCarpeta(cual)
    if (error) setFlash({ ok: false, text: error })
  }

  const cambiarAuto = () =>
    accion('auto', async () => {
      const nuevo = await post('/settings/', undefined, { auto_import: !auto.enabled })
      setEstado(nuevo)
      return nuevo.auto_import.enabled
        ? 'Importación automática prendida.'
        : 'Importación automática apagada: importa con el botón de arriba.'
    })

  const copiarAhora = () =>
    accion('copia', async () => {
      const copia = await post('/backup/', undefined, {})
      setEstado({ ...data, backups: copia.backups })
      const borradas = copia.removed.length
        ? ` Se borraron ${plural(copia.removed.length, 'copia vieja', 'copias viejas')}.`
        : ''
      return `Copia lista: ${copia.name} (${mb(copia.size)}).${borradas}`
    })

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Ajustes</h1>
          <p>
            Todo lo que antes pedía editar un <code>.env</code> o abrir una consola. Se guarda en{' '}
            <code>{data.env_file}</code> y se aplica al instante, sin reiniciar.
          </p>
        </div>
      </div>

      {flash ? <div className={`flash ${flash.ok ? '' : 'bad'}`}>{flash.text}</div> : null}

      <Panel
        title="Carpeta de replays"
        hint={
          'La carpeta MatchReplay donde Siege deja los replays. La app la busca sola en Steam, ' +
          'Ubisoft Connect y las rutas típicas de cada disco; si no la encuentra o tienes el ' +
          'juego en otro lado, elígela acá.'
        }
      >
        <div className="ajustes-estado">
          <span className={`chip ${data.replay_dir_exists ? 'win' : 'loss'}`}>
            {data.replay_dir_exists
              ? plural(data.replay_dir_folders, 'partida en disco', 'partidas en disco')
              : 'No existe en este PC'}
          </span>
          <span className="chip">{ORIGEN[data.replay_dir_source] || data.replay_dir_source}</span>
        </div>
        <form
          className="ajustes-carpeta"
          onSubmit={(event) => {
            event.preventDefault()
            guardarCarpeta(carpeta)
          }}
        >
          <input
            type="text"
            aria-label="Carpeta de replays"
            value={carpeta}
            onChange={(event) => setBorrador(event.target.value)}
            spellCheck={false}
          />
          <div className="ajustes-botones">
            {escritorio?.elegirCarpeta ? (
              <button
                type="button"
                className="btn primary small"
                onClick={elegirCarpeta}
                disabled={ocupado === 'carpeta'}
              >
                Elegir carpeta…
              </button>
            ) : null}
            <button
              type="submit"
              className="btn small"
              disabled={ocupado === 'carpeta' || carpeta === data.replay_dir || !carpeta.trim()}
            >
              Guardar
            </button>
            {data.replay_dir_source === 'elegida' ? (
              <button
                type="button"
                className="btn small"
                onClick={() => guardarCarpeta(null)}
                disabled={ocupado === 'carpeta'}
              >
                Buscarla sola
              </button>
            ) : null}
            {escritorio?.abrirCarpeta && data.replay_dir_exists ? (
              <button type="button" className="btn small" onClick={() => abrir('replays')}>
                Abrir en el Explorador
              </button>
            ) : null}
          </div>
        </form>
      </Panel>

      <Panel
        title="Importación automática"
        hint={
          `Revisa la carpeta cada ${auto.interval} s e importa cada partida ` +
          `${auto.quiet_seconds} s después de que termine. Al abrir la app importa lo que ` +
          'jugaste desde la última vez, así que no hace falta apretar Importar replays.'
        }
      >
        <label className="ajuste check">
          <input
            type="checkbox"
            checked={auto.enabled}
            onChange={cambiarAuto}
            disabled={ocupado === 'auto'}
          />
          <span>
            <b>Importar solas las partidas nuevas</b>
            <br />
            {!auto.enabled
              ? 'Apagada: las partidas se importan solo con el botón de arriba.'
              : auto.running
                ? `Vigilando la carpeta. Última revisión a las ${hora(auto.last_check)}.`
                : 'Prendida, pero este servidor no vigila la carpeta: eso lo hace la app de ' +
                  'escritorio (o python serve.py). Con manage.py runserver, deja corriendo ' +
                  'manage.py watch_replays.'}
          </span>
        </label>
      </Panel>

      <Panel
        title="Copias de seguridad"
        hint={
          'El juego va borrando los replays viejos, así que lo que ya importaste puede no estar ' +
          `más en disco. La app hace sola una copia de la base cada ${copias.every_days} días al ` +
          `abrir y guarda las últimas ${copias.keep}.`
        }
        right={
          <button
            className="btn primary small"
            onClick={copiarAhora}
            disabled={ocupado === 'copia'}
          >
            {ocupado === 'copia' ? 'Copiando...' : 'Hacer una copia ahora'}
          </button>
        }
      >
        <DataTable
          columns={[
            { key: 'name', label: 'Copia', left: true },
            {
              key: 'created_at',
              label: 'Cuándo',
              render: (row) => row.created_at.slice(0, 16).replace('T', ' '),
            },
            { key: 'size', label: 'Tamaño', render: (row) => mb(row.size) },
          ]}
          rows={copias.items}
          initialSort={{ key: 'created_at', dir: 'desc' }}
          rowKey={(row) => row.name}
          empty="Todavía no hay copias."
        />
        <div className="ajustes-pie">
          <span className="note">
            En <code>{copias.dir}</code>
          </span>
          {escritorio?.abrirCarpeta && copias.items.length ? (
            <button type="button" className="btn small" onClick={() => abrir('copias')}>
              Abrir carpeta
            </button>
          ) : null}
        </div>
      </Panel>

      <Panel title="Datos de la app">
        <div className="ajustes-pie">
          <span className="note">
            La base, las etiquetas y las copias viven en <code>{data.data_dir}</code>. Desinstalar
            la app no las borra.
          </span>
          {escritorio?.abrirCarpeta ? (
            <button type="button" className="btn small" onClick={() => abrir('datos')}>
              Abrir carpeta
            </button>
          ) : null}
        </div>
      </Panel>
    </>
  )
}
