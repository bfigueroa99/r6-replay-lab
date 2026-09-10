/**
 * Preload. Corre en sandbox y expone lo minimo: un flag para que la UI sepa
 * que esta en la app de escritorio y no en el navegador.
 *
 * No se expone nada que toque el disco ni que ejecute procesos: la UI solo
 * habla con la API por HTTP, igual que en el navegador.
 */

const { contextBridge } = require('electron')

contextBridge.exposeInMainWorld('r6desktop', {
  electron: process.versions.electron,
})
