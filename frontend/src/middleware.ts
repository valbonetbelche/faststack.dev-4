import {
  clerkMiddleware,
  createRouteMatcher,
} from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';
import type { PublicMetadata, SessionClaims } from './types'; // Import the types

// Define subscription-protected paths with allowed plans
const SUBSCRIPTION_PATHS = [
  { path: '/dashboard/notes', allowedPlans: ['Professional', 'Enterprise'] },
  { path: '/dashboard/reports', allowedPlans: ['Enterprise'] },
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

  const claims: SessionClaims = sessionClaims as SessionClaims;

  if (publicRoutes(req)) {
    return NextResponse.next();
  }

  if (!userId) {
    const signInUrl = new URL('/sign-in', req.url);
    signInUrl.searchParams.set('redirect_url', req.url);
    return NextResponse.redirect(signInUrl);
  }

  const restrictedPath = SUBSCRIPTION_PATHS.find(pathConfig => pathname.startsWith(pathConfig.path));
  if (restrictedPath) {
    try {
      const token = await getToken();
      if (token) {
        const subscriptionCheck = await validateSubscription(claims, token, restrictedPath.allowedPlans);

        if (subscriptionCheck.noSubscription) {
          console.log('User has no subscription');
          const billingUrl = new URL('/dashboard/billing', req.url);
          billingUrl.searchParams.set('error', 'subscription_required');
          return NextResponse.redirect(billingUrl);
        }

        if (subscriptionCheck.incorrectPlan) {
          console.log('User has an incorrect plan');
          const billingUrl = new URL('/dashboard/billing', req.url);
          billingUrl.searchParams.set('error', 'incorrect_plan');
          return NextResponse.redirect(billingUrl);
        }
      } else {
        throw new Error('Token is null');
      }
    } catch (error) {
      console.error('Error checking subscription:', error);
      return NextResponse.next();
    }
  }

  const onboardingComplete = claims?.publicMetadata?.onboardingComplete as boolean;
  const userRole = claims?.publicMetadata?.role as string;
  if (!onboardingComplete && !pathname.startsWith('/dashboard/onboarding')) {
    return NextResponse.redirect(new URL('/dashboard/onboarding', req.url));
  }

  if (onboardingComplete && pathname.startsWith('/dashboard/onboarding')) {
    return NextResponse.redirect(new URL('/dashboard', req.url));
  }

  return NextResponse.next();
});

async function validateSubscription(
  claims: SessionClaims,
  token: string,
  allowedPlans: string[]
): Promise<{
  noSubscription: boolean;
  incorrectPlan: boolean;
}> {
  const publicMetadata = claims?.publicMetadata as PublicMetadata;
  const subscriptionStatus = publicMetadata.subscription_status;
  const subscriptionPlan = publicMetadata.subscription_plan;
  const subscriptionEnd = publicMetadata.subscription_end
    ? new Date(publicMetadata.subscription_end)
    : new Date(0); // Default to epoch if undefined
  const now = new Date();

  // Determine subscription validity
  const isActive = subscriptionStatus === 'active' && subscriptionEnd > now;
  const isCorrectPlan = allowedPlans.includes(subscriptionPlan || '');

  return {
    noSubscription: !isActive,
    incorrectPlan: isActive && !isCorrectPlan,
  };
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|public/).*)",
    "/",
    "/(api|trpc)(.*)"
  ],
};