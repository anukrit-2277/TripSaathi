import SmartImage from './SmartImage';
import { HERO_IMAGES } from '../data/destinations';
import { IconArrow } from './icons';

/**
 * Hero — asymmetric bento collage, not a full-bleed background photo.
 *
 * The four tiles use deliberately unequal grid spans (see .tile-a…d in
 * index.css) so the arrangement reads as an editorial collage rather
 * than a card grid. A glass chip overlaps the collage edge to break the
 * rectangle and add depth.
 */
export default function Hero({ onStart }) {
  const [amber, taj, pichola, parvati] = HERO_IMAGES;
  const tiles = [
    { ...amber, cls: 'tile-a' },
    { ...taj, cls: 'tile-b' },
    { ...pichola, cls: 'tile-c' },
    { ...parvati, cls: 'tile-d' },
  ];

  return (
    <header className="hero">
      <div className="shell hero-grid">
        <div className="hero-copy">
          <p className="eyebrow">Itineraries for India</p>

          <h1 className="hero-title">
            Every trip deserves a<br />
            <span className="accent">proper plan.</span>
          </h1>

          <p className="hero-lede">
            Tell us where you're going and what you love. Four specialist agents
            research the destination, budget it honestly, build the day-by-day,
            then argue with each other until it's actually good.
          </p>

          <div className="hero-actions">
            <button type="button" className="btn-ghost" onClick={onStart}>
              Start planning
              <IconArrow />
            </button>
            <a className="btn-text" href="#destinations">
              Browse destinations
            </a>
          </div>

          <div className="hero-trust">
            <div className="trust-item">
              <span className="trust-num">5</span>
              <span className="trust-label">Destinations</span>
            </div>
            <div className="trust-item">
              <span className="trust-num">4</span>
              <span className="trust-label">Planning agents</span>
            </div>
            <div className="trust-item">
              <span className="trust-num">~60s</span>
              <span className="trust-label">To a full plan</span>
            </div>
          </div>
        </div>

        <div className="hero-collage-wrap">
          <div className="hero-collage">
            {tiles.map((t) => (
              <figure
                key={t.id}
                className={`tile ${t.cls}`}
                style={{ '--tile-tint': t.tint }}
              >
                <SmartImage src={t.src} alt={t.alt} />
                <figcaption className="tile-caption">
                  <strong>{t.label}</strong>
                  <span>{t.place}</span>
                </figcaption>
              </figure>
            ))}
          </div>

        </div>
      </div>
    </header>
  );
}
