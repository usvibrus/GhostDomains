// GhostDomains API Client — Production Ready
// Uses relative URLs in production (monolith), absolute in dev

const API_URL = import.meta.env.VITE_API_URL || '/api';

async function apiFetch(url, options = {}) {
  const resp = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: resp.statusText }));
    throw new Error(err.error || resp.statusText);
  }
  return resp.json();
}

export async function fetchDomains(params = {}) {
  const qs = new URLSearchParams();
  if (params.search) qs.set('search', params.search);
  if (params.min_da) qs.set('min_da', params.min_da);
  if (params.min_pa) qs.set('min_pa', params.min_pa);
  if (params.source) qs.set('source', params.source);
  if (params.page) qs.set('page', params.page);
  if (params.per_page) qs.set('per_page', params.per_page);
  if (params.sort) qs.set('sort', params.sort);
  if (params.order) qs.set('order', params.order);
  return apiFetch(`${API_URL}/domains?${qs}`);
}

export async function fetchDomainById(id) {
  return apiFetch(`${API_URL}/domains/${id}`);
}

export async function fetchStats() {
  return apiFetch(`${API_URL}/stats`);
}

export async function fetchChartData() {
  return apiFetch(`${API_URL}/stats/chart`);
}

export async function lookupDomain(domain) {
  return apiFetch(`${API_URL}/domains/lookup`, {
    method: 'POST',
    body: JSON.stringify({ domain }),
  });
}

export async function fetchSavedLists() {
  return apiFetch(`${API_URL}/lists`);
}

export async function createSavedList(name) {
  return apiFetch(`${API_URL}/lists`, {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
}

export async function addDomainToList(listId, domainId, notes = '') {
  return apiFetch(`${API_URL}/lists/${listId}/domains`, {
    method: 'POST',
    body: JSON.stringify({ domain_id: domainId, notes }),
  });
}

export async function fetchWatchers() {
  return apiFetch(`${API_URL}/watchers`);
}

export async function createWatcher(data) {
  return apiFetch(`${API_URL}/watchers`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function deleteWatcher(id) {
  return apiFetch(`${API_URL}/watchers/${id}`, { method: 'DELETE' });
}

export function getExportUrl(format = 'csv', filters = {}) {
  const qs = new URLSearchParams({ format, ...filters });
  return `${API_URL}/domains/export?${qs}`;
}
