const TOKEN_KEY = 'rd_token';

export function setSessionToken(token) {
  document.cookie = `${TOKEN_KEY}=${encodeURIComponent(token)}; Path=/; SameSite=Lax`;
}

export function getSessionToken() {
  const token = document.cookie
    .split('; ')
    .find((part) => part.startsWith(`${TOKEN_KEY}=`))
    ?.split('=')[1];
  return token ? decodeURIComponent(token) : null;
}

export function clearSessionToken() {
  document.cookie = `${TOKEN_KEY}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; Path=/;`;
}
