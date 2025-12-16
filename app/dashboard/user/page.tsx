"use client";

import type React from "react";
import { useState, useEffect } from "react";
import ReportSection from "../reportSection/ReportSection";
import Cookies from "js-cookie";
import DateFilter from "@/components/ui/DateFilter";
import * as Recharts from "recharts";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { initiateOAuth, handleOAuthCallback } from "@/actions/email-connection";
import axiosClient from "@/app/api/axiosClient";
import { useToast } from "@/hooks/use-toast";
import { useSearchParams, useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Mail,
  FileText,
  Clock,
  Download,
  RefreshCw,
  CheckCircle,
  XCircle,
  LinkIcon,
  Filter,
  LogOut,
  Plus,
  X,
  ChevronDown,
  Calendar,
  Loader2,
  RotateCcw,
  Subtitles,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { updateMailRowService } from "../user/reportService"

type DashboardData = {
  total_effort: number;
  emails_processed: number;
  documents_analyzed: number;
};

export default function UserDashboardPage() {
  const [displayProvider, setDisplayProvider] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isMailLoading, setIsMailLoading] = useState(true); // New state for mail loading
  // const [latestSync, setLastSync] = useState(new Date());
  const [emailConnectionStatus, setEmailConnectionStatus] = useState({
    connected: false,
    provider: null as string | null,
    lastScan: null as Date | null,
    emailAddress: null as string | null,
  });

  // const [dateRange, setDateRange] = useState({
  //   from: new Date(new Date().setMonth(new Date().getMonth() - 1))
  //     .toISOString()
  //     .split("T")[0],
  //   to: new Date().toISOString().split("T")[0],
  // });
  const [selectedRows, setSelectedRows] = useState<string[]>([]);
  const [reportData, setReportData] = useState([
    {
      id: "1",
      entityType: "Email",
      date: "2024-01-15",
      sender: "john.doe@company.com",
      recipients: "team@company.com",
      wordCount: 250,
      correspondingEfforts: "45 min",
      keywordRepetition: 3,
      efforts: "45 min",
    },
    {
      id: "2",
      entityType: "Document",
      date: "2024-01-14",
      sender: "jane.smith@company.com",
      recipients: "research@company.com",
      wordCount: 1200,
      correspondingEfforts: "2.5 hrs",
      keywordRepetition: 8,
      efforts: "2.5 hrs",
    },
    {
      id: "3",
      entityType: "Email",
      date: "2024-01-13",
      sender: "mike.wilson@company.com",
      recipients: "dev@company.com",
      wordCount: 180,
      correspondingEfforts: "30 min",
      keywordRepetition: 2,
      efforts: "30 min",
    },
  ]);

  const today = new Date();

  // first day of this month
  const firstDayPrevMonth = new Date(
    today.getFullYear(),
    today.getMonth() - 1,
    1
  );

  const formatDate = (d: Date) => d.toLocaleDateString("en-CA");

  const [folderdateRange, setfolderDateRange] = useState({
    from: formatDate(firstDayPrevMonth),
    to: formatDate(today),
  });

  const clearFilters = () => {
    const newDateRange = {
      from: formatDate(firstDayPrevMonth),
      to: formatDate(today),
    };
    setfolderDateRange(newDateRange);
    setItems([]);
  };

  const { toast } = useToast();
  const searchParams = useSearchParams();
  const router = useRouter();
  const [inputValue, setInputValue] = useState("");
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [loadingDashboard, setLoadingDashboard] = useState(true);
  const [userId, setUserId] = useState<number | null>(null);
  type Folder = {
    id: string;
    name: string;
  };
  const [allFolders, setAllFolders] = useState<Folder[]>([]);
  const [selectedFolders, setSelectedFolders] = useState<Folder[]>([]);
  const [items, setItems] = useState<Folder[]>([]);
  const [latestSync, setLastSync] = useState<Date | null>(null); //For last sync

  const [weeklyStats, setWeeklyStats] = useState<any[]>([]);
  const [topKeyword, setTopKeyword] = useState<TopKeyword | null>(null);
  const user_id = Cookies.get("userid") ? Number(Cookies.get("userid")) : null;
  const [loading, setLoading] = useState(false);

  type TopKeyword = {
    org_id: number;
    top_keywords: [string, number][];
  };

  const fetchDashboardData = async (
    from: string,
    to: string,
    userId: number
  ) => {
    setLoadingDashboard(true);
    try {
      const response = await axiosClient.get(
        "/userdash/userDashboardCardData",
        {
          params: {
            from_date: from,
            to_date: to,
            userId:
              Cookies.get("userid") ||
              localStorage.getItem("userid") ||
              sessionStorage.getItem("userid"),
            org_id:
              Cookies.get("orgid") ||
              localStorage.getItem("orgid") ||
              sessionStorage.getItem("orgid"),
          },
          withCredentials: true,
        }
      );
      // console.log("Dashboard API Response:", response.data);
      setDashboardData(response.data);
    } catch (err) {
      console.error("Error fetching user dashboard data:", err);
    } finally {
      setLoadingDashboard(false);
    }
  };

  //-------------Last Sync on user dashboard--------------//
  const fetchLastSyncData = async () => {
    try {
      const orgId = Number(
        Cookies.get("orgid") ||
        localStorage.getItem("orgid") ||
        sessionStorage.getItem("orgid")
      );

      const response = await axiosClient.get("/userdash/lastSync", {
        params: { user_id: user_id }, // already filtering by user?
      });

      const syncData = response?.data?.data;

      if (syncData?.length) {
        //Find sync for logged-in user
        const currentUserSync = syncData.find(
          (item: any) => item.user_id === user_id
        );

        if (currentUserSync?.last_sync) {
          const syncDate = new Date(currentUserSync.last_sync);
          setLastSync(syncDate);
        } else {
          setLastSync(null);
        }
      } else {
        setLastSync(null);
      }
    } catch (err) {
      console.error("Error fetching last sync data:", err);
      setLastSync(null);
    }
  };

  const currentUserId = "mock-user-id";

  const postFolder = async () => {
    if (!items || items.length === 0) {
      toast({
        title: "Validation Error",
        description: "Please select the folder.",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      // Fetch values from localStorage
      const mail_token =
        localStorage.getItem("mail_token") ||
        sessionStorage.getItem("mail_token");
      const user_id =
        localStorage.getItem("userid") || sessionStorage.getItem("userid");
      const org_id =
        localStorage.getItem("orgid") || sessionStorage.getItem("orgid");
      const provider =
        localStorage.getItem("provider") || sessionStorage.getItem("provider");

      if (!mail_token || !user_id || !org_id) {
        toast({
          title: "Error",
          description: "Missing required values in localStorage",
          variant: "destructive",
        });
        return;
      }

      // Construct payload
      const payload = {
        access_token: mail_token,
        folders: items.map((f) => f.name),
        user_id: Number(user_id),
        org_id: Number(org_id),
        provider: provider,
        from_date: folderdateRange.from,
        to_date: folderdateRange.to,
      };

      // Make POST request
      const response = await axiosClient.post("/auth/emails", payload);

      toast({
        title: "Success",
        description: "Folder name posted successfully!",
        variant: "default",
      });

        setLastSync(new Date());

      //------------Call updateMailRowService directly------------
      await updateMailRowService(String(user_id), String(org_id), true);

      //------------refresh dashboard------------
      if (userId !== null) {
       const today = new Date();
      const firstDayPrevMonth = new Date(
        today.getFullYear(),
        today.getMonth() - 1,
        1
      );

      var firstDay = formatDate(firstDayPrevMonth);
      var lastDay = formatDate(today);

        //fetchUsers(userId)
        //fetchKeywords(userId)

        fetchDashboardData(firstDay, lastDay, userId); //Based on Folder sync date range
        fetchChartData(firstDay, lastDay, userId);
        fetchTopKeywords(firstDay, lastDay, userId);
      }
      setLoading(false);

      return response.data;
    } catch (error: any) {
      // toast({
      //   title: "Error",
      //   description:
      //     error.response?.data?.message || "Something went wrong.",
      //   variant: "destructive",
      // });
      console.error("API Error:", error);

      //multiple patterns because backend might return data in different formats
      const backendError =
        error.response?.data?.detail?.error ||
        error.response?.data?.errors?.[0]?.error ||
        error.response?.data?.message ||
        error.message ||
        "Unexpected error occurred.";

      toast({
        title: "Error",
        description: backendError,
        variant: "destructive",
      });
      setLoading(false);
    }
  };
  const fetchFolders = async () => {
    try {
      const mail_token =
        localStorage.getItem("mail_token") ||
        sessionStorage.getItem("mail_token");

      if (!mail_token) throw new Error("Missing access token");

      const response = await axiosClient.post("/auth/fetch-all-folders", {
        access_token: mail_token,
        provider: localStorage.getItem("provider"), // <-- send in body
      });

      setAllFolders(response.data || []);
    } catch (err) {
      console.error("Error fetching folders:", err);
    }
  };

  const fetchMailEffort = async (mailId: number) => {
    try {
      const response = await axiosClient.post("/reports/mail", {
        user_id: 128,
      });
      console.log("Mail effort response:", response.data);
      toast({
        title: "Mail Effort Calculated",
        description: `Effort processed successfully for mail ID ${mailId}`,
        variant: "default",
      });
      return response.data;
    } catch (error: any) {
      console.error("Error fetching mail effort:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to calculate mail effort",
        variant: "destructive",
      });
    }
  };

  const handleManualSync = async () => {
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setLastSync(new Date());
    setIsLoading(false);
  };

  const handleConnectEmail = async (provider: "google" | "microsoft") => {
    try {
      await initiateOAuth(provider);
    } catch (error: any) {
      toast({
        title: "OAuth Initiation Failed",
        description: error.message || "Could not initiate OAuth flow.",
        variant: "destructive",
      });
    }
  };

  const handleRowSelect = (rowId: string) => {
    setSelectedRows((prev) =>
      prev.includes(rowId)
        ? prev.filter((id) => id !== rowId)
        : [...prev, rowId]
    );
  };

  const handleSelectAll = () => {
    setSelectedRows(
      selectedRows.length === reportData.length
        ? []
        : reportData.map((row) => row.id)
    );
  };

  const handleCellValueChange = (
    rowId: string,
    column: string,
    value: string
  ) => {
    setReportData((prev) =>
      prev.map((row) =>
        row.id === rowId
          ? {
            ...row,
            [column]:
              column === "wordCount" || column === "keywordRepetition"
                ? Number.parseInt(value) || 0
                : value,
          }
          : row
      )
    );
  };

  const handleDownload = (format: "excel" | "pdf") => {
    if (selectedRows.length === 0) {
      toast({
        title: "No rows selected",
        description: "Please select at least one row to download.",
        variant: "destructive",
      });
      return;
    }

    toast({
      title: "Download Started",
      description: `Downloading ${selectedRows.length
        } rows as ${format.toUpperCase()}...`,
    });
  };

  const handleLogout = () => {
    // Clear session/local storage
    sessionStorage.clear();
    localStorage.clear();

    // Remove all cookies
    Object.keys(Cookies.get()).forEach((cookie) => {
      Cookies.remove(cookie);
    });

    // Navigate to login page once
    router.replace("/login");
  };

  // Mock data for the logged-in user
  const currentUserStats = {
    totalEffort: "180 hrs",
    emailsProcessed: 156,
    documentsAnalyzed: 45,
    rdEmails: 120,
    nonRdEmails: 36,
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
        "/userdash/weekly-hours-previous-month",
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

  //------------Fetch Top Keywords On user Dashboard-------------//
  const fetchTopKeywords = async (
     from: string,
    to: string,
    userId: number

  ) => {
    setLoadingDashboard(true);
    try {
      const response = await axiosClient.get("/userdash/top-keywords", {
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
  }, []);

  useEffect(() => {
    // Initial fetch with current month
    if (userId !== null) {
      // const today = new Date();
      // const firstDay = new Date(
      //   today.getFullYear(),
      //   today.getMonth() - 1,
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

      fetchDashboardData(firstDay, lastDay, userId);//Based On Above Date Range Filter On User Dashboard
      fetchChartData(firstDay, lastDay, userId); //Based On Above Date Range Filter On User Dashboard
      fetchTopKeywords(firstDay, lastDay, userId);

      
    }
  }, [userId]);

  // useEffect(() => {
  //   async function fetchUserDashboardData() {
  //     const user_id = localStorage.getItem("userid") || sessionStorage.getItem("userid")
  //     if (!user_id) {
  //       toast({
  //         title: "Error",
  //         description: "Missing required values in localStorage",
  //         variant: "destructive",
  //       })
  //       return
  //     }

  //     try {
  //       const data = await getUserDashboardCardData();
  //       console.log("Dashboard API Response:", data);
  //       setDashboardData(data);
  //     } catch (err) {
  //       console.error("Error fetching user dashboard data:", err);
  //     } finally {
  //       setLoadingDashboard(false);
  //     }
  //   }

  //   fetchUserDashboardData();
  // }, []);

  // useEffect(() => {
  //   async function fetchUserDashboardData() {
  //     const user_id = localStorage.getItem("userid") ||  sessionStorage.getItem("userid")
  //     if ( !user_id) {
  //         toast({
  //           title: "Error",
  //           description: "Missing required values in localStorage",
  //           variant: "destructive",
  //         })
  //         return
  //       }

  //     try {
  //       const data = await getUserDashboardCardData();
  //       console.log("Dashboard API Response:", data);
  //       setDashboardData(data);
  //     } catch (err) {
  //       console.error("Error fetching user dashboard data:", err);
  //     } finally {
  //       setLoadingDashboard(false);
  //     }
  //   }

  //   fetchUserDashboardData();
  // }, []);

  // const addItem = () => {
  //   if (inputValue.trim() !== "") {
  //     setItems([...items, inputValue.trim()]);
  //     setInputValue("");
  //   }
  // };

  // const removeItem = (index: number) => {
  //   setItems(items.filter((_, i) => i !== index));
  // };
  // Mock user ID - in a real app, this would come from the authenticated session

  useEffect(() => {
    /////////////////////// Initial Data Load ///////////////////////
    // Load initial mail effort data on component mount

    const tokenFromQuery = searchParams.get("mail_token");
    if (tokenFromQuery) {
      localStorage.setItem("mail_token", tokenFromQuery);
      // console.log("Mail token saved:", tokenFromQuery);
      fetchFolders();
    }

    const loadEffortOnInit = async () => {
      try {
        // Example: hit API with first mail ID (id=1 from your mock data)
        if (reportData.length > 0) {
          const firstMailId = Number(reportData[0].id);
          // await fetchMailEffort(firstMailId)
        }
      } catch (err) {
        console.error("Effort init error:", err);
      }
    };

    loadEffortOnInit();

    const fetchConnectionStatus = async () => {
      // replace with real backend when available; keeping mock for now
      setEmailConnectionStatus({
        connected: false,
        provider: null,
        lastScan: null,
        emailAddress: null,
      });
    };
    fetchConnectionStatus();

    // Handle OAuth callback
    const code = searchParams.get("code");
    const provider = searchParams.get("provider");

    if (code && provider && !emailConnectionStatus.connected) {
      const connectEmail = async () => {
        try {
          const result = await handleOAuthCallback(
            code,
            provider as "google" | "microsoft",
            currentUserId
          );
          if (result.success) {
            toast({
              title: "Email Connected!",
              description: result.message,
              variant: "default",
            });
            setEmailConnectionStatus({
              connected: true,
              provider: result.provider,
              lastScan: new Date(),
              emailAddress: null, // emailAddress is not returned by the function
            });
            window.history.replaceState(
              {},
              document.title,
              window.location.pathname
            );
          } else {
            toast({
              title: "Connection Failed",
              description: result.message,
              variant: "destructive",
            });
          }
        } catch (error: any) {
          toast({
            title: "Connection Error",
            description:
              error.message ||
              "An unexpected error occurred during connection.",
            variant: "destructive",
          });
        }
      };
      connectEmail();
    }

    // Check for token in URL query parameters and call /emails API
    const token = searchParams.get("token");
    if (token) {
      const fetchMailData = async () => {
        try {
          setIsMailLoading(true);
          console.log(
            "Token found in URL, calling /emails API with token:",
            token
          );

          // const mailResponse = await axiosClient.post(
          //   "/auth/emails",
          //   { access_token: token }
          // )
          // console.log("Mail API response:", mailResponse.data)
          toast({
            title: "Mail Data Loaded",
            description: "Successfully fetched mail data from backend",
            variant: "default",
          });

          // Clean up the URL by removing the token parameter
          window.history.replaceState(
            {},
            document.title,
            window.location.pathname
          );
        } catch (mailError) {
          console.error("Error fetching mail:", mailError);
          toast({
            title: "Mail Fetch Error",
            description: "Failed to fetch mail data from backend",
            variant: "destructive",
          });
        } finally {
          setIsMailLoading(false);
        }
      };

      fetchMailData();
    } else {
      // No token in URL, set loading to false
      setIsMailLoading(false);
    }
  }, [searchParams, toast, emailConnectionStatus.connected, currentUserId]);

  useEffect(() => {
    setUserId(Cookies.get("userid") ? Number(Cookies.get("userid")) : null);
    //fetchChartData();
    //fetchTopKeywords();

    fetchLastSyncData(); //Fetching Last Sync
  }, []);

  //--------Display the username On User dashboard ----//
  const [userName, setUserName] = useState<string>("");
  useEffect(() => {
    const storedUser =
      localStorage.getItem("username") || sessionStorage.getItem("username");
    if (storedUser) setUserName(storedUser);
  }, []);

  useEffect(() => {
    const provider =
      localStorage.getItem('provider') || sessionStorage.getItem('provider');

    if (provider) {
      const capitalized = capitalizeFirstLetter(provider);
      setDisplayProvider(capitalized);
    }
  }, []);

  function capitalizeFirstLetter(str: string): string {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  return (
    <div className="min-h-screen relative">
      {loading && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/30 backdrop-blur-[2px] z-50">
          <div className="flex flex-col items-center space-y-4 text-white">
            <Loader2 className="h-10 w-10 animate-spin" />
            <p className="text-xl font-semibold">Loading...</p>
          </div>
        </div>
      )}
      <div className="container mx-auto px-4 py-4">
        {/* Header */}
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {userName ? `${userName} Dashboard` : "Dashboard"}
            </h1>
            <p className="text-gray-600 dark:text-gray-300">
              Last sync:{" "}
              {latestSync ? latestSync.toLocaleString() : "Not synced yet"}
            </p>
          </div>
          <div className="flex space-x-4">
            {/* <Button onClick={handleManualSync} disabled={isLoading} variant="outline">
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
              {isLoading ? "Syncing..." : "Manual Sync"}
            </Button> */}

            {/* <DateFilter
              fetchDashboardData={fetchDashboardData}
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
        <Card className="px-4 ">
          <Tabs defaultValue="dashboard" className="space-y-4 ">
            <TabsList className="grid w-full grid-cols-2 [&>*]:hover:bg-gradient-to-r [&>*]:hover:from-green-500 [&>*]:hover:to-cyan-500 [&>*]:hover:text-white [&>*]:transition-all [&>*]:duration-300">
              <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
              <TabsTrigger value="report">Transactions</TabsTrigger>
            </TabsList>

            <TabsContent
              value="dashboard"
              className="space-y-4 mb-0 max-h-[calc(100vh-250px)] min-h-[calc(100vh-250px)] overflow-auto"
            >
              {/* Email Connection Status */}
              <div className="flex flex-col md:flex-row md:items-center md:justify-between">
                <div>
                  <CardHeader>
                    <CardTitle>{displayProvider} Connection</CardTitle>
                    <CardDescription>
                      Connect your {displayProvider} to enable R&D effort tracking.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {emailConnectionStatus.connected ? (
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2 text-green-600 font-medium">
                          <CheckCircle className="h-5 w-5" />
                          <span>
                            Connected to{" "}
                            {emailConnectionStatus.provider === "google"
                              ? "Outlook"
                              : "Outlook"}
                          </span>
                          {emailConnectionStatus.lastScan && (
                            <span className="text-gray-500 text-sm ml-2">
                              (Last scanned:{" "}
                              {emailConnectionStatus.lastScan.toLocaleString()})
                            </span>
                          )}
                        </div>
                        {emailConnectionStatus.emailAddress && (
                          <div className="text-sm text-gray-600 dark:text-gray-300 font-medium">
                            {emailConnectionStatus.emailAddress}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <div className="flex items-center space-x-2 text-green-600 font-medium">
                          {/* <XCircle className="h-5 w-5" />
                        <span>Email not connected.</span>
                        <span>Connect with Microsoft</span> */}
                          <LinkIcon className="h-4 w-4 mr-2" />
                          Connected to {displayProvider}
                        </div>
                        {/* <div className="flex gap-4">
                        <Button onClick={() => handleConnectEmail("google")} className="flex-1">
                          <LinkIcon className="h-4 w-4 mr-2" />
                          Connect with Google
                        </Button>
                        <Button onClick={() => handleConnectEmail("microsoft")} className="flex-1">
                          <LinkIcon className="h-4 w-4 mr-2" />
                          Connect with Microsoft
                        </Button>
                      </div> */}
                      </div>
                    )}
                  </CardContent>
                </div>

                <Card className=" py-3 gap-2 max-w-3xl rounded-lg w-full float-right">
                  <CardHeader className="flex items-center justify-between px-4">
                    <h2 className="text-lg font-semibold">My Folders</h2>
                    <div className="flex space-x-2">
                      <Button
                        className=" px-3 
                                    rounded-md
                                    text-sm font-medium
                                    bg-gray-100 text-gray-700
                                    hover:bg-gray-200 hover:text-gray-900
                                    dark:bg-gray-800 dark:text-gray-200
                                    dark:hover:bg-gray-700 dark:hover:text-white
                                    border border-gray-300 dark:border-gray-600
                                    transition-colors duration-200
                                    "
                        variant="ghost"
                        size="sm"
                        onClick={clearFilters}
                        disabled={isLoading}
                      >
                        <RotateCcw className="h-4 w-4 mr-2" />
                        Clear
                      </Button>
                      <Button onClick={postFolder} className="h-8 py-0">
                        <RefreshCw /> Sync
                      </Button>
                    </div>
                  </CardHeader>

                  {/* Multi-select */}
                  {/* Multi-select dropdown */}
                  <CardContent className="flex gap-2 w-full justify-between px-4">
                    <div className="flex items-center flex-col space-x-4  dark:bg-gray-800 rounded-lg ">
                      <div className="flex items-center justify-between space-x-4  dark:bg-gray-800 rounded-lg w-full">
                        <div className="flex items-center space-x-2 w-full">
                          <Label htmlFor="date-from">From:</Label>
                          <Input
                            id="date-from"
                            type="date"
                            value={folderdateRange.from}
                            onChange={(e) =>
                              setfolderDateRange((prev) => ({
                                ...prev,
                                from: e.target.value,
                              }))
                            }
                            className="w-full bg-gray-50 dark:bg-gray-800 w-auto"
                            max={folderdateRange.to}
                          />
                        </div>

                        <div className="flex items-center space-x-2">
                          <Label htmlFor="date-to">To:</Label>
                          <Input
                            id="date-to"
                            type="date"
                            value={folderdateRange.to}
                            onChange={(e) =>
                              setfolderDateRange((prev) => ({
                                ...prev,
                                to: e.target.value,
                              }))
                            }
                            className="w-full bg-gray-50 dark:bg-gray-800 w-auto"
                            max={new Date().toISOString().split("T")[0]}
                            min={folderdateRange.from}
                          />
                        </div>
                        {/* <Button
                    variant="outline"
                    size="sm"
                    // onClick={() =>
                    //   fetchDashboardData(dateRange.from, dateRange.to, userId)
                    // }
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Filter className="h-4 w-4 mr-2" />
                    )}
                    {isLoading ? "Loading..." : "Apply Filter"}
                  </Button> */}
                      </div>
                    </div>
                    <div className="flex gap-2 w-full">
                      <DropdownMenu>
                        <DropdownMenuTrigger className="flex items-center h-9 overflow-auto text-sm justify-between px-2  border rounded bg-white dark:bg-gray-800 w-full">
                          <span className="">
                            {items.length > 0
                              ? items.map((f) => f.name).join(", ")
                              : "Select folders"}
                          </span>
                          <ChevronDown className="ml-2 w-4 h-4 text-gray-500" />
                        </DropdownMenuTrigger>

                        <DropdownMenuContent
                          className="w-60 max-h-64 overflow-auto bg-white dark:bg-gray-800 border rounded shadow-lg p-2"
                          sideOffset={4}
                        >
                          {allFolders.map((folder) => (
                            <DropdownMenuCheckboxItem
                              key={folder.id}
                              checked={items.some((f) => f.id === folder.id)}
                              onCheckedChange={() =>
                                setItems((prev) =>
                                  prev.some((f) => f.id === folder.id)
                                    ? prev.filter((f) => f.id !== folder.id)
                                    : [...prev, folder]
                                )
                              }
                            >
                              {folder.name}
                            </DropdownMenuCheckboxItem>
                          ))}
                        </DropdownMenuContent>
                      </DropdownMenu>
                      {/* Display added folders
                  <ul className="space-y-2 h-12 overflow-auto  flex-1">
                    {items.map((item) => (
                      <li
                        key={item.id}
                        className="flex justify-between items-center p-2 border rounded hover:bg-gray-50"
                      >
                        <span>{item.name}</span>
                        <button
                          onClick={() =>
                            setItems((prev) =>
                              prev.filter((i) => i.id !== item.id)
                            )
                          }
                          className="text-red-500 hover:text-red-700"
                        >
                          <X size={16} />
                        </button>
                      </li>
                    ))}
                  </ul> */}
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {loadingDashboard ? (
                  <p>Loading dashboard metrics...</p>
                ) : (
                  <>
                    <MetricCard
                      title="Total R&D Effort"
                      value={`${dashboardData?.total_effort ?? 0} hrs`}
                      icon={<Clock className="h-5 w-5" />}
                    />
                    <MetricCard
                      title="Emails Processed "
                      value={`${dashboardData?.emails_processed ?? 0}`}
                      icon={<Mail className="h-5 w-5" />}
                    />

                    <MetricCard
                      title="Meetings Processed "
                      value={`${dashboardData?.meetings_processed ?? 0}`}
                      icon={<FileText className="h-5 w-5" />}
                    />
                    <MetricCard
                      title="Documents Analyzed "
                      value={`${dashboardData?.documents_analyzed ?? 0}`}
                      icon={<FileText className="h-5 w-5" />}
                    />
                  </>
                )}
              </div>

              <div className="mb-0">
                <div className="">
                  <div className="grid md:grid-cols-2 gap-6">
                    <Card>
                      <CardHeader>
                        <CardTitle>Effort Trends</CardTitle>
                        {/* <CardDescription>
                        R&D effort over the last 30 days
                      </CardDescription> */}
                      </CardHeader>
                      <CardContent>
                        <div className="">
                          {/* <BarChart3 className="h-16 w-16" />
                    <span className="ml-4">Chart visualization would go here</span> */}

                          <ChartContainer
                            className="w-full h-50 max-h-50 overflow-auto"
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
                              // emailsProcessed: { color: "#facc15", label: "Emails Processed" },
                              // documentsAnalyzed: { color: "#14b8a6", label: "Documents Analyzed" },
                            }}
                          >
                            <Recharts.BarChart
                              data={weeklyStats || []}
                              margin={{
                                top: 20,
                                right: 30,
                                left: 20,
                                bottom: 5,
                              }}
                            >
                              <Recharts.XAxis dataKey="week_of_month" />
                              <Recharts.YAxis />
                              <Recharts.CartesianGrid strokeDasharray="3 3" />

                              <Recharts.Bar
                                barSize={30}
                                fill=" #60a5fa"
                                dataKey="total_hours"
                                name="total hours"
                              />
                              {/* <Recharts.Bar fill="#4ade80" dataKey="activeUsers" name="Active Users" />
                        <Recharts.Bar fill="#facc15" dataKey="emailsProcessed" name="Emails Processed" />
                        <Recharts.Bar fill="#14b8a6" dataKey="documentsAnalyzed" name="Documents Analyzed" /> */}
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
                      <CardContent className="w-full h-50 max-h-50 overflow-auto">
                        <div className="space-y-4">
                          {topKeyword?.top_keywords.map(
                            ([keyword, count], i) => (
                              <KeywordItem
                                key={i}
                                keyword={keyword}
                                count={count}
                              />
                            )
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </div>
              {/* Email Classification */}
              <Card className="hidden">
                <CardHeader>
                  <CardTitle>Email Classification Overview</CardTitle>
                  <CardDescription>
                    Breakdown of your emails classified as R&D or Non-R&D
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <EmailClassificationItem
                      type="R&D Emails"
                      count={currentUserStats.rdEmails}
                      total={currentUserStats.emailsProcessed}
                      icon={<CheckCircle className="h-5 w-5 text-green-500" />}
                    />
                    {/* <EmailClassificationItem
                    type="Non-R&D Emails"
                    count={currentUserStats.nonRdEmails}
                    total={currentUserStats.emailsProcessed}
                    icon={<XCircle className="h-5 w-5 text-red-500" />}
                  /> */}
                  </div>
                </CardContent>
              </Card>

              {/* Recent Activity */}
              <Card className="hidden">
                <CardHeader>
                  <CardTitle>Recent Activity</CardTitle>
                  <CardDescription>
                    Your most recent R&D related emails and documents
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <RecentActivityItem
                      type="Email"
                      subject="Meeting notes on AI model optimization"
                      date="2024-07-29"
                      effort="45 min"
                    />
                    <RecentActivityItem
                      type="Document"
                      subject="Research Proposal - Quantum Computing"
                      date="2024-07-28"
                      effort="90 min"
                    />
                    <RecentActivityItem
                      type="Email"
                      subject="Feedback on prototype design"
                      date="2024-07-27"
                      effort="30 min"
                    />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="report" className="space-y-4">
              <CardHeader>
                <CardTitle>Transactions</CardTitle>
                <CardDescription>
                  {/* View and export R&D activity data */}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ReportSection />
              </CardContent>
            </TabsContent>
          </Tabs>
        </Card>
      </div>
    </div>
  );
}

function MetricCard({
  title,
  value,
  icon,
}: {
  title: string;
  value: string;
  icon: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 ">
        <CardTitle className="font-semibold">
          <span>{title} : </span>
          <span className="font-semibold">{value}</span>
        </CardTitle>
        {icon}
      </CardHeader>
    </Card>
  );
}

function EmailClassificationItem({
  type,
  count,
  total,
  icon,
}: {
  type: string;
  count: number;
  total: number;
  icon: React.ReactNode;
}) {
  const percentage = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-2">
          {icon}
          <span className="font-medium">{type}</span>
        </div>
        <Badge variant="secondary">{count} emails</Badge>
      </div>
      <Progress
        value={percentage}
        className="h-2 [&>[data-slot=progress-indicator]]:bg-blue-500"
      />
      <p className="text-sm text-gray-600 dark:text-gray-300">
        {percentage}% of your processed emails
      </p>
    </div>
  );
}

function RecentActivityItem({
  type,
  subject,
  date,
  effort,
}: {
  type: string;
  subject: string;
  date: string;
  effort: string;
}) {
  return (
    <div className="flex items-center justify-between p-4 border rounded-lg">
      <div className="flex items-center space-x-4">
        {type === "Email" ? (
          <Mail className="h-5 w-5 text-blue-600" />
        ) : (
          <FileText className="h-5 w-5 text-purple-600" />
        )}
        <div>
          <p className="font-medium">{subject}</p>
          <p className="text-sm text-gray-600 dark:text-gray-300">{date}</p>
        </div>
      </div>
      <Badge variant="outline">{effort}</Badge>
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
