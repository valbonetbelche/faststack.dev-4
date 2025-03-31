import {
  clerkMiddleware,
  createRouteMatcher,
} from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';
import type { NextRequest } from "next/server";
import type { SessionClaims } from './types'; // Import the types
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

  try {
    const token = await getToken();
    if (token) {
      const subscriptionCheck = await checkSubscriptionStatus(token);
      
      if (!subscriptionCheck.has_active_subscription) {
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

async function checkSubscriptionStatus(token: string) {
  try {
    const response = await api.getCurrentSubscription(token);
    return response;
  } catch (error) {
    console.error('Failed to verify subscription:', error);
    throw new Error('Failed to verify subscription');
  }
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|public/).*)",
    "/",
    "/(api|trpc)(.*)"
  ],
};