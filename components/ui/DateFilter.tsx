import React, { useState } from "react";
import { Calendar, Filter, Loader2, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  TooltipProvider,
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "./tooltip";
import Cookies from "js-cookie";
interface ChildProps {
  fetchDashboardData: (from: string, to: string, userId: number) => void;
  loading: boolean; // parent loading
}

const DateFilter = ({ fetchDashboardData, loading }: ChildProps) => {
  const today = new Date();

  // first day of this month
  const firstDayPrevMonth = new Date(
    today.getFullYear(),
    today.getMonth() - 1,
    1
  );

  const formatDate = (d: Date) => d.toLocaleDateString("en-CA");

  const [dateRange, setDateRange] = useState({
    from: formatDate(firstDayPrevMonth),
    to: formatDate(today),
  });

  const userId = Number(Cookies.get("userId")) || 0;

  const clearFilters = () => {
    const newDateRange = {
      from: formatDate(firstDayPrevMonth),
      to: formatDate(today),
    };
    setDateRange(newDateRange);
    fetchDashboardData(newDateRange.from, newDateRange.to, userId);
  };

  return (
    <div className="flex items-center space-x-4 px-4 dark:bg-gray-800 rounded-lg">
      <Calendar className="h-5 w-5 text-gray-500" />
      <div className="flex items-center space-x-2">
        <Label htmlFor="date-from">From:</Label>
        <Input
          id="date-from"
          type="date"
          value={dateRange.from}
          onChange={(e) =>
            setDateRange((prev) => ({ ...prev, from: e.target.value }))
          }
          className=" bg-gray-50 dark:bg-gray-800"
          max={dateRange.to}
          style={{
            color: "var(--color-foreground, var(--foreground))",
            WebkitTextFillColor: "var(--color-foreground, var(--foreground))",
          }}
        />
      </div>
      <div className="flex items-center space-x-2">
        <Label htmlFor="date-to">To:</Label>
        <Input
          id="date-to"
          type="date"
          value={dateRange.to}
          onChange={(e) =>
            setDateRange((prev) => ({ ...prev, to: e.target.value }))
          }
          className=" bg-gray-50 dark:bg-gray-800"
          style={{
            color: "var(--color-foreground, var(--foreground))",
            WebkitTextFillColor: "var(--color-foreground, var(--foreground))",
          }}
          max={new Date().toISOString().split("T")[0]}
          min={dateRange.from}
        />
      </div>
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                fetchDashboardData(dateRange.from, dateRange.to, userId)
              }
              disabled={loading}
              className="text-center"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Filter className="h-4 w-4" />
              )}
              {loading ? "Loading..." : ""}
            </Button>
          </TooltipTrigger>
          <TooltipContent side="top" align="center">
            Apply Filter
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              className="bg-gray-50 text-gray-800 dark:bg-transparent dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700"
              variant="ghost"
              size="sm"
              onClick={clearFilters}
              disabled={loading}
            >
              <RotateCcw className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="top" align="center">
            Clear
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  );
};

export default DateFilter;
