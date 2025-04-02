"use client"
import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { useSearchParams } from "next/navigation"; // Import useSearchParams
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckIcon } from "lucide-react";
import { toast } from "sonner";
import { publicApi } from "@/lib/api";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

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
  const searchParams = useSearchParams(); // Access query parameters
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [dialogMessage, setDialogMessage] = useState(""); // State for dialog message

  // Fetch plans from the backend
  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const token = await getToken();
        if (token) {
          const data = await publicApi.getPlans(token); // Pass the token to the API method
          setPlans(data);
        } else {
          toast.error("Failed to authenticate. Please log in.");
        }
      } catch (error) {
        toast.error("Failed to load subscription plans. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchPlans();
  }, [getToken]);

  // Check for query parameters and set dialog state
  useEffect(() => {
    const error = searchParams.get("error");
    console.log("Error from query params:", error); // Log the error for debugging
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
        const { checkout_url } = await publicApi.createCheckoutSession({ plan_id: planId }, token); // Pass the token to the API method
        window.location.href = checkout_url; // Redirect to Stripe checkout
      } else {
        toast.error("Failed to authenticate. Please log in.");
      }
    } catch (error) {
      toast.error("Failed to initiate checkout. Please try again.");
    }
  };

  if (loading) {
    return <div>Loading plans...</div>;
  }

  return (
    <div className="container mx-auto py-8">
      {/* Alert Dialog */}
      {showDialog && (
        <AlertDialog open={showDialog} onOpenChange={setShowDialog}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Access Restricted</AlertDialogTitle>
              <AlertDialogDescription>{dialogMessage}</AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={() => setShowDialog(false)}>Ok</AlertDialogCancel>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}

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