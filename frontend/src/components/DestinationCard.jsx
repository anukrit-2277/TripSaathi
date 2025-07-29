import SmartImage from './SmartImage';
import { IconArrow, IconCheck, IconSun } from './icons';

/**
 * A premium destination card.
 *
 * Image treatment: 4:5 portrait crop, a permanent bottom scrim so the
 * overlaid serif name stays legible on both bright (Goa) and dark
 * (Delhi at dusk) photos, and a slow scale on hover. The name sits ON
 * the photo; the supporting copy sits below it on white — that split is
 * what keeps it from looking like a stock template card.
 */
export default function DestinationCard({ destination, isActive, onSelect }) {
  const { name, region, tagline, best, image, tint } = destination;

  return (
    <button
      type="button"
      id={`dest-${name.toLowerCase()}`}
      className={`dest-card ${isActive ? 'active' : ''}`}
      onClick={() => onSelect(name)}
      aria-pressed={isActive}
    >
      <div className="dest-media" style={{ '--card-tint': tint }}>
        <SmartImage src={image} alt={`${name}, ${region}`} />
        {isActive && (
          <span className="dest-badge">Selected</span>
        )}
        <div className="dest-overlay">
          <h3 className="dest-name">{name}</h3>
          <p className="dest-region">{region}</p>
        </div>
      </div>

      <div className="dest-body">
        <p className="dest-tagline">{tagline}</p>
        <div className="dest-foot">
          <span className="dest-best">
            <IconSun />
            Best {best}
          </span>
          <span className="dest-go">
            {isActive ? (<><IconCheck /> Chosen</>) : (<>Plan this <IconArrow /></>)}
          </span>
        </div>
      </div>
    </button>
  );
}
