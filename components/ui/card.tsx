import { forwardRef } from "react"

interface CardProps {
  className?: string
  children: React.ReactNode
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className = "", children }, ref) => (
    <div
      ref={ref}
      className={`rounded-lg border border-gray-200 bg-white text-gray-900 shadow-lg ${className}`}
    >
      {children}
    </div>
  )
)
Card.displayName = "Card"

const CardHeader = forwardRef<HTMLDivElement, CardProps>(
  ({ className = "", children }, ref) => (
    <div ref={ref} className={`flex flex-col space-y-1.5 p-6 ${className}`}>
      {children}
    </div>
  )
)
CardHeader.displayName = "CardHeader"

const CardTitle = forwardRef<HTMLParagraphElement, CardProps>(
  ({ className = "", children }, ref) => (
    <h3
      ref={ref}
      className={`text-2xl font-semibold leading-none tracking-tight ${className}`}
    >
      {children}
    </h3>
  )
)
CardTitle.displayName = "CardTitle"

const CardDescription = forwardRef<HTMLParagraphElement, CardProps>(
  ({ className = "", children }, ref) => (
    <p ref={ref} className={`text-sm text-slate-500 ${className}`}>
      {children}
    </p>
  )
)
CardDescription.displayName = "CardDescription"

const CardContent = forwardRef<HTMLDivElement, CardProps>(
  ({ className = "", children }, ref) => (
    <div ref={ref} className={`p-6 pt-0 ${className}`}>
      {children}
    </div>
  )
)
CardContent.displayName = "CardContent"

export { Card, CardHeader, CardTitle, CardDescription, CardContent }