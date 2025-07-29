/**
 * Destination metadata — imagery, framing copy, and palette hints.
 *
 * The `image` ids are Unsplash photo ids, each one visually verified to
 * actually show the place it claims to. Swap `IMG_BASE` for your own CDN
 * (or import local assets) without touching any component.
 *
 * `tint` is the average-ish hue of the photo. It paints the frame *behind*
 * the image so a slow or failed load still reads as an intentional colour
 * block instead of a white hole.
 */

const IMG_BASE = 'https://images.unsplash.com/photo-';

const img = (id, w = 900) =>
  `${IMG_BASE}${id}?auto=format&fit=crop&q=80&w=${w}`;

export const DESTINATIONS = [
  {
    name: 'Jaipur',
    region: 'Rajasthan',
    tagline: 'Pink city palaces and stepwell shadows',
    best: 'Oct – Mar',
    image: img('1477587458883-47145ed94245'),
    tint: '#B4795A',
  },
  {
    name: 'Udaipur',
    region: 'Rajasthan',
    tagline: 'Marble courtyards above Lake Pichola',
    best: 'Sep – Mar',
    image: img('1615836245337-f5b9b2303f10'),
    tint: '#C79B63',
  },
  {
    name: 'Delhi',
    region: 'National Capital',
    tagline: 'Mughal ruins, chaotic bazaars, quiet gardens',
    best: 'Oct – Mar',
    image: img('1587474260584-136574528ed5'),
    tint: '#8C6B85',
  },
  {
    name: 'Goa',
    region: 'Konkan Coast',
    tagline: 'Palm shade, warm surf, long slow evenings',
    best: 'Nov – Feb',
    image: img('1587922546307-776227941871'),
    tint: '#5E9AA3',
  },
  {
    name: 'Manali',
    region: 'Himachal Pradesh',
    tagline: 'Deodar forests under the high Himalaya',
    best: 'Mar – Jun',
    image: img('1626621341517-bbf3d9990a23'),
    tint: '#6E8CA8',
  },
];

/** Asymmetric hero collage — deliberately unequal weights. */
export const HERO_IMAGES = [
  { id: 'amber',    src: img('1599661046289-e31897846e41', 1000), alt: 'Amber Fort rising above Maota Lake at golden hour, Jaipur', tint: '#B9834A', label: 'Amber Fort', place: 'Jaipur' },
  { id: 'taj',      src: img('1548013146-72479768bada', 700),     alt: 'The Taj Mahal framed by a carved sandstone gateway, Agra',  tint: '#A8674A', label: 'Agra',       place: 'Uttar Pradesh' },
  { id: 'pichola',  src: img('1561312514-1d71b2b7e495', 700),     alt: 'A canopied boat crossing Lake Pichola at sunset, Udaipur',  tint: '#C08A4E', label: 'Lake Pichola', place: 'Udaipur' },
  { id: 'parvati',  src: img('1609920658906-8223bd289001', 700),  alt: 'A river running through pine forest in the Himalaya',      tint: '#5F7E86', label: 'Parvati Valley', place: 'Himachal' },
  { id: 'kerala',   src: img('1602216056096-3b40cc0c9944', 700),  alt: 'A houseboat on the palm-lined Kerala backwaters',          tint: '#5C7A4E', label: 'Backwaters', place: 'Kerala' },
];
