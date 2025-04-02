// app/(dashboard)/notes/page.tsx
import { auth } from "@clerk/nextjs/server"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default async function NotesPage() {
  const { userId } = await auth()

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Reports</h2>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Reports</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mt-4 space-y-2">
              <Button className="w-full" variant="outline">
                Add Report
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}