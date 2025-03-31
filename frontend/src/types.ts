export interface PublicMetadata {
  subscription_status?: string; // e.g., "active", "inactive"
  subscription_plan?: string; // e.g., "Professional", "Basic"
  subscription_end?: string; // ISO date string
  last_checked?: string; // ISO date string
  onboardingComplete?: boolean; // Optional
  [key: string]: any; // Allow additional metadata fields
}
  
export interface SessionClaims {
    publicMetadata?: PublicMetadata;
  }

export interface User {
    id: number;
    clerk_id: string;
    email: string;
    company?: string;
    role: 'owner' | 'developer' | 'other';
    onboarding_completed: boolean;
    email_verified: boolean;
    created_at: string;
    updated_at: string;
}

export interface OnboardingData {
    company: string;
    role: 'owner' | 'developer' | 'other';
}