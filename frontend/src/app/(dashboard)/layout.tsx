// app/(dashboard)/layout.tsx
import { UserButton } from "@clerk/nextjs"
import Link from "next/link"
import { Home, Settings, CreditCard, User, Pen, ChartArea } from "lucide-react"
import { ThemeToggle } from "@/components/ui/theme-toggle"

const sidebarNavItems = [
  {
    title: "Home",
    href: "/dashboard",
    icon: Home,
  },
  {
    title: "Settings",
    href: "/dashboard/settings",
    icon: Settings,
  },
  {
    title: "Billing",
    href: "/dashboard/billing",
    icon: CreditCard,
  },
  {
    title: "Profile",
    href: "/dashboard/profile",
    icon: User,
  },
  {
    title: "Notes",
    href: "/dashboard/notes",
    icon: Pen,
  },
  {
    title: "Reports",
    href: "/dashboard/reports",
    icon: ChartArea,
  },
]

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex min-h-screen">
      {/* Only show sidebar if not on onboarding page */}
      <div className="hidden md:flex w-64 flex-col fixed inset-y-0">
        <div className="flex-1 flex flex-col min-h-0 border-r bg-gray-50 dark:bg-gray-900">
          <div className="flex items-center h-16 flex-shrink-0 px-4 border-b">
            <span className="text-lg font-semibold">YourSaaS</span>
          </div>
          <div className="flex-1 flex flex-col overflow-y-auto">
            <nav className="flex-1 px-2 py-4 space-y-1">
              {sidebarNavItems.map((item) => {
                const Icon = item.icon
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="flex items-center px-2 py-2 text-sm font-medium rounded-md hover:bg-gray-100 dark:hover:bg-gray-800"
                  >
                    <Icon className="mr-3 h-6 w-6" />
                    {item.title}
                  </Link>
                )
              })}
            </nav>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 md:pl-64">
        <div className="sticky top-0 z-10 flex h-16 bg-white dark:bg-gray-900 border-b">
          <div className="flex-1 px-4 flex justify-end">
            <div className="ml-4 flex items-center md:ml-6">
              <div className="mr-4">
                <ThemeToggle />
              </div>
              
              <UserButton afterSignOutUrl="/" />
            </div>
          </div>
        </div>

        <main className="py-6">
          <div className="mx-auto px-4 sm:px-6 md:px-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}