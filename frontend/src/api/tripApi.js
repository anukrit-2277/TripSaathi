const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * API client for TripSaathi backend.
 */

export async function planTrip(tripData) {
  const response = await fetch(`${API_BASE_URL}/api/trip/plan`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(tripData),
  });

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
