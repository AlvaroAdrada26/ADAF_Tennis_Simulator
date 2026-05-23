/**
 * auth.js — Validación de sesión al cargar la página.
 *
 * Si hay token en localStorage, llama a GET /api/auth/me para:
 *   1. Comprobar que el token sigue siendo válido.
 *   2. Actualizar los datos del usuario en localStorage (por si cambiaron en BD).
 *
 * Si el token es inválido/expirado, limpia localStorage y redirige a /.
 *
 * Dispara el evento 'auth:ready' en document cuando termina, con
 *   detail.authenticated = true/false
 * para que las páginas sepan cuándo usar los datos.
 */
(function () {
  'use strict';

  const token = localStorage.getItem('access_token');

  if (!token) {
    //No hay sesion — nada que validar
    //setTimeout para que los scripts de página registren sus listeners primero
    setTimeout(function () {
      document.dispatchEvent(new CustomEvent('auth:ready', { detail: { authenticated: false } }));
    }, 0);
    return;
  }

  fetch('/api/auth/me', {
    headers: { 'Authorization': 'Bearer ' + token }
  })
    .then(function (resp) {
      if (!resp.ok) throw new Error(resp.status);
      return resp.json();
    })
    .then(function (freshUser) {
      //Actualizar datos del usuario en localStorage
      localStorage.setItem('user', JSON.stringify(freshUser));
      document.dispatchEvent(new CustomEvent('auth:ready', { detail: { authenticated: true, user: freshUser } }));
    })
    .catch(function () {
      //Token invalido o expirado — limpiar sesión
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      document.dispatchEvent(new CustomEvent('auth:ready', { detail: { authenticated: false } }));
    });
})();
