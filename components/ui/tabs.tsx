import { forwardRef, createContext, useContext } from "react"

interface TabsProps {
  value: string
  onValueChange: (value: string) => void
  className?: string
  children: React.ReactNode
}

interface TabsListProps {
  className?: string
  children: React.ReactNode
}

interface TabsTriggerProps {
  value: string
  className?: string
  children: React.ReactNode
}

interface TabsContentProps {
  value: string
  className?: string
  children: React.ReactNode
}

interface TabsContextValue {
  value: string
  onValueChange: (value: string) => void
}

const TabsContext = createContext<TabsContextValue | null>(null)

const Tabs = forwardRef<HTMLDivElement, TabsProps>(
  ({ value, onValueChange, className = "", children }, ref) => (
    <TabsContext.Provider value={{ value, onValueChange }}>
      <div ref={ref} className={className}>
        {children}
      </div>
    </TabsContext.Provider>
  )
)
Tabs.displayName = "Tabs"

const TabsList = forwardRef<HTMLDivElement, TabsListProps>(
  ({ className = "", children }, ref) => (
    <div
      ref={ref}
      className={`inline-flex h-10 items-center justify-center rounded-md bg-slate-100 p-1 text-slate-500 ${className}`}
    >
      {children}
    </div>
  )
)
TabsList.displayName = "TabsList"

const TabsTrigger = forwardRef<HTMLButtonElement, TabsTriggerProps>(
  ({ value, className = "", children }, ref) => {
    const context = useContext(TabsContext)
    if (!context) throw new Error("TabsTrigger must be used within Tabs")
    
    const isActive = context.value === value

    return (
      <button
        ref={ref}
        className={`inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-white transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ${
          isActive 
            ? "bg-white text-slate-950 shadow-sm" 
            : "hover:bg-slate-200"
        } ${className}`}
        onClick={() => context.onValueChange(value)}
      >
        {children}
      </button>
    )
  }
)
TabsTrigger.displayName = "TabsTrigger"

const TabsContent = forwardRef<HTMLDivElement, TabsContentProps>(
  ({ value, className = "", children }, ref) => {
    const context = useContext(TabsContext)
    if (!context) throw new Error("TabsContent must be used within Tabs")
    
    if (context.value !== value) return null

    return (
      <div
        ref={ref}
        className={`mt-2 ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 ${className}`}
      >
        {children}
      </div>
    )
  }
)
TabsContent.displayName = "TabsContent"

export { Tabs, TabsList, TabsTrigger, TabsContent }