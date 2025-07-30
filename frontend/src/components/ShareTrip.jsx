import { useEffect, useState } from 'react';
import { IconShare, IconLink, IconCheck } from './icons';

/**
 * Share panel for a finished plan.
 *
 * The link is the app's own URL with ?trip=<id> appended. A query param
 * rather than a /trip/<id> path on purpose: there is no router in this app,
 * and a real path would also need an SPA-fallback rewrite wherever the
 * frontend is hosted. App.jsx reads the param on mount and pulls the plan
 * back from GET /api/trip/{id}.
 *
 * Only rendered when the trip actually committed to Postgres — see the
 * `shareable` flag on TripResponse. A link to an in-memory-only trip would
 * 404 for the friend who opens it.
 */
export default function ShareTrip({ tripId, destination, days }) {
  const [copied, setCopied] = useState(false);
  const [clipboardBlocked, setClipboardBlocked] = useState(false);

  const url = `${window.location.origin}${window.location.pathname}?trip=${tripId}`;

  // Let the "Copied" confirmation fall back to the idle label on its own.
  useEffect(() => {
    if (!copied) return;
    const t = setTimeout(() => setCopied(false), 2400);
    return () => clearTimeout(t);
  }, [copied]);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setClipboardBlocked(false);
    } catch {
      // navigator.clipboard is undefined on insecure origins and can be
      // permission-denied elsewhere. The input stays selectable, so say so
      // rather than failing silently.
      setClipboardBlocked(true);
    }
  };

  /* The native share sheet is worth having on phones, which is where a
     "send this to a friend" action actually gets used. */
  const canShareNatively = typeof navigator !== 'undefined' && !!navigator.share;

  const shareNatively = async () => {
    try {
      await navigator.share({
        title: `${days}-day trip to ${destination}`,
        text: `Here's our ${days}-day plan for ${destination}, built with TripSaathi.`,
        url,
      });
    } catch (err) {
      // Dismissing the sheet throws AbortError — that is not a failure.
      if (err.name !== 'AbortError') copy();
    }
  };

  return (
    <div className="panel panel-pad share-card" id="share-trip">
      <div className="share-head">
        <span className="share-mark"><IconShare /></span>
        <div>
          <p className="eyebrow">Share this plan</p>
          <p className="share-lede">
            Anyone with the link can open the full itinerary — no account, no sign-in.
          </p>
        </div>
      </div>

      <div className="share-row">
        <label className="share-link">
          <IconLink />
          <input
            type="text"
            readOnly
            value={url}
            aria-label="Shareable link to this trip"
            onFocus={(e) => e.target.select()}
            onClick={(e) => e.target.select()}
          />
        </label>

        <button
          type="button"
          className={`share-copy ${copied ? 'is-copied' : ''}`}
          onClick={copy}
        >
          {copied ? <><IconCheck /> Copied</> : 'Copy link'}
        </button>

        {canShareNatively && (
          <button type="button" className="btn-ghost share-native" onClick={shareNatively}>
            <IconShare /> Share
          </button>
        )}
      </div>

      {clipboardBlocked && (
        <p className="share-warn">
          Your browser blocked the clipboard — tap the link above to select it,
          then copy it manually.
        </p>
      )}
    </div>
  );
}
