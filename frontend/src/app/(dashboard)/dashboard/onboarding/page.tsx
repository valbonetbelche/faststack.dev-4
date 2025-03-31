// app/(dashboard)/onboarding/page.tsx
import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import CompleteOnboardingForm from "./complete-onboarding-form";

export default async function OnboardingPage() {
  const { userId } = await auth();
  
  if (!userId) {
    redirect('/sign-in');
  }

  return (
    <div className="container max-w-2xl mx-auto py-8">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold">Welcome to YourSaaS</h1>
        <p className="text-muted-foreground mt-2">Let's get your account set up</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Complete Your Profile</CardTitle>
          <CardDescription>
            Tell us a bit about yourself and your preferences
          </CardDescription>
        </CardHeader>
        <CardContent>
          <CompleteOnboardingForm />
        </CardContent>
      </Card>
    </div>
  )
}