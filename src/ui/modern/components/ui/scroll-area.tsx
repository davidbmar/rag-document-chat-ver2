import { forwardRef } from "react"

interface ScrollAreaProps {
  className?: string
  children: React.ReactNode
}

const ScrollArea = forwardRef<HTMLDivElement, ScrollAreaProps>(
  ({ className = "", children }, ref) => (
    <div
      ref={ref}
      className={`relative overflow-auto ${className}`}
    >
      {children}
    </div>
  )
)
ScrollArea.displayName = "ScrollArea"

export { ScrollArea }