const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * API client for TripSaathi backend.
 */

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
