export interface Product {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors: string[]
  search_tags: string[]
  price: number
  image_url: string
}

export interface SizeStock {
  size: string
  quantity: number
}

export interface ProductDetail extends Product {
  sizes: SizeStock[]
}

const OFFLINE_MESSAGE = "Can't reach the Campus Customs server. Make sure the backend is running, then try again."

// fetch() only throws when the server can't be reached at all (e.g. the backend is stopped).
async function request(url: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(url, init)
  } catch {
    throw new Error(OFFLINE_MESSAGE)
  }
}

async function getJson<T>(url: string): Promise<T> {
  const res = await request(url)
  if (!res.ok) throw new Error(`Request failed (${res.status})`)
  return res.json() as Promise<T>
}

export const fetchProducts = () => getJson<Product[]>('/api/products')

export const fetchProduct = (id: string) =>
  getJson<ProductDetail>(`/api/products/${encodeURIComponent(id)}`)

export const formatPrice = (price: number) => `$${price.toFixed(2)}`

// ---------- Accounts ----------

export interface User {
  id: number
  first_name: string
  last_name: string
  email: string
}

export interface RegisterInput {
  first_name: string
  last_name: string
  email: string
  password: string
}

async function postJson<T>(url: string, body?: unknown): Promise<T> {
  const res = await request(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const detail = typeof data.detail === 'string' ? data.detail : 'Something went wrong. Please try again.'
    throw new Error(detail)
  }
  return data as T
}

export const fetchMe = () => getJson<{ user: User | null }>('/api/auth/me').then((d) => d.user)

export const login = (email: string, password: string) =>
  postJson<{ user: User }>('/api/auth/login', { email, password }).then((d) => d.user)

export const register = (input: RegisterInput) =>
  postJson<{ user: User }>('/api/auth/register', input).then((d) => d.user)

export const logout = () => postJson<{ ok: boolean }>('/api/auth/logout')

// ---------- Chat ----------

export interface ProductCard {
  product_id: string
  name: string
  garment_type: string
  price: number
  colors: string[]
  image_url: string
}

export interface ChatReply {
  reply: string
  products: ProductCard[]
}

export const sendChat = (message: string) => postJson<ChatReply>('/api/chat', { message })
