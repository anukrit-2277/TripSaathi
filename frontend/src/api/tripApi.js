/**
 * API client for TripSaathi backend.
 */

/* Where the API lives.
 *
 * VITE_API_BASE_URL still wins when it is set, but the fallback is now
 * environment-aware instead of always localhost. Vite inlines these at BUILD
 * time, so a production bundle built without the variable — a missing env var
 * on the host, a preview deploy, a fresh clone — used to ship pointing at the
 * developer's own machine and fail for every visitor with "Could not reach
 * the server". Baking the deployed URL in as the production default makes the
 * env var an override rather than a requirement.
 */
const PROD_API_BASE_URL = 'https://tripsaathi-390970881686.asia-south1.run.app';

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL?.trim() ||
  (import.meta.env.PROD ? PROD_API_BASE_URL : 'http://localhost:8000')
).replace(/\/+$/, '');  // a trailing slash would double up against '/api/...'

export async function planTrip(tripData) {
  // The backend workflow can take 60-180s. We give it up to 4 minutes,
  // then abort cleanly so the UI shows a real error instead of the browser
  // silently killing the socket.
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 240_000);

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/trip/plan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(tripData),
      signal: controller.signal,
    });
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error(
        'The server took too long to respond (>4 min). It may be waking up or rate-limited. Please try again.'
      );
    }
    throw new Error(
      `Could not reach the server. Check your connection or try again. (${err.message})`
    );
  } finally {
    clearTimeout(timeoutId);
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP error ${response.status}`);
  }

  return response.json();
}

export async function getTrip(tripId) {
  const response = await fetch(`${API_BASE_URL}/api/trip/${tripId}`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Trip not found' }));
    throw new Error(error.detail || `HTTP error ${response.status}`);
  }

  return response.json();
}
