"use client";

import type React from "react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import ReportSection from "../reportSection/ReportSection";
import Cookies from "js-cookie";
import * as Recharts from "recharts";
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import {
  BarChart3,
  Users,
  Mail,
  FileText,
  Clock,
  TrendingUp,
  Download,
  RefreshCw,
  Plus,
  Edit,
  Save,
  X,
  Calendar,
  Filter,
  LogOut,
  Search,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import axiosClient from "@/app/api/axiosClient";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
// removed server actions; using axiosClient directly
import { useToast } from "@/hooks/use-toast";
import { toast } from "@/components/ui/use-toast";
import { useEffect } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import DateFilter from "@/components/ui/DateFilter";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import BusinessRulesTab from "../businessRulesSection/BusinessRulesSection";
import CategoriesTab from "../categorySection/CategorySection";
import { SearchBar } from "@/components/ui/SearchBar";

const getUserContext = () => {
  let userId =
    sessionStorage.getItem("userid") || localStorage.getItem("userid");
  let orgId = sessionStorage.getItem("orgid") || localStorage.getItem("orgid");
  let roleId =
    sessionStorage.getItem("roleid") || localStorage.getItem("roleid");
  return { userId, orgId, roleId };
};

export default function DashboardPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(true);

  const [keywords, setKeywords] = useState<any[]>([]);
  const [loadingKeywords, setLoadingKeywords] = useState(true);

  const [isLoading, setIsLoading] = useState(false);
  //const [lastSync, setLastSync] = useState(new Date())
  const [isCreateUserDialogOpen, setIsCreateUserDialogOpen] = useState(false);
  const [isCreateKeywordDialogOpen, setIsCreateKeywordDialogOpen] =
    useState(false);
  // const [isCreateBusinessRuleDialogOpen, setIsCreateBusinessRuleDialogOpen] =
  //   useState(false);
  // const [editingBusinessRule, setEditingBusinessRule] = useState<string | null>(
  //   null
  // );
  const [editingKeyword, setEditingKeyword] = useState<string | null>(null);
  // const [businessRules, setBusinessRules] = useState([
  //   { id: "1", name: "AI Research Keywords", wordCount: 500, efforts: 120 },
  //   { id: "2", name: "Data Analysis Projects", wordCount: 300, efforts: 90 },
  //   { id: "3", name: "Machine Learning Models", wordCount: 800, efforts: 180 },
  //   { id: "4", name: "Research Documentation", wordCount: 200, efforts: 60 },
  // ]);

  const [weeklyStats, setWeeklyStats] = useState<any[]>([]);
  type TopKeyword = {
    org_id: number;
    top_keywords: [string, number][];
  };

  // Initialize state correctly
  const [topKeyword, setTopKeyword] = useState<TopKeyword | null>(null);

  // const [reportData, setReportData] = useState([
  //   {
  //     id: "1",
  //     entityType: "Email",
  //     date: "2024-01-15",
  //     sender: "john@company.com",
  //     recipients: "team@company.com",
  //     wordCount: 450,
  //     efforts: 45,
  //     keywordCount: 8,
  //     keywordEfforts: 15,
  //     selected: false,
  //   },
  //   {
  //     id: "2",
  //     entityType: "Calendar",
  //     date: "2024-01-14",
  //     sender: "sarah@company.com",
  //     recipients: "dev-team@company.com",
  //     wordCount: 200,
  //     efforts: 30,
  //     keywordCount: 5,
  //     keywordEfforts: 10,
  //     selected: false,
  //   },
  //   {
  //     id: "3",
  //     entityType: "Email",
  //     date: "2024-01-13",
  //     sender: "mike@company.com",
  //     recipients: "research@company.com",
  //     wordCount: 680,
  //     efforts: 75,
  //     keywordCount: 12,
  //     keywordEfforts: 25,
  //     selected: false,
  //   },
  // ])
  // const [dateRange, setDateRange] = useState({
  //   from: "2024-01-01",
  //   to: "2024-01-31",
  // });
  const router = useRouter();

  const handleManualSync = async () => {
    setIsLoading(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 2000));
    // setLastSync(new Date().toLocaleString())
    setIsLoading(false);
  };

  //Function for fecthing the Card data with calculation and display Above On Admin Dashboard
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [loadingDashboard, setLoadingDashboard] = useState(true);
  const [userId, setUserId] = useState<number | null>(null);
  const [org_id, setOrgId] = useState<number | null>(null);

  //------------Fetch User With Pagination Logic-------------//
  const [totalCount, setTotalCount] = useState(1);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [userSearchQuery, setUserSearchQuery] = useState("");
  const [lastSyncData, setLastSyncData] = useState<Record<number, string>>({});
  const [limit, setLimit] = useState(5); // default 5 per page

  useEffect(() => {
    if (userId) {
      if (userSearchQuery.trim() === "") {
        fetchUsers(userId, currentPage);
      }
      fetchLastSyncData();
    }
  }, [currentPage, userId, userSearchQuery]);

  const fetchUsers = async (
    userId: number,
    page: number,
    query = userSearchQuery, // default to current search query
    customLimit?: number
  ) => {
    try {
      setLoadingUsers(true);
      const orgId = Number(
        Cookies.get("orgid") ||
          localStorage.getItem("orgid") ||
          sessionStorage.getItem("orgid")
      );
      const role_id = Number(
        Cookies.get("roleid") ||
          localStorage.getItem("roleid") ||
          sessionStorage.getItem("roleid")
      );

      const effectiveLimit = customLimit ?? limit; //use passed limit or current

      let response;
      if (query.trim() === "") {
        // No searchcall main API
        response = await axiosClient.get("/admin/users", {
          params: { org_id: orgId, userId, page, limit: effectiveLimit, role_id },
        });
        setUsers(response.data.users || []);
        setTotalCount(response.data.totalCount || 0);
      } else {
        // Search call search API
        response = await axiosClient.get("/admin/searchUser", {
          params: { org_id: orgId, query, page, limit: effectiveLimit },
        });
        setUsers(response.data.items || []);
        setTotalCount(response.data.totalCount || 0);
      }

      setTotalPages(
        Math.ceil((response.data.totalCount || 0) / effectiveLimit)
      );
    } catch (err) {
      console.error("Error fetching users:", err);
    } finally {
      setLoadingUsers(false);
    }
  };

  //------------Fetching Last Sync For user-----------------//
  const fetchLastSyncData = async () => {
    try {
      const orgId = Number(
        Cookies.get("orgid") ||
          localStorage.getItem("orgid") ||
          sessionStorage.getItem("orgid")
      );

      const response = await axiosClient.get("/admin/lastSyncEachUser", {
        params: { org_id: orgId },
      });

      if (response?.data?.data?.length) {
        const syncMap: { [key: number]: string } = {};
        let latestSync: Date | null = null;

        response.data.data.forEach((item: any) => {
          syncMap[item.user_id] = item.last_sync;

          if (item.last_sync) {
            // ✅ Now backend sends ISO with +05:30, so this works directly
            const syncDate = new Date(item.last_sync);

            if (!latestSync || syncDate > latestSync) {
              latestSync = syncDate;
            }
          }
        });

        setLastSyncData(syncMap);
        setLastSync(latestSync || null);
      } else {
        setLastSyncData({});
        setLastSync(null);
      }
    } catch (err) {
      console.error("Error fetching last sync data:", err);
      setLastSyncData({});
      setLastSync(null);
    }
  };
  //------------Fetch Keywords With Pagination Logic-------------//
  const [keywordsTotalCount, setKeywordsTotalCount] = useState(0);
  const [keywordsTotalPages, setKeywordsTotalPages] = useState(1);
  const [keywordsCurrentPage, setKeywordsCurrentPage] = useState(1);
  const [keywordSearchQuery, setKeywordSearchQuery] = useState("");
  const [keywordsLimit, setKeywordsLimit] = useState(5); // ✅ Rows per page

  const handleKeywordCreated = async () => {
    setKeywordsCurrentPage(1); // reset pagination
    await fetchKeywords(1); // fetch first page
  };
  useEffect(() => {
    if (userId) {
      fetchKeywords(keywordsCurrentPage); //only pass page
    }
  }, [keywordsCurrentPage, userId]);

  async function fetchKeywords(
    page: number,
    query = keywordSearchQuery,
    customLimit?: number
  ) {
    try {
      setLoadingKeywords(true);
      const orgId = Number(
        Cookies.get("orgid") ||
          localStorage.getItem("orgid") ||
          sessionStorage.getItem("orgid")
      );

      const effectiveLimit = customLimit ?? keywordsLimit; // ✅ Handle new limit properly

      let response;
      if (query.trim() === "") {
        // No search → old API
        response = await axiosClient.get("/admin/keywords", {
          params: {
            org_id: orgId,
            userId: Number(userId),
            page,
            limit: effectiveLimit,
          },
        });
      } else {
        // Search → searchKeyword API
        response = await axiosClient.get("/admin/searchKeyword", {
          params: { org_id: orgId, query, page, limit: effectiveLimit },
        });
      }

      const totalCountFromAPI =
        response.data.totalCount || response.data.total || 0;
      setKeywords(response.data.keywords || response.data.items || []);
      setKeywordsTotalCount(totalCountFromAPI);
      setKeywordsTotalPages(Math.ceil(totalCountFromAPI / effectiveLimit));
    } catch (err) {
      console.error("Error fetching keywords:", err);
    } finally {
      setLoadingKeywords(false);
    }
  }

  //------------Fetch Dashboard Card Data-------------//
  const fetchDashboardData = async (
    from: string,
    to: string,
    userId: number
  ) => {
    setLoadingDashboard(true);
    try {
      const response = await axiosClient.get("/admin/dashboardCardData", {
        params: {
          from_date: from,
          to_date: to,
          userId:Cookies.get("userid") ||
            localStorage.getItem("userid") ||
            sessionStorage.getItem("userid"),
          org_id:
            Cookies.get("orgid") ||
            localStorage.getItem("orgid") ||
            sessionStorage.getItem("orgid"),
	  role_id:
            Cookies.get("roleid") ||
            localStorage.getItem("roleid") ||
            sessionStorage.getItem("roleid"),
        },
        withCredentials: true,
      });
      setDashboardData(response.data);
    } catch (err) {
      console.error("Error fetching dashboard data:", err);
      try {
        const axiosErr: any = err as any;
        const status = axiosErr?.response?.status;
        const detail = axiosErr?.response?.data?.detail || axiosErr?.message;
        typeof window !== "undefined" &&
          console.warn("GET /admin/dashboardCardData failed", status, detail, {
            from,
            to,
            userId,
          });
        useToast().toast?.({
          title: `Dashboard metrics failed (${status || "error"})`,
          description: String(detail),
          variant: "destructive",
        });
      } catch {}
    } finally {
      setLoadingDashboard(false);
    }
  };
  const user_id = Cookies.get("userid") ? Number(Cookies.get("userid")) : null;

  //-----------Update the Status Of User-----------------//
  const handleToggle = async (user_id: number, newStatus: number) => {
    // Optimistic UI update
    setUsers((prev) =>
      prev.map((u) =>
        u.user_id === user_id ? { ...u, is_active: newStatus } : u
      )
    );

    try {
      const orgId = Number(
        Cookies.get("orgid") ||
          localStorage.getItem("orgid") ||
          sessionStorage.getItem("orgid")
      );

      await axiosClient.post("/admin/updateUserStatus", null, {
        params: { user_id, is_active: newStatus, org_id: orgId },
      });
    } catch (err) {
      console.error("Error updating user status:", err);
      // Optional: rollback UI if API fails
      setUsers((prev) =>
        prev.map((u) =>
          u.user_id === user_id
            ? { ...u, is_active: newStatus === 1 ? 0 : 1 }
            : u
        )
      );
    }
  };

  //-----------Update the Status Of keyword-----------------//
  const handleKeywordToggle = async (keyword_id: number, newStatus: number) => {
    // Optimistic UI update
    setKeywords((prev) =>
      prev.map((k) =>
        k.keyword_id === keyword_id ? { ...k, is_active: newStatus } : k
      )
    );

    try {
      const orgId = Number(
        Cookies.get("orgid") ||
          localStorage.getItem("orgid") ||
          sessionStorage.getItem("orgid")
      );

      await axiosClient.post("/admin/updateKeywordStatus", null, {
        params: { keyword_id, is_active: newStatus },
      });
    } catch (err) {
      console.error("Error updating user status:", err);
      // Optional: rollback UI if API fails
      setUsers((prev) =>
        prev.map((k) =>
          k.keyword_id === keyword_id
            ? { ...k, is_active: newStatus === 1 ? 0 : 1 }
            : k
        )
      );
    }
  };

  //------------Fetch Chart data on dashboard-------------//
  const fetchChartData = async (
     from: string,
    to: string,
    userId: number
  ) => {
    setLoadingDashboard(true);
    try {
      const response = await axiosClient.get(
        "/admin/weekly-hours-previous-month",
        {
          params: {
             from_date: from,
             to_date: to,
             user_id: userId,
            org_id:
              Cookies.get("orgid") ||
              localStorage.getItem("orgid") ||
              sessionStorage.getItem("orgid"),
            
          },
          withCredentials: true,
        }
      );
      setWeeklyStats(response.data);
      console.log("weeklyStats:", weeklyStats);
    } catch (err) {
      console.error("Error fetching dashboard data:", err);
      setLoadingDashboard(false);
    } finally {
      setLoadingDashboard(false);
    }
  };

  //------------Fetch Top Keywords On admin Dashboard-------------//
  const fetchTopKeywords = async (
     from: string,
    to: string,
    userId: number
  ) => {
    setLoadingDashboard(true);
    try {
      const response = await axiosClient.get("/admin/top-keywords", {
        params: {
          from_date: from,
          to_date: to,
          user_id: userId,
          org_id:
            Cookies.get("orgid") ||
            localStorage.getItem("orgid") ||
            sessionStorage.getItem("orgid"),
          
        },
        withCredentials: true,
      });
      setTopKeyword(response.data);
    } catch (err) {
      console.error("Error fetching dashboard data:", err);
      setLoadingDashboard(false);
    } finally {
      setLoadingDashboard(false);
    }
  };

  useEffect(() => {
    setUserId(Cookies.get("userid") ? Number(Cookies.get("userid")) : null);
    //fetchChartData();
    //fetchTopKeywords();
  }, []);

  const formatDate = (d: Date) => d.toLocaleDateString("en-CA");
  useEffect(() => {
    if (userId !== null) {
      // const today = new Date();
      // const firstDay = new Date(
      //   today.getFullYear(),
      //   today.getMonth(),
      //   1
      // ).toLocaleDateString("en-CA");
      // const lastDay = new Date(
      //   today.getFullYear(),
      //   today.getMonth() + 1,
      //   0
      // ).toLocaleDateString("en-CA");

      const today = new Date();
      const firstDayPrevMonth = new Date(
        today.getFullYear(),
        today.getMonth() - 1,
        1
      );

      var firstDay = formatDate(firstDayPrevMonth);
      var lastDay = formatDate(today);

      // fetchUsers(userId)
      //fetchKeywords(userId)

      fetchDashboardData(firstDay, lastDay, userId);
      fetchChartData(firstDay, lastDay, userId);
      fetchTopKeywords(firstDay, lastDay, userId);
    }
  }, [userId]);

  // const [activeTab, setActiveTab] = useState<"users" | "keywords">("users");
  // useEffect(() => {
  //   if (activeTab === "users") {
  //     setCurrentPage(1);
  //   } else if (activeTab === "keywords") {
  //     setKeywordsCurrentPage(1);
  //   }
  // }, [activeTab]);

  const [activeTab, setActiveTab] = useState<"users" | "keywords">("users");

  useEffect(() => {
    if (activeTab === "users") {
      setCurrentPage(1);
      setUserSearchQuery(""); // clear search when switching back
    } else if (activeTab === "keywords") {
      setKeywordsCurrentPage(1);
      setKeywordSearchQuery(""); // clear keyword search too
    }
  }, [activeTab]);

  //------------Handle Logout functionality-------------//
  const handleLogout = () => {
    // Clear any session data if needed
    // localStorage.clear() // Uncomment if you store session data
    sessionStorage.clear();
    localStorage.clear();
    Object.keys(Cookies.get()).forEach((cookie) => {
      Cookies.remove(cookie);
    });

    router.replace("/login");
  };

  // const handleEditBusinessRule = (id: string) => {
  //   setEditingBusinessRule(id);
  // };

  // const handleSaveBusinessRule = (id: string) => {
  //   setEditingBusinessRule(null);
  //   // Here you would typically save to backend
  // };

  // const handleCancelEdit = () => {
  //   setEditingBusinessRule(null);
  // };

  const handleEditKeyword = (id: string) => {
    setEditingKeyword(id);
  };

  const handleCancelEditKeyword = () => {
    setEditingKeyword(null);
  };

  //------------Update the Keyword with Some Pagination Logic-------------//

  const handleSaveKeyword = async (keyword: {
    keyword_id: string;
    keyword_name: string;
  }) => {
    try {
      const updated_by = userId; //getting Updated_by Id

      if (!updated_by) {
        console.error("User ID not found in cookies!");
        return;
      }

      const response = await axiosClient.put("/admin/updateKeyword", {
        keyword_id: Number(keyword.keyword_id),
        keyword_name: keyword.keyword_name,
        updated_by: Number(updated_by),
      });

      //Show success toast if data exists
      if (response?.data) {
        toast({
          title: "Success!",
          description: `Keyword "${response.data.keyword_name}" updated successfully.`,
          duration: 2000,
        });

        // Refresh keywords after successful update
        //await fetchKeywords(Number(updated_by), keywordsCurrentPage);

        // Close editing mode
        setEditingKeyword(null);
      }
    } catch (error: any) {
      //Show error toast if request fails
      const message =
        error.response?.data?.detail ||
        error.message ||
        "Failed to update keyword";

      toast({
        title: "Error!",
        description: message,
        variant: "destructive",
        duration: 2000,
      });

      console.error("Request failed:", message);
    }
  };

  // const handleSelectAll = (checked: boolean) => {
  //   setReportData((prev) => prev.map((item) => ({ ...item, selected: checked })))
  // }

  // const handleSelectRow = (id: string, checked: boolean) => {
  //   setReportData((prev) => prev.map((item) => (item.id === id ? { ...item, selected: checked } : item)))
  // }

  // const handleDownload = (format: "excel" | "pdf") => {
  //   const selectedRows = reportData.filter((row) => row.selected)
  //   if (selectedRows.length === 0) {
  //     alert("Please select at least one row to download")
  //     return
  //   }
  //   // Here you would implement actual download logic
  //   console.log(`Downloading ${selectedRows.length} rows as ${format}`)
  // }

  // const handleEffortChange = (id: string, field: "efforts" | "keywordEfforts", value: number) => {
  //   setReportData((prev) => prev.map((item) => (item.id === id ? { ...item, [field]: value } : item)))
  // }

  const [latestSync, setLastSync] = useState<Date | null>(null);

  useEffect(() => {
    fetchLastSyncData();
  }, []);
  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-4 py-4">
        {/* Header */}
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Admin Dashboard
            </h1>
            <p className="text-gray-600 dark:text-gray-300 mt-2">
              Last sync: {latestSync ? latestSync.toLocaleString() : ""}
            </p>
          </div>
          <div className="flex space-x-4">
            {/* <Button onClick={handleManualSync} disabled={isLoading} variant="outline">
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
              {isLoading ? "Syncing..." : "Manual Sync"}
            </Button> */}
             {/* <DateFilter
              fetchDashboardData={(from, to) => {
                if (userId !== null) fetchDashboardData(from, to, userId);
              }}
              loading={loadingDashboard}
            /> */}

             <DateFilter
  fetchDashboardData={(from, to) => {
    if (userId !== null) {
      fetchDashboardData(from, to, userId);
      fetchChartData(from, to, userId);
      fetchTopKeywords(from,to,userId)
    }
  }}
  loading={loadingDashboard}
/>

            <Button onClick={handleLogout} variant="outline">
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>

        {/* ------Admin Dashboard card Data Binding---- */}
        {/* Here My Card Data Is Display On Admin Dashboard */}
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-4">
          {loadingDashboard ? (
            <p>Loading dashboard metrics...</p>
          ) : (
            <>
              <MetricCard
                title="Total R&D Effort"
                value={`${dashboardData?.total_effort ?? 0} hrs`}
                change="+12%"
                icon={<Clock className="h-5 w-5" />}
                trend="up"
              />
              <MetricCard
                title="Active Users"
                value={`${dashboardData?.active_users ?? 0}`}
                change="+3"
                icon={<Users className="h-5 w-5" />}
                trend="up"
              />
              <MetricCard
                title="Emails Processed"
                value={`${dashboardData?.emails_processed ?? 0}`}
                change="+156"
                icon={<Mail className="h-5 w-5" />}
                trend="up"
              />

              <MetricCard
                title="Meetings Processed"
                value={`${dashboardData?.meetings_processed ?? 0}`}
                change="+156"
                icon={<Mail className="h-5 w-5" />}
                trend="up"
              />

              <MetricCard
                title="Documents Analyzed"
                value={`${dashboardData?.documents_analyzed ?? 0}`}
                change="+28"
                icon={<FileText className="h-5 w-5" />}
                trend="up"
              />
            </>
          )}
        </div>

        {/* Main Content */}
        <Card>
          <CardContent>
            <Tabs defaultValue="overview" className="space-y-4">
              <TabsList className="mb-[0.5rem] px-0 flex w-full [&>*]:flex-1 [&>*]:text-center [&>*]:hover:bg-gradient-to-r [&>*]:hover:from-orange-500 [&>*]:hover:to-yellow-500 [&>*]:hover:text-white [&>*]:transition-all [&>*]:duration-300">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="users">Users</TabsTrigger>
                <TabsTrigger value="categories-value">Categories</TabsTrigger>
                <TabsTrigger value="keywords">Keywords</TabsTrigger>
                <TabsTrigger value="business-rules">Business Rules</TabsTrigger>
                <TabsTrigger value="report">Transactions</TabsTrigger>
              </TabsList>

              <TabsContent value="overview" className="space-y-4">
                <div className="grid md:grid-cols-2 gap-6">
                  <Card>
                    <CardHeader>
                       <CardTitle>Effort Trends</CardTitle> 
                      {/* <CardDescription>
                    R&D effort over the last 30 days
                  </CardDescription> */}
                    </CardHeader>
                    <CardContent className="max-h-[16rem] h-[16rem] overflow-y-auto">
                      <div className="">
                        {/* <BarChart3 className="h-16 w-16" />
                    <span className="ml-4">Chart visualization would go here</span> */}

                        <ChartContainer
                          className="w-full h-55 max-h-55 overflow-auto"
                          id="weekly-stats"
                          config={{
                            month_name: {
                              color: "#4ade80",
                              label: "Month Name",
                            },
                            total_hours: {
                              color: "#60a5fa",
                              label: "Total Hours",
                            },
                          }}
                        >
                          <Recharts.BarChart
                            data={weeklyStats || []}
                            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                          >
                            <Recharts.XAxis dataKey="week_of_month" />
                            <Recharts.YAxis />
                            <Recharts.CartesianGrid strokeDasharray="3 3" />

                            <Recharts.Bar
                              barSize={20}
                              fill="#60a5fa"
                              dataKey="total_hours"
                              name="total hours"
                            />

                            <ChartTooltip content={<ChartTooltipContent />} />
                            <ChartLegend content={<ChartLegendContent />} />
                          </Recharts.BarChart>
                        </ChartContainer>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Top Keywords */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Top Keywords</CardTitle> 
                      {/* <CardDescription>
                    Most frequently detected R&D keywords
                  </CardDescription> */}
                    </CardHeader>
                    <CardContent className="max-h-[16rem] overflow-y-auto">
                      <div className="space-y-4">
                        {topKeyword?.top_keywords.map(([keyword, count], i) => (
                          <KeywordItem
                            key={i}
                            keyword={keyword}
                            count={count}
                          />
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              {/* User Creation With Pagination */}
              <TabsContent value="users" className="space-y-4">
                <Card className="gap-3 disable-styles">
                  <CardHeader className="flex flex-row items-center justify-between mb-[0.5rem] px-0">
                    <div>{/* <CardTitle> List of Users</CardTitle> */}</div>
                    {/* Search + Create Button Container */}
                    <div className="flex items-center space-x-2">
                      {/* Users Search */}
                      <SearchBar
                        value={userSearchQuery}
                        onChange={setUserSearchQuery}
                        onSearch={() => fetchUsers(userId!, 1)}
                        placeholder="Search users..."
                      />

                      {/* Create User Button */}
                      <Dialog
                        open={isCreateUserDialogOpen}
                        onOpenChange={setIsCreateUserDialogOpen}
                      >
                        <DialogTrigger asChild>
                          <Button size="sm" className="h-9 w-9">
                            <Plus className="h-5 w-5 m-auto" />
                          </Button>
                        </DialogTrigger>
                        <CreateUserDialog
                          open={isCreateUserDialogOpen}
                          onClose={() => setIsCreateUserDialogOpen(false)}
                          fetchUsers={fetchUsers}
                        />
                      </Dialog>
                    </div>
                  </CardHeader>
                  <CardContent className="max-h-[12rem] overflow-y-auto  px-0">
                    {/* Listing the Users */}
                    <div className="grid grid-cols-3 gap-x-4 gap-y-3">
                      {loadingUsers ? (
                        <p>Loading users...</p>
                      ) : !users || users.length === 0 ? (
                        <p>No users found.</p>
                      ) : (
                        users.map((u: any) => (
                          <UserActivityItem
                            key={u.user_id}
                            name={u.user_name}
                            role={u.org_name}
                            emails={u.email_count}
                            isActive={u.is_active}
                            lastSync={
                              lastSyncData[u.user_id]
                                ? new Date(
                                    lastSyncData[u.user_id]
                                  ).toLocaleString()
                                : "No Mail Sync "
                            }
                            onToggle={() =>
                              handleToggle(u.user_id, u.is_active === 1 ? 0 : 1)
                            }
                          />
                        ))
                      )}
                    </div>
                  </CardContent>
                  <CardFooter className="px-0">
                    {/* Pagination Controls */}
                    <Pagination className="d-flex justify-between items-center">
                      <PaginationContent className=" flex justify-end mt-4">
                        <PaginationItem>
                          <PaginationPrevious
                            onClick={() =>
                              setCurrentPage((p) => Math.max(1, p - 1))
                            }
                            className={
                              currentPage === 1
                                ? "pointer-events-none opacity-50"
                                : ""
                            }
                          />
                        </PaginationItem>
                        <span className="px-4 py-2 text-sm">
                          Page {currentPage} of {totalPages}
                        </span>
                        <PaginationItem>
                          <PaginationNext
                            onClick={() =>
                              setCurrentPage((p) => Math.min(totalPages, p + 1))
                            }
                            className={
                              currentPage === totalPages
                                ? "pointer-events-none opacity-50"
                                : ""
                            }
                          />
                        </PaginationItem>
                      </PaginationContent>
                      <div className="flex justify-end items-center mt-2 space-x-2">
                        <label className="text-sm">Rows per page:</label>
                        <select
                          value={limit}
                          onChange={(e) => {
                            const newLimit = Number(e.target.value);
                            setLimit(newLimit);
                            setCurrentPage(1);
                            fetchUsers(userId!, 1, userSearchQuery, newLimit); // ✅ search + limit + page reset
                          }}
                          className="border px-2 py-1 rounded focus:outline-none"
                        >
                          <option value={5}>5</option>
                          <option value={10}>10</option>
                          <option value={20}>20</option>
                          <option value={50}>50</option>
                        </select>
                      </div>
                    </Pagination>
                  </CardFooter>
                </Card>
              </TabsContent>

              {/* ------------------------category start--------------------- */}
              <CategoriesTab />
              {/* ------------------------category end--------------------- */}

              {/* Keyword Creation With Pagination */}
              <TabsContent value="keywords" className="space-y-4">
                <Card className="gap-3 disable-styles ">
                  <CardHeader className="flex flex-row items-center justify-between mb-[0.5rem] px-0">
                    <div>
                      {/* <CardTitle>Keyword Management</CardTitle> */}
                      {/* <CardDescription>
                    Configure R&D keywords and their weights
                  </CardDescription> */}
                    </div>
                    <div className="flex items-center space-x-2">
                      <SearchBar
                        value={keywordSearchQuery}
                        onChange={setKeywordSearchQuery}
                        onSearch={() => fetchKeywords(keywordsCurrentPage)}
                        placeholder="Search keywords..."
                      />

                      {/* Create Button */}
                      <Dialog
                        open={isCreateKeywordDialogOpen}
                        onOpenChange={setIsCreateKeywordDialogOpen}
                      >
                        <DialogTrigger asChild>
                          <Button size="sm" className="h-9 w-9">
                            <Plus className="h-4 w-4 m-auto" />
                          </Button>
                        </DialogTrigger>
                        <CreateKeywordDialog
                          open={isCreateKeywordDialogOpen}
                          onClose={() => setIsCreateKeywordDialogOpen(false)}
                          fetchKeywords={handleKeywordCreated}
                        />
                      </Dialog>
                    </div>
                  </CardHeader>

                  <CardContent className="max-h-[12rem] overflow-y-auto  px-0">
                    {/* Listing the Keywords */}
                    <div className="grid grid-cols-3 gap-x-4 gap-y-3">
                      {loadingKeywords ? (
                        <p>Loading keywords...</p>
                      ) : keywords.length === 0 ? (
                        <p>No keywords found.</p>
                      ) : (
                        keywords.map((k: any) => (
                          <KeywordEditItem
                            key={k.keyword_id}
                            keyword_name={{
                              id: k.keyword_id,
                              name: k.keyword_name,
                              isActive: k.is_active,
                            }}
                            categoryName={'Categories:'+k.category_name}
                            isEditing={editingKeyword === k.keyword_id}
                            onEdit={() => handleEditKeyword(k.keyword_id)}
                            onSave={(updatedText) =>
                              handleSaveKeyword({
                                keyword_id: k.keyword_id,
                                keyword_name: updatedText,
                              })
                            }
                            onCancel={handleCancelEditKeyword}
                            onToggle={() =>
                              handleKeywordToggle(
                                k.keyword_id,
                                k.is_active === 1 ? 0 : 1
                              )
                            } //Toggle Handler
                          />
                        ))
                      )}
                    </div>
                  </CardContent>
                  <CardFooter className="px-0">
                    <Pagination className="d-flex justify-between items-center">
                      <PaginationContent className=" flex justify-end mt-4">
                        <PaginationItem>
                          <PaginationPrevious
                            onClick={() =>
                              setKeywordsCurrentPage((p) => Math.max(1, p - 1))
                            }
                            className={
                              keywordsCurrentPage === 1
                                ? "pointer-events-none opacity-50"
                                : ""
                            }
                          />
                        </PaginationItem>

                        <span className="px-4 py-2 text-sm">
                          Page {keywordsCurrentPage} of {keywordsTotalPages}
                        </span>

                        <PaginationItem>
                          <PaginationNext
                            onClick={() =>
                              setKeywordsCurrentPage((p) =>
                                Math.min(keywordsTotalPages, p + 1)
                              )
                            }
                            className={
                              keywordsCurrentPage === keywordsTotalPages
                                ? "pointer-events-none opacity-50"
                                : ""
                            }
                          />
                        </PaginationItem>
                      </PaginationContent>

                      <div className="flex justify-end items-center mt-2 space-x-2">
                        <label className="text-sm">Rows per page:</label>
                        <select
                          value={keywordsLimit}
                          onChange={(e) => {
                            const newLimit = Number(e.target.value);
                            setKeywordsLimit(newLimit);
                            setKeywordsCurrentPage(1); // reset to page 1
                            fetchKeywords(1, keywordSearchQuery, newLimit); //pass search new limit
                          }}
                          className="border px-2 py-1 rounded focus:outline-none"
                        >
                          <option value={5}>5</option>
                          <option value={10}>10</option>
                          <option value={20}>20</option>
                          <option value={50}>50</option>
                        </select>
                      </div>
                    </Pagination>
                  </CardFooter>
                </Card>
              </TabsContent>

              {/* ------------------------business rule component(start)--------------------- */}
              <BusinessRulesTab />
              {/* ------------------------business rule component(end)--------------------- */}

              {/* <TabsContent value="business-rules" className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Business Rules</CardTitle>
                  <CardDescription>Manage R&D effort calculation rules</CardDescription>
                </div>
                <Dialog open={isCreateBusinessRuleDialogOpen} onOpenChange={setIsCreateBusinessRuleDialogOpen}>
                  <DialogTrigger asChild>
                    <Button size="sm">
                      <Plus className="h-4 w-4 mr-2" />
                      Create New
                    </Button>
                  </DialogTrigger>
                  <CreateBusinessRuleDialog onClose={() => setIsCreateBusinessRuleDialogOpen(false)} />
                </Dialog>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {businessRules.map((rule) => (
                    <BusinessRuleItem
                      key={rule.id}
                      rule={rule}
                      isEditing={editingBusinessRule === rule.id}
                      onEdit={() => handleEditBusinessRule(rule.id)}
                      onSave={() => handleSaveBusinessRule(rule.id)}
                      onCancel={handleCancelEdit}
                    />
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent> */}

              {/* <TabsContent value="report" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Report</CardTitle>
                <CardDescription>View and export R&D activity data</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Date Range Filter }
                  <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
                    <Calendar className="h-5 w-5 text-gray-500" />
                    <div className="flex items-center space-x-2">
                      <Label htmlFor="date-from">From:</Label>
                      <Input
                        id="date-from"
                        type="date"
                        value={dateRange.from}
                        onChange={(e) => setDateRange((prev) => ({ ...prev, from: e.target.value }))}
                        className="w-40"
                      />
                    </div>
                    <div className="flex items-center space-x-2">
                      <Label htmlFor="date-to">To:</Label>
                      <Input
                        id="date-to"
                        type="date"
                        value={dateRange.to}
                        onChange={(e) => setDateRange((prev) => ({ ...prev, to: e.target.value }))}
                        className="w-40"
                      />
                    </div>
                    <Button variant="outline" size="sm">
                      <Filter className="h-4 w-4 mr-2" />
                      Apply Filter
                    </Button>
                  </div>

                  { Download Buttons }
                  <div className="flex justify-between items-center">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="select-all"
                        checked={reportData.every((row) => row.selected)}
                        onCheckedChange={handleSelectAll}
                      />
                      <Label htmlFor="select-all" className="text-sm font-medium">
                        Select All ({reportData.filter((row) => row.selected).length} selected)
                      </Label>
                    </div>
                    <div className="flex space-x-2">
                      <Button onClick={() => handleDownload("excel")} size="sm">
                        <Download className="h-4 w-4 mr-2" />
                        Download Excel
                      </Button>
                      <Button onClick={() => handleDownload("pdf")} size="sm" variant="outline">
                        <Download className="h-4 w-4 mr-2" />
                        Download PDF
                      </Button>
                    </div>
                  </div>

                  { Report Table }
                  <div className="border rounded-lg overflow-hidden">
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Select
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Entity Type
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Date
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Sender
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider" style={{ width: '150px', wordWrap: 'break-word', overflowWrap: 'break-word' }}>
                              Recipients
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Word Count
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Efforts (min)
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Keyword Count
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Keyword Efforts (min)
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {reportData.map((row) => (
                            <tr key={row.id} className="hover:bg-gray-50">
                              <td className="px-4 py-4 whitespace-nowrap">
                                <Checkbox
                                  checked={row.selected}
                                  onCheckedChange={(checked) => handleSelectRow(row.id, checked as boolean)}
                                />
                              </td>
                              <td className="px-4 py-4 whitespace-nowrap">
                                <Badge variant={row.entityType === "Email" ? "default" : "secondary"}>
                                  {row.entityType}
                                </Badge>
                              </td>
                              <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">{row.date}</td>
                              <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">{row.sender}</td>
                              <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">{row.recipients}</td>
                              <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">{row.wordCount}</td>
                              <td className="px-4 py-4 whitespace-nowrap">
                                <Input
                                  type="number"
                                  value={row.efforts}
                                  onChange={(e) =>
                                    handleEffortChange(row.id, "efforts", Number.parseInt(e.target.value))
                                  }
                                  className="w-20 text-sm"
                                />
                              </td>
                              <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">{row.keywordCount}</td>
                              <td className="px-4 py-4 whitespace-nowrap">
                                <Input
                                  type="number"
                                  value={row.keywordEfforts}
                                  onChange={(e) =>
                                    handleEffortChange(row.id, "keywordEfforts", Number.parseInt(e.target.value))
                                  }
                                  className="w-20 text-sm"
                                />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent> */}
              <TabsContent value="report" className="space-y-4">
                <Card className="disable-styles">
                  <CardHeader className=" px-0">
                    {/* <CardTitle>Transactions</CardTitle> */}
                    {/* <CardDescription>
                  View and export R&D activity data
                </CardDescription> */}
                  </CardHeader>
                  <CardContent className="px-0">
                    <ReportSection />
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

{
  /* Card Data which data is store  */
}
function MetricCard({
  title,
  value,
  change,
  icon,
  trend,
}: {
  title: string;
  value: string;
  change: string;
  icon: React.ReactNode;
  trend: "up" | "down";
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {/* <p className={`text-xs ${trend === "up" ? "text-green-600" : "text-red-600"}`}>
          <TrendingUp className="h-3 w-3 inline mr-1" />
          {change} from last month
        </p> */}
      </CardContent>
    </Card>
  );
}

// Related To Keyword
function KeywordsActivityItem({
  keyword_name,

  status,
}: {
  keyword_name: string;
  status: "active" | "warning";
}) {
  return (
    <div className="flex items-center justify-between p-4 border rounded-lg">
      <div className="flex items-center space-x-4">
        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
          <Users className="h-5 w-5 text-blue-600" />
        </div>
        <div>
          <p className="font-medium">{keyword_name}</p> {/*Now it shows */}
        </div>
      </div>
      <Badge variant={status === "active" ? "default" : "destructive"}>
        {status}
      </Badge>
    </div>
  );
}

function KeywordItem({ keyword, count }: { keyword: string; count: number }) {
  return (
    <div className="flex justify-between items-center">
      <span className="font-medium">{keyword}</span>
      <Badge variant="secondary">{count}</Badge>
    </div>
  );
}

function KeywordEditItem({
  keyword_name,
  isEditing,
  onEdit,
  onSave,
  onCancel,
  // isActive,
  categoryName,
  onToggle,
}: {
  keyword_name: { id: string; name: string; isActive: 1 | 0 };
  isEditing: boolean;
  onEdit: () => void;
  onSave: (updatedText: string) => void; // pass updated text here
  onCancel: () => void;
  // isActive: 1 | 0; // <-- strict type
  onToggle: () => void;
  categoryName?: string;
}) {
  const [editedKeyword, setEditedKeyword] = useState(keyword_name);

  useEffect(() => {
    setEditedKeyword(keyword_name);
  }, [keyword_name]);

  return (
    <div className="grid grid-cols-[75%_1fr] p-2 border rounded-lg">
      <div className="flex-1 ">
        {isEditing ? (
          <>
            <Input
              value={editedKeyword.name}
              onChange={(e) =>
                setEditedKeyword((prev) => ({ ...prev, name: e.target.value }))
              }
              placeholder="Keyword Name"
            />
          </>
        ) : (
          <>
            <div>
              <p className="font-medium">{keyword_name.name}</p>
              {categoryName && (
                <p className="text-sm text-gray-500">{categoryName}</p>
              )}
            </div>
          </>
        )}
      </div>
      <div className="flex items-center justify-end space-x-2 ml-4">
        {/* {isEditing ? (
          <>
            <Button
              size="sm"
              onClick={() => onSave(editedKeyword.name)} //send updated text
            >
              <Save className="h-4 w-4" />
            </Button>
            <Button size="sm" variant="outline" onClick={onCancel}>
              <X className="h-4 w-4" />
            </Button>
          </>
        ) : 
        (
          <Button size="sm" variant="outline" onClick={onEdit}>
            <Edit className="h-4 w-4" />
          </Button>
        )
        } */}

        <div
          onClick={onToggle}
          className={`w-13 h-6 flex items-center rounded-full p-1 cursor-pointer transition-all duration-300 ${
            keyword_name.isActive === 1 ? "bg-orange-500" : "bg-gray-100"
          }`}
        >
          <div
            className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform duration-300 ${
              keyword_name.isActive === 1 ? "translate-x-7" : "translate-x-0"
            }`}
          ></div>
        </div>
      </div>
    </div>
  );
}

//Related To User
function UserActivityItem({
  name,
  role,
  // effort,
  lastSync,
  emails,

  isActive,
  onToggle,
}: {
  name: string;
  role: string;
  lastSync: string;
  // effort: string
  emails: number;

  isActive: 1 | 0; // <-- strict type
  onToggle: () => void;
}) {
  return (
    <div className="grid grid-cols-[75%_1fr] items-center p-2 border rounded-lg">
      {/* Left Section: Icon + Name + Role */}
      <div className="flex items-center space-x-4 overflow-hidden">
        <div className="flex items-center flex-col justify-center space-y-1">
          <span className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
            <Users className="h-4 w-4 text-blue-600" />
          </span>
          {/* Center Section: Emails Count */}
          <span className="flex justify-center items-center">
            <p className="text-sm text-gray-600 dark:text-gray-300 whitespace-nowrap">
              {emails} emails
            </p>
          </span>
        </div>
        <div className="min-w-0">
          <p className="font-medium truncate">{name}</p>
          <p className="text-sm text-gray-600 dark:text-gray-300 truncate">
            {role}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-300 truncate">
            Last Sync: {lastSync}
          </p>
        </div>
      </div>

      {/* Right Section: Toggle Button */}
      <div className="flex justify-end">
        <div
          onClick={onToggle}
          className={`w-13 h-6 flex items-center rounded-full p-1 cursor-pointer transition-all duration-300 ${
            isActive === 1
              ? "bg-orange-500"
              : "bg-gray-100 outline outline-1 outline-gray-300"
          }`}
        >
          <div
            className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform duration-300 ${
              isActive === 1 ? "translate-x-7" : "translate-x-0"
            }`}
          ></div>
        </div>
      </div>
    </div>
  );
}

function KeywordConfigItem({
  keyword,
  weight,
  category,
  matches,
}: {
  keyword: string;
  weight: number;
  category: string;
  matches: number;
}) {
  return (
    <div className="flex items-center justify-between p-4 border rounded-lg">
      <div>
        <p className="font-medium">{keyword}</p>
        <p className="text-sm text-gray-600 dark:text-gray-300">{category}</p>
      </div>
      <div className="flex items-center space-x-4">
        <div className="text-right">
          <p className="text-sm">Weight: {weight}min</p>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            {matches} matches
          </p>
        </div>
        <Button size="sm" variant="outline">
          Edit
        </Button>
      </div>
    </div>
  );
}

//Related To Business Rule
// function BusinessRuleItem({
//   rule,
//   isEditing,
//   onEdit,
//   onSave,
//   onCancel,
// }: {
//   rule: { id: string; name: string; wordCount: number; efforts: number };
//   isEditing: boolean;
//   onEdit: () => void;
//   onSave: () => void;
//   onCancel: () => void;
// }) {
//   const [editedRule, setEditedRule] = useState(rule);

//   useEffect(() => {
//     setEditedRule(rule);
//   }, [rule]);

//   return (
//     <div className="flex items-center justify-between p-4 border rounded-lg">
//       <div className="flex-1 grid grid-cols-3 gap-4">
//         {isEditing ? (
//           <>
//             <Input
//               value={editedRule.name}
//               onChange={(e) =>
//                 setEditedRule((prev) => ({ ...prev, name: e.target.value }))
//               }
//               placeholder="Rule Name"
//             />
//             <Input
//               type="number"
//               value={editedRule.wordCount}
//               onChange={(e) =>
//                 setEditedRule((prev) => ({
//                   ...prev,
//                   wordCount: Number.parseInt(e.target.value),
//                 }))
//               }
//               placeholder="Word Count"
//             />
//             <Input
//               type="number"
//               value={editedRule.efforts}
//               onChange={(e) =>
//                 setEditedRule((prev) => ({
//                   ...prev,
//                   efforts: Number.parseInt(e.target.value),
//                 }))
//               }
//               placeholder="Efforts (min)"
//             />
//           </>
//         ) : (
//           <>
//             <div>
//               <p className="font-medium">{rule.name}</p>
//             </div>
//             <div>
//               <p className="text-sm text-gray-600 dark:text-gray-300">
//                 {rule.wordCount} words
//               </p>
//             </div>
//             <div>
//               <p className="text-sm text-gray-600 dark:text-gray-300">
//                 {rule.efforts} minutes
//               </p>
//             </div>
//           </>
//         )}
//       </div>
//       <div className="flex items-center space-x-2 ml-4">
//         {isEditing ? (
//           <>
//             <Button size="sm" onClick={onSave}>
//               <Save className="h-4 w-4" />
//             </Button>
//             <Button size="sm" variant="outline" onClick={onCancel}>
//               <X className="h-4 w-4" />
//             </Button>
//           </>
//         ) : (
//           <Button size="sm" variant="outline" onClick={onEdit}>
//             <Edit className="h-4 w-4" />
//           </Button>
//         )}
//       </div>
//     </div>
//   );
// }

{
  /* Fetching the Roles from backend */
}
type Role = {
  role_id: number;
  role_name: string;
};

/* Fetching the Categories from backend */

type Category = {
  cat_id: number;
  cat_name: number;
};

/* creating the users the Users */
interface CreateUserDialogProps {
  open: boolean;
  onClose: () => void;
  fetchUsers: (userId: number, page: number) => Promise<void>;
}

{
  /* creating the users the Users */
}
const CreateUserDialog: React.FC<CreateUserDialogProps> = ({
  open,
  onClose,
  fetchUsers,
}) => {
  const { toast } = useToast();
  const [selectedRole, setSelectedRole] = useState<number | null>(null);

  const [isLoading, setIsLoading] = useState(false);
  const [roles, setRoles] = useState<Role[]>([]);
  const [errors, setErrors] = useState<any>({});
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    async function fetchRoles() {
      try {
        const resp = await axiosClient.get("/admin/roles");
        setRoles(resp.data);
      } catch (err) {
        console.error("Error fetching roles:", err);
      }
    }
    fetchRoles();
  }, []);

  const createUser = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    setErrors({});

    const formData = new FormData(e.currentTarget);
    const name = formData.get("name") as string;
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;
    const role_id = formData.get("role_id") as string;
    const provider = formData.get("provider") as string;
    const department = formData.get("department") as string;

    // Client-side validation
    const newErrors: any = {};
   if (!name?.trim()) {
  newErrors.name = "Name is required";
} else if (name.trim().length < 4) {
  newErrors.name = "Name must be at least 4 characters long.";
}
    if (!password?.trim()) {
  newErrors.password = "Password is required";
} else {
  const passwordRegex = /^(?=[A-Z])(?=.*[a-zA-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]).{6,}$/;
  if (!passwordRegex.test(password)) {
    newErrors.password =
      "Password must start with a capital letter, contain at least one number, one special character, and be at least 6 characters long.";
  }
}
    if (!role_id) newErrors.role_id = "Role is required";
    if (!provider) newErrors.provider = "Provider is required";

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      setIsLoading(false);
      return;
    }

    try {
      const userId =
        sessionStorage.getItem("userid") || localStorage.getItem("userid");

      const payload = {
        user_name: name,
        mail_id: email,
        role_id: Number(role_id),
        password,
        org_id:
          Cookies.get("orgid") ||
          localStorage.getItem("orgid") ||
          sessionStorage.getItem("orgid"),
        user_id:
          Cookies.get("userid") ||
          localStorage.getItem("userid") ||
          sessionStorage.getItem("userid"),
        created_by:
          Cookies.get("userid") ||
          localStorage.getItem("userid") ||
          sessionStorage.getItem("userid"),
        folder_name: "default_folder",
       provider,
        department,
      };

      const response = await axiosClient.post("/admin/createUser", payload, {
        withCredentials: true,
      });

      toast({
        title: "Success!",
        description: `User ${response.data.user_name} created successfully.`,
      });

      onClose();
      if (userId) {
        setCurrentPage(1);
        await fetchUsers(Number(userId), 1);
      }
    } catch (err: any) {
      let backendData = err.response?.data;

      // ✅ If backend sends object, safely get errors/message as string
      let backendMsg =
        typeof backendData === "object" && backendData !== null
          ? backendData.errors ||
            backendData.message ||
            JSON.stringify(backendData)
          : backendData || err.message || "Failed to create user";

      // Remove "400:" prefix if exists
      const cleanMsg = backendMsg
        .toString()
        .replace(/^\d+:\s*/, "")
        .toLowerCase();

      // Check for duplicate email case
      if (cleanMsg.includes("user is already registered with this email")) {
        setErrors({ email: "User is already registered with this email." });

        toast({
          title: "Duplicate Email",
          description:
            "User is already registered with this email. Please use a different one.",
          variant: "destructive",
          duration: 3000,
        });
      } else {
        toast({
          title: "Error!",
          description: backendMsg, // always a string now
          variant: "destructive",
          duration: 3000,
        });
      }
    } finally {
      setIsLoading(false);
    }
  };
  return (
    <DialogContent className="sm:max-w-[425px]">
      <DialogHeader>
        <DialogTitle>Create New User</DialogTitle>
        <DialogDescription>
          Enter user details. Temporary credentials will be generated and
          simulated to be emailed.
        </DialogDescription>
      </DialogHeader>

      {/* Only ONE form here */}
      <form onSubmit={createUser} autoComplete="off">
        <div className="grid gap-4 py-4">
          {/* Name Field */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="name" className="text-right">
              Name<span className="text-red-500">*</span>
            </Label>
            <Input id="name" name="name" className="col-span-3" required />
            {errors?.name && (
              <p className="col-span-4 text-right text-sm text-red-500">
                {errors.name}
              </p>
            )}
          </div>

          {/* Email Field */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="email" className="text-right">
              Email<span className="text-red-500">*</span>
            </Label>
            <Input
              id="email"
              name="email"
              type="email"
              className="col-span-3"
              required
              autoComplete="off"
            />
            {errors?.email && (
              <p className="col-span-4 text-right text-sm text-red-500">
                {errors.email}
              </p>
            )}
          </div>

          {/* Password Field */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="password" className="text-right">
              Password<span className="text-red-500">*</span>
            </Label>
            <Input id="password" name="password" className="col-span-3" />
            {errors?.password && (
              <p className="col-span-4 text-right text-sm text-red-500">
                {errors.password}
              </p>
            )}
          </div>

          {/* Role Dropdown */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="role" className="text-right">
              Role<span className="text-red-500">*</span>
            </Label>
            <select
              id="role"
              name="role_id"
              value={selectedRole ?? ""}
              onChange={(e) => setSelectedRole(Number(e.target.value))}
              className="col-span-3 rounded-md border px-3 py-2"
              required
            >
              <option value="" disabled>
                Select a role
              </option>
              {roles.map((role) => (
                <option key={role.role_id} value={role.role_id}>
                  {role.role_name}
                </option>
              ))}
            </select>
            {errors?.role_id && (
              <p className="col-span-4 text-right text-sm text-red-500">
                {errors.role_id}
              </p>
            )}
          </div>

          {/* Provider Field */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">
              Provider<span className="text-red-500">*</span>
            </Label>
            <div className="col-span-3 flex items-center space-x-4">
              <label className="flex items-center space-x-2">
                <input type="radio" name="provider" value="google" required />
                <span>Gmail</span>
              </label>
              <label className="flex items-center space-x-2">
                <input type="radio" name="provider" value="outlook" required />
                <span>Outlook</span>
              </label>
            </div>
          </div>

          {/* Department Field */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="department" className="text-right">
              Department
            </Label>
            <Input id="department" name="department" className="col-span-3" />
            {errors?.department && (
              <p className="col-span-4 text-right text-sm text-red-500">
                {errors.department}
              </p>
            )}
          </div>
        </div>

        {/* Button inside same form */}
        <DialogFooter>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? "Creating..." : "Create User"}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  );
};

/* Creating the Keywords */
interface CreateKeywordDialogProps {
  open: boolean;
  onClose: () => void;
  fetchKeywords: (page: number) => Promise<void>;
}

{
  /* Creating the Keywords */
}
const CreateKeywordDialog: React.FC<CreateKeywordDialogProps> = ({
  open,
  onClose,
  fetchKeywords,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [errors, setErrors] = useState<any>({});
  const { toast } = useToast();

  useEffect(() => {
    async function fetchCategory() {
      try {
        const { userId, orgId } = getUserContext();
        const response = await axiosClient.get("/admin/categories", {
          params: {
            //send query params
            userId: userId,
            org_id: orgId,
          },
        });
        setCategories(response.data);
      } catch (err) {
        console.error("Error fetching categories:", err);
      }
    }
    fetchCategory();
  }, []);

  const createKeyword = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const userId =
        sessionStorage.getItem("userid") || localStorage.getItem("userid");
      const formData = new FormData(e.currentTarget);

      const payload = {
        cat_id: Number(formData.get("cat_id")),
        keyword_name: formData.get("keyword"),
        org_id:
          Cookies.get("orgid") ||
          localStorage.getItem("orgid") ||
          sessionStorage.getItem("orgid"),
        created_by:
          Cookies.get("userid") ||
          localStorage.getItem("userid") ||
          sessionStorage.getItem("userid"),
      };

      const response = await axiosClient.post("/admin/createKeyword", payload, {
        withCredentials: true,
      });

      if (response?.data) {
        toast({
          title: "Success!",
          description: "Keyword created successfully.",
          duration: 2000,
        });

        setTimeout(async () => {
          onClose();
          if (userId) {
            await fetchKeywords(1);
          }
        }, 2000);
      }
    } catch (err: any) {
      console.log("Backend Error:", err.response?.data);

      const backendData = err.response?.data;

      // Safely extract message if object, otherwise use raw string
      let backendMsg =
        typeof backendData === "object" && backendData !== null
          ? backendData.errors ||
            backendData.message ||
            "Failed to create keyword"
          : backendData || err.message || "Failed to create keyword";

      // Remove "400:" or any numeric prefix before checking
      const cleanMsg = backendMsg
        .toString()
        .replace(/^\d+:\s*/, "")
        .toLowerCase();

      if (cleanMsg.includes("keyword already exist")) {
        toast({
          title: "Duplicate Keyword",
          description:
            "Keyword already exists with this name, please try with a different name.",
          variant: "destructive",
          duration: 3000,
        });
      } else {
        toast({
          title: "Error!",
          description: backendMsg,
          variant: "destructive",
          duration: 3000,
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <DialogContent className="sm:max-w-[425px]">
      <DialogHeader>
        <DialogTitle>Create New Keyword</DialogTitle>
        <DialogDescription>
          Add a new R&D keyword with its configuration.
        </DialogDescription>
      </DialogHeader>
      <form onSubmit={createKeyword}>
        <div className="grid grid-cols-4 items-center gap-4">
          <Label htmlFor="category" className="text-right">
            Category
          </Label>
          <select
            id="category"
            name="cat_id"
            value={selectedCategory ?? ""}
            onChange={(e) => setSelectedCategory(Number(e.target.value))}
            className="col-span-3 rounded-md border px-3 py-2"
            required
          >
            <option value="" disabled>
              Select a Category
            </option>
            {categories.map((category) => (
              <option key={category.cat_id} value={category.cat_id}>
                {category.cat_name}
              </option>
            ))}
          </select>
          {errors?.cat_id && (
            <p className="col-span-4 text-right text-sm text-red-500">
              {errors.cat_id}
            </p>
          )}
        </div>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="keyword" className="text-right">
              Keyword
            </Label>
            <Input
              id="keyword"
              name="keyword"
              className="col-span-3"
              placeholder="Enter keyword"
              autoComplete="off"
            />
          </div>
          {/* <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="weight" className="text-right">
              Weight (min)
            </Label>
            <Input
              id="weight"
              type="number"
              className="col-span-3"
              placeholder="Enter weight"
            />
          </div> */}
        </div>
        <DialogFooter>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? "Creating..." : "Create Keyword"}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  );
};

// function CreateBusinessRuleDialog({ onClose }: { onClose: () => void }) {
//   return (
//     <DialogContent className="sm:max-w-[425px]">
//       <DialogHeader>
//         <DialogTitle>Create New Business Rule</DialogTitle>
//         <DialogDescription>Define a new rule for R&D effort calculation.</DialogDescription>
//       </DialogHeader>

//       <div className="grid gap-4 py-4">
//         <div className="grid grid-cols-4 items-center gap-4">
//           <Label htmlFor="rule-name" className="text-right">
//             Rule Name
//           </Label>
//           <Input id="rule-name" className="col-span-3" placeholder="Enter rule name" />
//         </div>
//         <div className="grid grid-cols-4 items-center gap-4">
//           <Label htmlFor="word-count" className="text-right">
//             Word Count
//           </Label>
//           <Input id="word-count" type="number" className="col-span-3" placeholder="Enter word count" />
//         </div>
//         <div className="grid grid-cols-4 items-center gap-4">
//           <Label htmlFor="efforts" className="text-right">
//             Efforts (min)
//           </Label>
//           <Input id="efforts" type="number" className="col-span-3" placeholder="Enter efforts in minutes" />
//         </div>
//       </div>
//       <DialogFooter>
//         <Button onClick={onClose}>Create Rule</Button>
//       </DialogFooter>
//     </DialogContent>
//   )

// }
