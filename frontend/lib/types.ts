// Shared types for Minitender frontend

export interface User {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  company: string;
  phone: string;
}

export interface Address {
  id: number;
  address: string;
  city: string;
  region: string;
  latitude: number | null;
  longitude: number | null;
  is_default: boolean;
}

export interface RequestItem {
  id: number;
  name: string;
  quantity: number;
  unit: string;
  category: string;
  brand: string;
  spec: string;
  confidence: number;
  is_confirmed: boolean;
}

export interface Request {
  id: number;
  code: string;
  status: string;
  raw_text: string;
  comment: string;
  address: Address | null;
  items: RequestItem[];
  created_at: string;
  updated_at: string;
}

export interface SupplierMatch {
  supplier_id: number;
  name: string;
  email: string;
  phone: string;
  site: string;
  city: string;
  distance_km: number | null;
  total_score: number;
  category_score: number;
  distance_score: number;
  manufacturer_bonus: number;
  supplier_type: string;
  source: string;
  latitude: number | null;
  longitude: number | null;
}

export interface QuoteItem {
  id: number;
  request_item: number;
  material_name: string;
  price: number;
  is_analog: boolean;
  brand: string;
}

export interface Quote {
  id: number;
  request: number;
  supplier: number;
  supplier_name: string;
  status: string;
  delivery_cost: number | null;
  delivery_time: string;
  payment_terms: string;
  comment: string;
  items: QuoteItem[];
  created_at: string;
}

export interface CompetitiveSheetItem {
  supplier_id: number;
  supplier_name: string;
  materials_total: number;
  delivery: number;
  grand_total: number;
  payment_terms: string;
  delivery_time: string;
}

export interface ApiError {
  detail?: string;
  error?: string;
  [key: string]: unknown;
}
