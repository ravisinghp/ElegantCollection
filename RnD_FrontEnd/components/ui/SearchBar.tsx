import * as React from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Search } from "lucide-react"

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
  onSearch: () => void
  placeholder?: string
}

export function SearchBar({
  value,
  onChange,
  onSearch,
  placeholder = "Search...",
}: SearchBarProps) {
  return (
    <div className="flex w-full max-w-md">
      <Input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-l-md rounded-r-none border px-3 py-2 focus:outline-none"
        onKeyDown={(e) => e.key === "Enter" && onSearch()}
      />
      <Button
        type="button"
        onClick={onSearch}
        className="rounded-l-none rounded-r-md"
      >
        <Search className="h-4 w-4" />
      </Button>
    </div>
  )
}
