import { forwardRef } from "react"

interface AlertProps {
  className?: string
  children: React.ReactNode
}

const Alert = forwardRef<HTMLDivElement, AlertProps>(
  ({ className = "", children }, ref) => (
    <div
      ref={ref}
      className={`relative w-full rounded-lg border border-slate-200 p-4 [&>svg~*]:pl-7 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-slate-950 ${className}`}
    >
      {children}
    </div>
  )
)
Alert.displayName = "Alert"

const AlertDescription = forwardRef<HTMLParagraphElement, AlertProps>(
  ({ className = "", children }, ref) => (
    <div ref={ref} className={`text-sm [&_p]:leading-relaxed ${className}`}>
      {children}
    </div>
  )
)
AlertDescription.displayName = "AlertDescription"

export { Alert, AlertDescription }