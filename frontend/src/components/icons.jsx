/**
 * Inline stroke icons — 24x24 grid, currentColor, no dependency.
 *
 * Kept in one file so weight and joins stay consistent; a mix of
 * icon sets is one of the fastest ways to make a UI look assembled
 * rather than designed.
 */

const base = {
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.75,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
};

export const IconPin = (p) => (
  <svg {...base} {...p}><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0116 0z" /><circle cx="12" cy="10" r="3" /></svg>
);

export const IconCheck = (p) => (
  <svg {...base} strokeWidth="2.5" {...p}><polyline points="20 6 9 17 4 12" /></svg>
);

export const IconArrow = (p) => (
  <svg {...base} {...p}><line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" /></svg>
);

export const IconChevron = (p) => (
  <svg {...base} {...p}><polyline points="6 9 12 15 18 9" /></svg>
);

export const IconClock = (p) => (
  <svg {...base} {...p}><circle cx="12" cy="12" r="9" /><polyline points="12 7 12 12 15 14" /></svg>
);

export const IconCalendar = (p) => (
  <svg {...base} {...p}><rect x="3" y="5" width="18" height="16" rx="2" /><line x1="3" y1="10" x2="21" y2="10" /><line x1="8" y1="3" x2="8" y2="7" /><line x1="16" y1="3" x2="16" y2="7" /></svg>
);

export const IconUsers = (p) => (
  <svg {...base} {...p}><path d="M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 00-3-3.87" /><path d="M16 3.13a4 4 0 010 7.75" /></svg>
);

export const IconWallet = (p) => (
  <svg {...base} {...p}><path d="M20 12V8a2 2 0 00-2-2H5a2 2 0 010-4h12" /><path d="M3 6v12a2 2 0 002 2h13a2 2 0 002-2v-4" /><circle cx="17" cy="14" r="1.25" /></svg>
);

export const IconSearch = (p) => (
  <svg {...base} {...p}><circle cx="11" cy="11" r="7" /><line x1="16.5" y1="16.5" x2="21" y2="21" /></svg>
);

export const IconCar = (p) => (
  <svg {...base} {...p}><path d="M5 17h14M4 17V11l2-5h12l2 5v6" /><circle cx="7.5" cy="17" r="1.75" /><circle cx="16.5" cy="17" r="1.75" /></svg>
);

export const IconFork = (p) => (
  <svg {...base} {...p}><path d="M6 3v7a2 2 0 002 2v9" /><path d="M10 3v7" /><path d="M6 3v4" /><path d="M17 3c-1.5 2-2 4-2 6s1 3 2 3v9" /></svg>
);

export const IconSparkle = (p) => (
  <svg {...base} {...p}><path d="M12 3l1.9 5.6L19.5 10l-5.6 1.9L12 17.5l-1.9-5.6L4.5 10l5.6-1.4L12 3z" /></svg>
);

export const IconDoc = (p) => (
  <svg {...base} {...p}><path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8z" /><polyline points="14 3 14 8 19 8" /></svg>
);

export const IconSun = (p) => (
  <svg {...base} {...p}><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></svg>
);
