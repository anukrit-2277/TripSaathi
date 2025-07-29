import { useState } from 'react';

/**
 * An <img> that fades in once decoded, over a solid tint block.
 *
 * Why bother: a grid of photos that pop in at different moments looks
 * broken, and a white gap before load reads as a bug. The parent paints
 * `tint` (the photo's own dominant colour), the image fades over it, and
 * a failed load simply stays as an intentional colour block.
 */
export default function SmartImage({ src, alt, className = '', ...rest }) {
  const [loaded, setLoaded] = useState(false);

  return (
    <img
      src={src}
      alt={alt}
      loading="lazy"
      decoding="async"
      onLoad={() => setLoaded(true)}
      /* Leave it hidden on error so the tint block shows through. */
      onError={() => setLoaded(false)}
      className={`${className} ${loaded ? 'is-loaded' : ''}`.trim()}
      {...rest}
    />
  );
}
