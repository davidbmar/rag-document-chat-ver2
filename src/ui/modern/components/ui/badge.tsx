import { forwardRef } from "react"

interface BadgeProps {
  variant?: "default" | "secondary" | "destructive" | "outline"
  className?: string
  children: React.ReactNode
}

const Badge = forwardRef<HTMLDivElement, BadgeProps>(
  ({ variant = "default", className = "", children }, ref) => {
    const variants = {
      default: "border-transparent bg-blue-600 text-white hover:bg-blue-700 shadow-sm",
      secondary: "border-transparent bg-gray-100 text-gray-900 hover:bg-gray-200 shadow-sm",
      destructive: "border-transparent bg-red-600 text-white hover:bg-red-700 shadow-sm",
      outline: "text-gray-900 border-gray-300 bg-white hover:bg-gray-50 shadow-sm"
    }

    return (
      <div
        ref={ref}
        className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-slate-950 focus:ring-offset-2 ${variants[variant]} ${className}`}
      >
        {children}
      </div>
    )
  }
)
Badge.displayName = "Badge"

export { Badge }