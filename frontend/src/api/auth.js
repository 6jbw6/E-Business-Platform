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

/** 上传裁剪好的头像。不手动设 Content-Type，交给浏览器带上 multipart boundary。 */
export function uploadAvatar(blob) {
  const form = new FormData()
  form.append('file', blob, 'avatar.png')
  return http.post('/auth/avatar', form)
}
