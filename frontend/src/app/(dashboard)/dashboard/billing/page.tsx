"use client";
import { useEffect, useState } from "react";
import { useAuth, useUser } from "@clerk/nextjs";
import { useSearchParams } from "next/navigation";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckIcon, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { publicApi } from "@/lib/api";
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import SpinningLoader from "@/components/ui/spinning-loader";

// Define the Plan type based on your schema
type Plan = {
  id: number;
  name: string;
  description: string;
  price: number;
  features: string[];
  stripe_price_id: string;
  stripe_product_id: string;
  billing_interval: string;
  is_active: boolean;
};

export default function BillingPage() {
  const { getToken } = useAuth();
  const { user, isLoaded } = useUser();
  const searchParams = useSearchParams();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [dialogMessage, setDialogMessage] = useState("");
  const [fadeIn, setFadeIn] = useState(false); // State for fade-in effect

  // Fetch plans from the backend
  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const token = await getToken();
        if (token) {
          const data = await publicApi.getPlans(token);
          setPlans(data);
        } else {
          toast.error("Failed to authenticate. Please log in.");
        }
      } catch (error) {
        toast.error("Failed to load subscription plans. Please try again later.");
      } finally {
        setLoading(false);
        setTimeout(() => setFadeIn(true), 100); // Trigger fade-in after loading
      }
    };

    fetchPlans();
  }, [getToken]);

  // Check for query parameters and set dialog state
  useEffect(() => {
    const error = searchParams.get("error");
    if (error) {
      setShowDialog(true);
      if (error === "subscription_required") {
        setDialogMessage("You need an active subscription to access this feature. Please subscribe to a plan.");
      } else if (error === "incorrect_plan") {
        setDialogMessage("Your current subscription plan does not grant access to this feature. Upgrade your plan to unlock all features!");
      } else {
        setDialogMessage("An unknown error occurred. Please check your subscription.");
      }
    }
  }, [searchParams]);

  // Handle checkout session creation
  const handleCheckout = async (planId: number) => {
    try {
      const token = await getToken();
      if (token) {
        const { checkout_url } = await publicApi.createCheckoutSession({ plan_id: planId }, token);
        window.location.href = checkout_url;
      } else {
        toast.error("Failed to authenticate. Please log in.");
      }
    } catch (error) {
      toast.error("Failed to initiate checkout. Please try again.");
    }
  };

  const fetchStripePortalSession = async () => {
    try {
      const token = await getToken();
      if (token) {
        const url = await publicApi.getStripeBillingUrl(token);
        console.log(url);
        window.open(url, "_blank");
      }
    } catch (error) {
      console.error("Failed to set the Stripe Billing Url:", error);
    }
  };

  if (loading) {
    return <SpinningLoader />;
  }

  return (
    <div className={`container mx-auto py-8 transition-opacity duration-500 ${fadeIn ? "opacity-100" : "opacity-0"}`}>
      {showDialog && (
        <AlertDialog open={showDialog} onOpenChange={setShowDialog}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Oops</AlertDialogTitle>
              <AlertDialogDescription>{dialogMessage}</AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={() => setShowDialog(false)}>Ok</AlertDialogCancel>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}

      {isLoaded && user?.publicMetadata.subscription_status as Boolean && (
        <div className="mb-8 p-6 border rounded-lg">
          <h2 className="text-2xl font-bold mb-4">Your Subscription</h2>
          <p className="mb-2">
            <strong>Plan:</strong> {String(user?.publicMetadata.subscription_plan as string || "")}
          </p>
          <p className="mb-2">
            <strong>Renewal Date:</strong> {user?.publicMetadata.subscription_end ? new Date(user?.publicMetadata.subscription_end as string).toLocaleDateString() : "N/A"}
          </p>
          <Button
            onClick={fetchStripePortalSession} // Opens the Stripe billing portal
            className="mt-4"
          >
            Manage Subscription
          </Button>
        </div>
      )}

      {/* Subscription Plans Section */}
      <h1 className="text-3xl font-bold mb-6">Subscription Plans</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map((plan) => (
          <Card key={plan.id} className="flex flex-col">
            <CardHeader>
              <CardTitle>{plan.name}</CardTitle>
              <CardDescription>{plan.description}</CardDescription>
            </CardHeader>
            <CardContent className="flex-grow">
              <div className="text-2xl font-bold">
                ${plan.price} <span className="text-sm text-gray-500">/{plan.billing_interval}</span>
              </div>
              <ul className="mt-4 space-y-2">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-center">
                    <CheckIcon className="w-4 h-4 mr-2 text-green-500" />
                    {feature}
                  </li>
                ))}
              </ul>
            </CardContent>
            <CardFooter>
              <Button
                onClick={() => handleCheckout(plan.id)}
                className="w-full"
                disabled={!plan.is_active}
              >
                {plan.is_active ? "Subscribe" : "Unavailable"}
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  );
}