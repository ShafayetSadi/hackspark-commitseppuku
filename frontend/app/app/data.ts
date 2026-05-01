// RentPi placeholder data — ported from hackathon/project/data.jsx
// Used across the dashboard, products, availability, trending, and chat pages.

export const CATEGORIES = [
  "Electronics",
  "Vehicles",
  "Tools",
  "Outdoor",
  "Sports",
  "Music",
  "Furniture",
  "Cameras",
  "Office",
] as const;

export type Category = (typeof CATEGORIES)[number];

export const CATEGORY_HUE: Record<Category, number> = {
  Electronics: 220,
  Vehicles: 25,
  Tools: 45,
  Outdoor: 145,
  Sports: 0,
  Music: 280,
  Furniture: 30,
  Cameras: 200,
  Office: 260,
};

export type Product = {
  id: number;
  name: string;
  category: Category;
  price: number;
  owner: number;
  desc: string;
};

export const PRODUCTS: Product[] = [
  { id: 1042, name: "Premium Camera Kit", category: "Cameras", price: 450, owner: 5021, desc: "Full-frame mirrorless body with 24-70mm lens, two batteries, and a hard case." },
  { id: 1088, name: "Outdoor Camping Tent", category: "Outdoor", price: 300, owner: 1882, desc: "4-person dome tent with rainfly, footprint, and aluminum poles." },
  { id: 1156, name: "Electric Drill Set", category: "Tools", price: 180, owner: 7341, desc: "20V cordless drill with 60-piece bit set and two batteries." },
  { id: 1201, name: "DJ Mixer Console", category: "Music", price: 620, owner: 3344, desc: "4-channel mixer with built-in effects, suitable for events up to 200 people." },
  { id: 1233, name: "Mountain Bike — Trail", category: "Vehicles", price: 540, owner: 2210, desc: "Hardtail aluminum frame, 29\" wheels, 12-speed drivetrain. Helmet included." },
  { id: 1278, name: "Standing Desk — Adjustable", category: "Furniture", price: 220, owner: 4419, desc: "Electric height-adjustable desk, 60\" wide. Memory presets." },
  { id: 1305, name: "Drone with 4K Camera", category: "Electronics", price: 780, owner: 6612, desc: "30-minute flight time, gimbal-stabilized 4K, two extra batteries." },
  { id: 1340, name: "Tennis Racket — Pro Series", category: "Sports", price: 95, owner: 8821, desc: "Pro-grade graphite frame, fresh string, two grips." },
  { id: 1389, name: "Conference Room Projector", category: "Office", price: 410, owner: 5512, desc: "4000-lumen short-throw, HDMI + wireless casting." },
  { id: 1421, name: "Pro Camera Lens — 70-200", category: "Cameras", price: 520, owner: 5021, desc: "f/2.8 telephoto zoom with image stabilization." },
  { id: 1455, name: "Acoustic Guitar — Studio", category: "Music", price: 240, owner: 7790, desc: "Solid spruce top, hardshell case, capo and tuner included." },
  { id: 1490, name: "Portable Speaker Kit", category: "Electronics", price: 320, owner: 6612, desc: "Two 12\" speakers + sub, suitable for indoor/outdoor events." },
  { id: 1512, name: "Snowboard — All Mountain", category: "Sports", price: 380, owner: 9981, desc: "156cm board, bindings, and boots size 10." },
  { id: 1547, name: "Office Chair — Ergonomic", category: "Furniture", price: 140, owner: 4419, desc: "Mesh back, lumbar support, adjustable arms." },
  { id: 1583, name: "SUV — Family 7 Seater", category: "Vehicles", price: 2400, owner: 1101, desc: "Full insurance included. Daily mileage cap 200km." },
  { id: 1620, name: "Pressure Washer — 3000 PSI", category: "Tools", price: 220, owner: 7341, desc: "Gas-powered, 4 nozzle attachments, 25ft hose." },
];

export type TrendingItem = {
  id: number;
  name: string;
  category: Category;
  score: number;
  note: string;
};

export const TRENDING: TrendingItem[] = [
  { id: 1088, name: "Elite Camping Tent", category: "Outdoor", score: 24, note: "Popular this season" },
  { id: 1421, name: "Pro Camera Lens", category: "Cameras", score: 19, note: "Frequently rented now" },
  { id: 1490, name: "Portable Speaker Kit", category: "Electronics", score: 17, note: "Trending nearby" },
  { id: 1233, name: "Mountain Bike — Trail", category: "Vehicles", score: 15, note: "Rising this week" },
  { id: 1340, name: "Tennis Racket — Pro", category: "Sports", score: 13, note: "Steady demand" },
  { id: 1305, name: "Drone with 4K Camera", category: "Electronics", score: 11, note: "New favorite" },
];

export type BusyPeriod = {
  start: number;
  end: number;
  by: string;
};

export const BUSY_PERIODS: Record<number, BusyPeriod[]> = {
  1042: [
    { start: 3, end: 6, by: "Renter #2210" },
    { start: 12, end: 14, by: "Renter #4419" },
    { start: 22, end: 26, by: "Renter #1101" },
  ],
  1088: [{ start: 8, end: 11, by: "Renter #6612" }],
  1156: [],
};

export type ChatSession = {
  id: string;
  title: string;
  time: string;
};

export const CHAT_SESSIONS: ChatSession[] = [
  { id: "s1", title: "Peak Electronics Rental Period", time: "2h ago" },
  { id: "s2", title: "Outdoor Gear Availability", time: "Yesterday" },
  { id: "s3", title: "Discount Tier Question", time: "2 days ago" },
  { id: "s4", title: "Trending Products Today", time: "5 days ago" },
];

export const SUGGESTED_PROMPTS = [
  "Which products are trending today?",
  "Is product 1042 available next week?",
  "Which category has the most rentals?",
  "Show me peak rental periods for cameras.",
  "How does my discount tier work?",
  "Recommend something for a weekend getaway.",
];

export type PageId =
  | "dashboard"
  | "products"
  | "availability"
  | "trending"
  | "chat"
  | "profile"
  | "analytics";

export type CategoryFilter = Category | "All";
