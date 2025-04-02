// app/(dashboard)/notes/page.tsx
import { auth } from "@clerk/nextjs/server"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default async function NotesPage() {
  const { userId } = await auth()

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Notes</h2>
        <p className="text-muted-foreground">
          Welcome to your notes.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mt-4 space-y-2">
              <Button className="w-full" variant="outline">
                Add note
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}