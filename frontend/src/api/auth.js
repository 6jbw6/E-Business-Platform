import http from './http'

export function login(payload) {
  return http.post('/auth/login', payload)
}

export function register(payload) {
  return http.post('/auth/register', payload)
}

export function fetchCurrentUser(config = {}) {
  return http.get('/auth/me', config)
}

export function updateProfile(payload) {
  return http.put('/auth/me', payload)
}
