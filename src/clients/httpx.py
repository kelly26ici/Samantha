import httpx

httpx = httpx.AsyncClient(
  timeout=30,
  follow_redirects=True)
  