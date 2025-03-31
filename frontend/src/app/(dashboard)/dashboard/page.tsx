// app/(dashboard)/dashboard/page.tsx
import { auth } from "@clerk/nextjs/server"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default async function DashboardPage() {
  const { userId } = await auth()

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">
          Welcome to your dashboard. Here's an overview of your account.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Quick Start</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Get started by completing these quick tasks to set up your account.
            </p>
            <div className="mt-4 space-y-2">
              <Button className="w-full" variant="outline">
                Complete Profile
              </Button>
              <Button className="w-full" variant="outline">
                Invite Team Members
              </Button>
              <Button className="w-full" variant="outline">
                Set up Billing
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Usage</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Your current usage and limits.
            </p>
            {/* Add usage statistics here */}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Your recent account activity.
            </p>
            {/* Add activity list here */}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}