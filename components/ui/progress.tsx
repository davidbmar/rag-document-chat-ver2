import { forwardRef } from "react"

interface ProgressProps {
  value?: number
  className?: string
}

const Progress = forwardRef<HTMLDivElement, ProgressProps>(
  ({ value = 0, className = "" }, ref) => (
    <div
      ref={ref}
      className={`relative h-4 w-full overflow-hidden rounded-full bg-slate-100 ${className}`}
    >
      <div
        className="h-full w-full flex-1 bg-slate-900 transition-all"
        style={{ transform: `translateX(-${100 - (value || 0)}%)` }}
      />
    </div>
  )
)
Progress.displayName = "Progress"

export { Progress }