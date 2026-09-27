export function parseCollection(title: string): string {
  const t = title.toUpperCase();
  if (t.includes("AUTOMATIC")) return "Automatic";
  if (t.includes("STELLAR")) return "Stellar";
  if (t.includes("TAREEQ")) return "Tareeq";
  if (t.includes("KOHINOOR")) return "Kohinoor";
  if (t.includes("SANGAM")) return "Sangam";
  if (t.includes("JANATA")) return "Janata";
  if (t.includes("PILOT")) return "Pilot";
  if (t.includes("SONA")) return "Sona";
  if (t.includes("HIMALAYA")) return "Himalaya";
  if (t.includes("KEDAR")) return "Kedar";
  if (t.includes("ROHINI")) return "Rohini";
  if (t.includes("GANDABERUNDA")) return "Gandaberunda";
  if (t.includes("SOUMYA")) return "Soumya";
  if (t.includes("ELEGANCE")) return "Elegance";
  if (t.includes("QUARTZ")) return "Quartz";
  if (t.includes("MECHANICAL")) return "Mechanical";
  return "Classic";
}

export function parseColor(title: string): string {
  const colors = [
    "Sunray Blue",
    "Ice Blue",
    "Tiffany Blue",
    "Turquoise",
    "Blue",
    "Green",
    "Yellow",
    "Gold",
    "Silver",
    "Black",
    "White",
    "Maroon",
    "Red",
    "Champagne",
    "Salmon",
    "Pink",
    "Brown",
    "Grey",
  ];
  for (const c of colors) {
    if (title.toLowerCase().includes(c.toLowerCase())) {
      return c;
    }
  }
  return "Standard";
}

export function formatPrice(price?: number | null): string {
  if (price === null || price === undefined || isNaN(price)) {
    return "N/A";
  }
  return `₹${price.toLocaleString("en-IN")}`;
}

export function formatTimeAgo(isoString?: string | null): string {
  if (!isoString) return "Recently";
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);

  if (diffSecs < 60) return "Just now";
  const diffMins = Math.floor(diffSecs / 60);
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

export function formatCountdown(seconds: number): string {
  if (seconds <= 0) return "Imminent";
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  if (mins === 0) return `${secs}s`;
  return `${mins}m ${secs}s`;
}

export function cleanStoreName(url: string, siteName?: string): string {
  if (siteName) return siteName;
  if (url.includes("hmtwatches.store")) return "hmtwatches.store";
  return "hmtwatches.in";
}
