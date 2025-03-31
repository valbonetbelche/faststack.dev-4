import {
  clerkMiddleware,
  createRouteMatcher,
} from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';
import type { NextRequest } from "next/server";
import type { PublicMetadata, SessionClaims } from './types'; // Import the types
import { api } from "@/lib/api";

const SUBSCRIPTION_PATHS = [
  '/notes',
  '/api/notes'
];

const publicRoutes = createRouteMatcher([
  '/',
  '/sign-up(.*)',
  '/sign-in(.*)',
  '/pricing',
  '/about',
  '/contact',
  '/api/public(.*)'
]);

export default clerkMiddleware(async (auth, req) => {
  const authData = await auth();
  const { userId, sessionClaims, getToken } = authData;
  const pathname = req.nextUrl.pathname;

  // Explicitly type sessionClaims
  const claims: SessionClaims = sessionClaims as SessionClaims;

  // Allow public routes
  if (publicRoutes(req)) {
    return NextResponse.next();
  }

  // If there's no userId and trying to access protected route, redirect to sign-in
  if (!userId) {
    const signInUrl = new URL('/sign-in', req.url);
    signInUrl.searchParams.set('redirect_url', req.url);
    return NextResponse.redirect(signInUrl);
  }

  // Restrict subscription-protected routes
  if (SUBSCRIPTION_PATHS.some(path => pathname.startsWith(path))) {
    try {
      const token = await getToken();
      if (token) {
        const subscriptionCheck = await validateSubscription(claims, token);

        if (!subscriptionCheck) {
          // Redirect to billing page with error
          const billingUrl = new URL('/billing', req.url);
          billingUrl.searchParams.set('error', 'subscription_required');
          return NextResponse.redirect(billingUrl);
        }
      } else {
        throw new Error('Token is null');
      }
    } catch (error) {
      console.error('Error checking subscription:', error);
      // On error, allow the request to continue - the client-side check will handle it
      return NextResponse.next();
    }
  }

  // Handle onboarding flow
  const onboardingComplete = claims?.publicMetadata?.onboardingComplete as boolean;
  const userRole = claims?.publicMetadata?.role as string;
  console.log("onboardingComplete=", onboardingComplete);  
  if (!onboardingComplete && !pathname.startsWith('/dashboard/onboarding')) {
    return NextResponse.redirect(new URL('/dashboard/onboarding', req.url));
  }

  if (onboardingComplete && pathname.startsWith('/dashboard/onboarding')) {
    return NextResponse.redirect(new URL('/dashboard', req.url));
  }

  return NextResponse.next();
});

async function validateSubscription(claims: SessionClaims, token: string): Promise<boolean> {
  const publicMetadata = claims?.publicMetadata as PublicMetadata;
  const subscriptionStatus = publicMetadata.subscription_status;
  const subscriptionPlan = publicMetadata.subscription_plan;
  if (!subscriptionStatus || !subscriptionPlan) {
    console.error('Missing subscription metadata');
    return false;
  }
  const subscriptionEnd = publicMetadata.subscription_end ? new Date(publicMetadata.subscription_end) : new Date(0); // Default to epoch if undefined
  const lastChecked = new Date(publicMetadata.last_checked || 0); // Default to epoch if undefined
  const now = new Date();

  // Check if it's been more than 1 hour since last_checked
  const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
  if (lastChecked < oneHourAgo) {
    // Request backend to update metadata
    try {
      await api.updateSubscriptionMetadata(token);
      // Assume backend updates Clerk metadata and refreshes the session token
      return true; // Allow access after backend updates
    } catch (error) {
      console.error('Failed to update subscription metadata:', error);
      return false;
    }
  }

  // If within 1 hour, validate subscription locally
  return (
    subscriptionStatus === 'active' &&
    subscriptionEnd > now &&
    SUBSCRIPTION_PATHS.includes(subscriptionPlan)
  );
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|public/).*)",
    "/",
    "/(api|trpc)(.*)"
  ],
};