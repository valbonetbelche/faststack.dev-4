// app/(dashboard)/onboarding/complete-onboarding-form.tsx
'use client'

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from '@clerk/nextjs'
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { toast } from "sonner"
import type { OnboardingData } from "@/types"

export default function CompleteOnboardingForm() {
  const router = useRouter()
  const { isLoaded, isSignedIn } = useAuth()
  const userService = {}
  const [isLoading, setIsLoading] = useState(false)
  const [formData, setFormData] = useState<OnboardingData>({
    company: '',
    role: 'owner',
  })

  if (!isLoaded) {
    return <div>Loading...</div>
  }

  if (!isSignedIn) {
    router.push('/sign-in')
    return null
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setIsLoading(true)

    try {

      toast.success("Welcome aboard! 🎉 Your account has been successfully set up.")
      
      // The middleware will automatically redirect to /dashboard
      router.push("/dashboard")
      router.refresh()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Something went wrong during setup.")
  }

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="company">Company Name</Label>
          <Input
            id="company"
            placeholder="Enter your company name"
            required
            value={formData.company}
            onChange={(e) => setFormData(prev => ({
              ...prev,
              company: e.target.value
            }))}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="role">Your Role</Label>
          <Select 
            value={formData.role}
            onValueChange={(value: OnboardingData['role']) => 
              setFormData(prev => ({
                ...prev,
                role: value
              }))
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Select your role" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="owner">Business Owner</SelectItem>
              <SelectItem value="developer">Developer</SelectItem>
              <SelectItem value="other">Other</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <Button 
        type="submit" 
        className="w-full"
        disabled={isLoading}
      >
        {isLoading ? "Setting up your account..." : "Complete Setup"}
      </Button>
    </form>
  )
}
}