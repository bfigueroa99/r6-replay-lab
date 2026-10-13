/**
 * Preload. Corre en sandbox y expone lo minimo para la pagina Ajustes: un flag
 * para que la UI sepa que esta en la app de escritorio, el selector de carpetas
 * nativo y "abrir en el Explorador".
 *
 * Ninguno lee ni escribe el disco desde la pagina. El selector solo devuelve la
 * ruta que eligio el usuario (la guarda la API, que la valida), y abrir recibe
 * un nombre (`replays`, `copias`, `datos`), no una ruta: la ruta la decide el
 * proceso principal preguntandole al backend, asi la pagina no puede abrir
 * cualquier cosa.
 */

const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('r6desktop', {
  electron: process.versions.electron,
  elegirCarpeta: (desde) => ipcRenderer.invoke('r6:elegir-carpeta', desde),
  abrirCarpeta: (cual) => ipcRenderer.invoke('r6:abrir-carpeta', cual),
})
