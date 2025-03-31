export interface PublicMetadata {
    onboardingComplete?: boolean;
    hasActiveSubscription?: boolean;
    role?: string;
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