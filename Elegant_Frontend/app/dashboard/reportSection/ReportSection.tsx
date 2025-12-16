"use client";

import { useState, useEffect } from "react";
import axiosClient from "@/app/api/axiosClient";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import ReportTable from "@/components/ui/reacttable";
import Image from "next/image";
import {
  MailOpen,
  CalendarDays,
  FileSpreadsheet,
  FileText,
} from "lucide-react";
import { ReportRow } from "@/types/reportType";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Calendar,
  Download,
  Filter,
  Save,
  Edit,
  X,
  Eye,
  RotateCcw,
  Loader2,
  ChevronDown,
} from "lucide-react";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { useToast } from "@/hooks/use-toast";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useSearchParams, useRouter } from "next/navigation";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { updateMailRowService } from "../user/reportService"

// interface ReportRow {
//   id: string;
//   entityType: string;
//   date: string;
//   sender: string;
//   recipients: string;
//   wordCount: number;
//   attachmentWordCount: number;
//   efforts: number | string;
//   keywordCount: number;
//   ComputedEfforts: number;
//   keywordEfforts: number;
//   selected: boolean;
//   mail_dtl_id: string;
//   meetingDuration?: number;
//   isEditing?: boolean;
//   cal_id: string;
// }

interface PreviewData {
  mail_dtl_id: string;
  user_id: string;
  subject: string;
  body: string;
  attachments: string[];
  cal_id: string;
}

// Format date in local timezone as yyyy-mm-dd
const formatDate = (d: Date) => d.toLocaleDateString("en-CA");

// const formatDateTime = (dateTimeString: string) => {
//   try {
//     const date = new Date(dateTimeString);
//     const day = String(date.getDate()).padStart(2, "0");
//     const month = String(date.getMonth() + 1).padStart(2, "0");
//     const year = date.getFullYear();
//     return `${day}-${month}-${year}`;
//   } catch {
//     return dateTimeString;
//   }
// };

export default function ReportSection() {
  const { toast } = useToast();
  const today = new Date();
  const firstDayPrevMonth = new Date(
    today.getFullYear(),
    today.getMonth() - 1,
    1
  );

  const [reportData, setReportData] = useState<ReportRow[]>([]);
  const [dateRange, setDateRange] = useState({
    from: formatDate(firstDayPrevMonth),
    to: formatDate(today),
  });
  const [loading, setLoading] = useState(false);
  const [originalData, setOriginalData] = useState<ReportRow[]>([]);

  // Separate meeting data state
  const [meetingData, setMeetingData] = useState<ReportRow[]>([]);
  const [originalMeetingData, setOriginalMeetingData] = useState<ReportRow[]>(
    []
  );

  // Preview state
  const [isPreviewDialogOpen, setIsPreviewDialogOpen] = useState(false);
  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  // Individual row loading states
  const [updatingRows, setUpdatingRows] = useState<Set<string>>(new Set());
  const [previewingRows, setPreviewingRows] = useState<Set<string>>(new Set());

  // Entity type filter state
  const [entities, setEntities] = useState<
    { entity_id: number; entity_name: string }[]
  >([]);
  const [selectedEntityType, setSelectedEntityType] = useState<
    "" | "mail" | "meeting"
  >("mail");

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const rowsPerPage = 5;

  // Calculate total pages and paginated rows based on current entity type
  const getCurrentData = () => {
    if (selectedEntityType === "meeting") {
      return meetingData;
    }
    return reportData;
  };

  const currentData = getCurrentData();
  const totalPages = Math.ceil(currentData.length / rowsPerPage);
  const paginatedRows = currentData.slice(
    (currentPage - 1) * rowsPerPage,
    currentPage * rowsPerPage
  );

  const [userId, setUserId] = useState<number | null>(null);
  type Folder = {
    id: string;
    name: string;
  };

  const [allFolders, setAllFolders] = useState<Folder[]>([]);
  const [selectedFolders, setSelectedFolders] = useState<Folder[]>([]);

  // Keywords
  const [allKeywords, setAllKeywords] = useState<
    { id: string; name: string }[]
  >([]);
  const [selectedKeyword, setSelectedKeyword] = useState<string | null>(null);

  // Categories
  const [allCategory, setAllCategory] = useState<
    { id: string; name: string }[]
  >([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  // Users
  const [allUsers, setAllUsers] = useState<{ id: string; name: string }[]>([]);
  const [selectedUser, setSelectedUser] = useState<string | null>(null);

  // File Types
  const [allFileTypes, setAllFileTypes] = useState<
    { id: string; name: string }[]
  >([]);
  const [selectedFileType, setSelectedFileType] = useState<string | null>(null);

  const [items, setItems] = useState<Folder[]>([]);

  const user_id =
    sessionStorage.getItem("userid") || localStorage.getItem("userid");

  const searchParams = useSearchParams();

  useEffect(() => {
    const loadInitial = async () => {
      setLoading(true);
      fetchKeywordsList();
      fetchCategoryList();
      fetchUsersList();
      fetchFileTypeList();
      try {
        setCurrentPage(1);
        const tokenFromQuery = searchParams.get("mail_token");
        if (tokenFromQuery) {
          localStorage.setItem("mail_token", tokenFromQuery);
          console.log("Mail token saved:", tokenFromQuery);
          fetchFolders();
        }
      } catch (err) {
        console.error("Error loading data:", err);
        setReportData([]);
      } finally {
        setLoading(false);
      }
    };

    loadInitial();
  }, []); // run only once on mount

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

  //-----------------------Keywords List-----------------------
  const fetchKeywordsList = async () => {
    const { orgId } = getUserContext();
    if (!orgId) return console.error("Organization ID is required");

    try {
      const response = await axiosClient.post("/reports/fetch_keywords_list", {
        org_id: orgId,
      });

      const keywordsArray = Array.isArray(response.data) ? response.data : [];
      setAllKeywords(keywordsArray);
    } catch (err) {
      console.error(`Error fetching keywords:`, err);
      setAllKeywords([]);
    }
  };

  //-----------------------Category List-----------------------
  const fetchCategoryList = async () => {
    const { orgId } = getUserContext();
    if (!orgId) return console.error("Organization ID is required");

    try {
      const response = await axiosClient.post("/reports/fetch_category_list", {
        org_id: orgId,
      });

      const categoryArray = Array.isArray(response.data) ? response.data : [];
      setAllCategory(categoryArray);
    } catch (err) {
      console.error(`Error fetching categories:`, err);
      setAllCategory([]);
    }
  };

  //-----------------------Users List-----------------------
  const fetchUsersList = async () => {
    const { orgId, roleId } = getUserContext();
    if (!orgId) return console.error("Organization ID is required");

    try {
      const response = await axiosClient.post("/reports/fetch_users_list", {
        org_id: orgId,
	role_id: roleId 
      });

      const usersArray = Array.isArray(response.data) ? response.data : [];
      setAllUsers(usersArray);
    } catch (err) {
      console.error(`Error fetching users:`, err);
      setAllUsers([]);
    }
  };

  //-----------------------File Types (GET request)-----------------------
  const fetchFileTypeList = async () => {
    try {
      const response = await axiosClient.get("/reports/fetch_fileType_list");

      const fileTypesArray = Array.isArray(response.data) ? response.data : [];
      setAllFileTypes(fileTypesArray);
    } catch (err) {
      console.error(`Error fetching file types:`, err);
      setAllFileTypes([]);
    }
  };

  // ---------------------- UTILITY METHODS ----------------------
  const getUserContext = () => {
    let userId =
      sessionStorage.getItem("userid") || localStorage.getItem("userid");
    let orgId =
      sessionStorage.getItem("orgid") || localStorage.getItem("orgid");
    let roleId =
      sessionStorage.getItem("roleid") || localStorage.getItem("roleid");
    return { userId, orgId, roleId };
  };

  // ---------------------- ENTITY METHODS ----------------------
  const fetchEntities = async () => {
    try {
      const response = await axiosClient.get("reports/fetch_entity_types");
      if (response.data?.success) {
        setEntities(response.data.data || []);
      } else {
        toast({
          title: "Error",
          description: response.data?.message || "Failed to fetch entities",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error fetching entity types:", error);
      toast({
        title: "Error",
        description: "Failed to fetch entities",
        variant: "destructive",
      });
    }
  };

  // ---------------------- MAIL METHODS ----------------------
  const fetchMailData = async (range = dateRange): Promise<ReportRow[]> => {
    try {
      const { userId, orgId, roleId } = getUserContext();

      const payload: any = {
        from_date: range.from,
        to_date: range.to,
        user_id: userId,
        org_id: orgId,
        role_id: roleId,
        keyword: selectedKeyword ? String(selectedKeyword) : "",
        category: selectedCategory ? String(selectedCategory) : "",
        user: selectedUser ? String(selectedUser) : "",
        file_type: selectedFileType ? String(selectedFileType) : "",
      };

      const response = await axiosClient.post(
        "/reports/fetch_report_data_filtered",
        payload
      );

      const mails: ReportRow[] = response.data.data.map((item: any) => ({
        id: String(item.report_id),
        entityType: "mail",
        date: item.created_date ?? "",
        sender: item.mail_from ?? "",
        recipients: item.mail_to ?? "",
        wordCount: Number(item.word_count),
        attachmentWordCount: Number(item.attachment_word_count) || 0,
        efforts: Number(item.planned_effort_time) || 0,
        keywordCount: Number(item.repeated_keyword_count) || 0,
        cat_name: String(item.cat_name ?? ""),
        ComputedEfforts: Number(item.actual_effort_time) || 0,
        keywordEfforts: 0,
        selected: false,
        mail_dtl_id: String(item.mail_dtl_id ?? ""),
        isEditing: false,
      }));

      return mails;
    } catch (error) {
      console.error("Error fetching mail data:", error);
      return [];
    }
  };

  const editMailRow = (id: string) => {
    setReportData((prev) =>
      prev.map((item) => {
        if (item.id === id) {
          return { ...item, isEditing: true };
        }
        return { ...item, isEditing: false }; // Ensure other rows are not in editing mode
      })
    );
    // Store original data for this specific row
    const rowToEdit = reportData.find((item) => item.id === id);
    if (rowToEdit) {
      setOriginalData([rowToEdit]);
    }
  };

  // const updateMailRow = async (
  //   id: string,
  //   org_id: string,
  //   isOnLoad: boolean = false
  // ) => {
  //   if (!isOnLoad) {
  //     setUpdatingRows((prev) => new Set(prev).add(id));
  //   }

  //   try {
  //     let requestData: any = {};

  //     if (isOnLoad) {
  //       // On load → generate reports for all mails of this user
  //       requestData = {
  //         user_id: id,
  //         org_id: org_id,
  //       };
  //     } else {
  //       // On update → update specific report row
  //       const currentRow = reportData.find((item) => item.id === id);
  //       if (!currentRow) return;

  //       requestData = {
  //         user_id: getUserContext().userId,
  //         report_id: currentRow.id,
  //         mail_dtl_id: currentRow.mail_dtl_id,
  //         efforts: currentRow.efforts,
  //         keyword_efforts: currentRow.keywordEfforts,
  //         org_id: getUserContext().orgId,
  //       };
  //     }

  //     const response = await axiosClient.post("/reports/mail", requestData);

  //     // If updating a single row → stop editing mode and show success toast
  //     if (!isOnLoad) {
  //       setReportData((prev) =>
  //         prev.map((item) =>
  //           item.id === id ? { ...item, isEditing: false } : item
  //         )
  //       );

  //       toast({
  //         title: "Success",
  //         description: "Mail row updated successfully",
  //         variant: "default",
  //       });

  //       // Refresh the data only if we're currently viewing mail data
  //       if (selectedEntityType === "mail" || selectedEntityType === "") {
  //         const refreshedData = await fetchMailData();
  //         setReportData(refreshedData);
  //       }
  //     }
  //   } catch (error) {
  //     console.error("Error updating mail effort:", error);

  //     // Show error toast for single row updates
  //     if (!isOnLoad) {
  //       toast({
  //         title: "Error",
  //         description: "Failed to update mail row. Please try again.",
  //         variant: "destructive",
  //       });
  //     }
  //   } finally {
  //     if (!isOnLoad) {
  //       setUpdatingRows((prev) => {
  //         const newSet = new Set(prev);
  //         newSet.delete(id);
  //         return newSet;
  //       });
  //     }
  //   }
  // };
  const updateMailRow = async (
    id: string,
    org_id: string,
    isOnLoad: boolean = false
  ) => {
    if (!isOnLoad) setUpdatingRows((prev) => new Set(prev).add(id));

    try {
      if (isOnLoad) {
        await updateMailRowService(id, org_id, true);
      } else {
        const currentRow = reportData.find((item) => item.id === id);
        if (!currentRow) return;

        await updateMailRowService(id, org_id, false, {
          report_id: currentRow.id,
          mail_dtl_id: currentRow.mail_dtl_id,
          efforts: currentRow.efforts,
          keywordEfforts: currentRow.keywordEfforts,
        });

        toast({
          title: "Success",
          description: "Mail row updated successfully",
          variant: "default",
        });

        const refreshedData = await fetchMailData();
        setReportData(refreshedData);
      }
    } catch (error) {
      console.error("Error updating mail effort:", error);
      if (!isOnLoad) {
        toast({
          title: "Error",
          description: "Failed to update mail row. Please try again.",
          variant: "destructive",
        });
      }
    } finally {
      if (!isOnLoad) {
        setUpdatingRows((prev) => {
          const newSet = new Set(prev);
          newSet.delete(id);
          return newSet;
        });
      }
    }
  };

  const cancelMailRow = (id: string) => {
    // Revert the specific row back to original values
    const originalRow = originalData.find((item) => item.id === id);
    if (originalRow) {
      setReportData((prev) =>
        prev.map((item) => {
          if (item.id === id) {
            return { ...originalRow, isEditing: false };
          }
          return item;
        })
      );
    } else {
      // If no original data, just stop editing
      setReportData((prev) =>
        prev.map((item) => {
          if (item.id === id) {
            return { ...item, isEditing: false };
          }
          return item;
        })
      );
    }
  };

  const handleMailEffortChange = (
    id: string,
    field: "efforts" | "keywordEfforts",
    value: number
  ) => {
    setReportData((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, [field]: isNaN(value) ? 0 : value } : item
      )
    );
  };

  const handleMailSelectRow = (
    id: string,
    checked: boolean | "indeterminate"
  ) => {
    const isChecked = checked === true;
    setReportData((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, selected: isChecked } : item
      )
    );
  };

  const handleMailSelectAll = (checked: boolean, pageRows: ReportRow[]) => {
    const isChecked = checked === true;
    setReportData((prev) =>
      prev.map((item) =>
        pageRows.find((row) => row.id === item.id)
          ? { ...item, selected: isChecked }
          : item
      )
    );
  };

  // ---------------------- MEETING METHODS ----------------------
  const fetchMeetingData = async (range = dateRange): Promise<ReportRow[]> => {
    try {
      const { userId, orgId, roleId } = getUserContext();

      const response = await axiosClient.post("/reports/fetch_meeting_data", {
        from_date: range.from,
        to_date: range.to,
        user_id: userId,
        org_id: orgId,
        role_id: roleId,
        user: selectedUser ? String(selectedUser) : "",
      });

      const rawData = response?.data?.data ?? [];

      const meetings: ReportRow[] = rawData.map((item: any, index: number) => {
        const duration = Number(item.meeting_duration) || 0;
        const meetingId = String(
          item.meeting_report_id || `meeting-${index}-${Date.now()}`
        );

        // Preserve existing selection state if the meeting already exists
        const existingMeeting = meetingData.find(
          (existing) => existing.id === meetingId
        );

        return {
          id: meetingId,
          entityType: "meeting",
          date: item.event_start_datetime || "",
          sender: item.organiser || "",
          recipients: item.attendees || "",
          selected: existingMeeting ? existingMeeting.selected : false,
          cal_id: String(item.cal_id) || "0",
          meetingDuration: duration,
          isEditing: existingMeeting ? existingMeeting.isEditing : false,
          attachmentWordCount: 0,
          efforts: item.efforts_time || 0,
        };
      });

      return meetings;
    } catch (error) {
      console.error("Error fetching meeting data:", error);
      return [];
    }
  };

  const editMeetingRow = (id: string) => {
    setMeetingData((prev) =>
      prev.map((item) => {
        if (item.id === id) {
          return { ...item, isEditing: true };
        }
        return { ...item, isEditing: false }; // Ensure other rows are not in editing mode
      })
    );
    // Store original data for this specific meeting row
    const rowToEdit = meetingData.find((item) => item.id === id);
    if (rowToEdit) {
      setOriginalMeetingData([rowToEdit]);
    }
  };

  const updateMeetingRow = async (id: string) => {
    setUpdatingRows((prev) => new Set(prev).add(id));

    try {
      const currentRow = meetingData.find((item) => item.id === id);
      if (!currentRow) return;

      const requestData = {
        meeting_report_id: currentRow.id,
        efforts: currentRow.efforts,
      };

      const response = await axiosClient.post(
        "/reports/update_meeting",
        requestData
      );

      // Stop editing mode and show success toast
      setMeetingData((prev) =>
        prev.map((item) =>
          item.id === id ? { ...item, isEditing: false } : item
        )
      );

      toast({
        title: "Success",
        description: "Meeting row updated successfully",
        variant: "default",
        duration: 3000,
      });

      // Refresh the data only if we're currently viewing meeting data
      if (selectedEntityType === "meeting") {
        const refreshedData = await fetchMeetingData();
        // Preserve the editing state (should be false) and selection state
        setMeetingData(
          refreshedData.map((newRow) => {
            const existingRow = meetingData.find(
              (existing) => existing.id === newRow.id
            );
            return {
              ...newRow,
              isEditing: false, // Ensure editing is false after refresh
              selected: existingRow ? existingRow.selected : newRow.selected,
            };
          })
        );
      }
    } catch (error) {
      console.error("Error updating meeting effort:", error);

      toast({
        title: "Error",
        description: "Failed to update meeting row. Please try again.",
        variant: "destructive",
      });
    } finally {
      setUpdatingRows((prev) => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    }
  };

  const cancelMeetingRow = (id: string) => {
    // Revert the specific meeting row back to original values
    const originalRow = originalMeetingData.find((item) => item.id === id);
    if (originalRow) {
      setMeetingData((prev) =>
        prev.map((item) => {
          if (item.id === id) {
            return { ...originalRow, isEditing: false };
          }
          return item;
        })
      );
    } else {
      // If no original data, just stop editing
      setMeetingData((prev) =>
        prev.map((item) => {
          if (item.id === id) {
            return { ...item, isEditing: false };
          }
          return item;
        })
      );
    }
  };

  const handleMeetingEffortChange = (
    id: string,
    field: "efforts" | "keywordEfforts",
    value: number
  ) => {
    setMeetingData((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, [field]: isNaN(value) ? 0 : value } : item
      )
    );
  };

  const handleMeetingSelectRow = (id: string, checked: boolean) => {
    setMeetingData((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, selected: checked } : item
      )
    );
  };

  const handleMeetingSelectAll = (checked: boolean, pageRows: ReportRow[]) => {
    setMeetingData((prev) =>
      prev.map((item) =>
        pageRows.find((row) => row.id === item.id)
          ? { ...item, selected: checked }
          : item
      )
    );
  };
  // ---------------------- PREVIEW METHODS ----------------------
  const openMailPreview = async (id: string) => {
    setIsPreviewDialogOpen(true);
    setPreviewLoading(true);
    setPreviewingRows((prev) => new Set(prev).add(id));
    try {
      const response = await axiosClient.post(
        "/reports/fetch_mail_details_by_id",
        {
          mail_dtl_id: id,
        }
      );
      setPreviewData({
        ...response.data,
        mail_dtl_id: id,
        user_id:
          sessionStorage.getItem("userid") ||
          localStorage.getItem("userid") ||
          "",
      });
    } catch (error) {
      console.error("Error fetching mail preview data:", error);
      toast({
        title: "Error",
        description: "Failed to fetch mail preview",
        variant: "destructive",
      });
    } finally {
      setPreviewLoading(false);
      setPreviewingRows((prev) => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    }
  };

  const openMeetingPreview = async (cal_id: string) => {
    setIsPreviewDialogOpen(true);
    setPreviewLoading(true);
    setPreviewingRows((prev) => new Set(prev).add(cal_id));
    try {
      // Fetch meeting details - you might need to adjust this endpoint
      const response = await axiosClient.post(
        "/reports/fetch_meeting_details_by_id",
        {
          cal_id: cal_id,
        }
      );
      setPreviewData({
        ...response.data,
        cal_id: cal_id,
        user_id:
          sessionStorage.getItem("userid") ||
          localStorage.getItem("userid") ||
          "",
      });
    } catch (error) {
      console.error("Error fetching meeting preview data:", error);
      toast({
        title: "Error",
        description: "Failed to fetch meeting preview",
        variant: "destructive",
      });
    } finally {
      setPreviewLoading(false);
      setPreviewingRows((prev) => {
        const newSet = new Set(prev);
        newSet.delete(cal_id);
        return newSet;
      });
    }
  };

  const closePreview = () => {
    setIsPreviewDialogOpen(false);
    setPreviewData(null);
  };

  // ---------------------- ATTACHMENT METHODS ----------------------
  const handlePreviewAttachment = async (
    mail_dtl_id: string,
    user_id: string,
    attachmentName: string
  ) => {
    try {
      const response = await axiosClient.post(
        "/reports/attachments/preview",
        {
          mail_dtl_id,
          user_id,
          attachment_name: attachmentName,
        },
        {
          responseType: "blob",
        }
      );

      if (!response || !response.data) {
        throw new Error("Failed to fetch attachment");
      }

      const blob = response.data;
      const url = window.URL.createObjectURL(blob);
      window.open(url, "_blank");
    } catch (error) {
      console.error("Error previewing attachment:", error);
      toast({
        title: "Error",
        description: "Failed to preview attachment",
        variant: "destructive",
      });
    }
  };

  // ---------------------- FILTER AND DOWNLOAD METHODS ----------------------
  const applyFilter = async () => {
    setLoading(true);
    try {
      if (selectedEntityType === "meeting") {
        const meetings = await fetchMeetingData();
        setMeetingData(meetings);
        setReportData([]);
      } else if (selectedEntityType === "mail") {
        const mails = await fetchMailData();
        setReportData(mails);
        setMeetingData([]);
      } else {
        // Default: load mail data
        const mails = await fetchMailData();
        setReportData(mails);
        setMeetingData([]);
      }

      setCurrentPage(1);
    } catch (err) {
      console.error("Error loading data:", err);
      setReportData([]);
      setMeetingData([]);
    } finally {
      setLoading(false);
    }
  };

  const clearFilters = async () => {
    const newDateRange = {
      from: formatDate(firstDayPrevMonth),
      to: formatDate(today),
    };
    setDateRange(newDateRange);
    // setSelectedEntityType("");
    setItems([]);
    setCurrentPage(1);
    setSelectedKeyword("");
    setSelectedCategory("");
    setSelectedUser("");
    setSelectedFileType("");

    setLoading(true);
    try {
      const mails = await fetchMailData(newDateRange);
      setReportData(mails);
      setMeetingData([]);
    } catch (err) {
      console.error("Error clearing filters:", err);
      setReportData([]);
      setMeetingData([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (format: "excel" | "pdf") => {
    const selectedRows = currentData.filter((row) => row.selected);
    if (selectedRows.length < 1) {
      toast({
        title: "Error",
        description: "Please select at least one row to download",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      // Use different endpoints for different entity types
      let endpoint = "";
      if (selectedEntityType === "meeting") {
        endpoint =
          format === "pdf" ? "/reports/meeting/pdf" : "/reports/meeting/csv";
      } else {
        endpoint = format === "pdf" ? "/reports/mail/pdf" : "/reports/mail/csv";
      }

      // For meetings, we might need a different endpoint or parameter
      const requestData =
        selectedEntityType === "meeting"
          ? { meeting_report_ids: selectedRows.map((row) => Number(row.id)) }
          : { report_ids: selectedRows.map((row) => Number(row.id)) };

      const response = await axiosClient.post(endpoint, requestData, {
        responseType: "blob",
      });

      const blob = new Blob([response.data], {
        type:
          format === "excel" ? "text/csv;charset=utf-8;" : "application/pdf",
      });

      const filename = `${selectedEntityType || "mail"}_report_${dateRange.from
        }_to_${dateRange.to}.${format === "excel" ? "csv" : "pdf"}`;

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error(`Error downloading ${format}:`, error);
      toast({
        title: "Error",
        description: `Failed to download ${format}`,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  // ---------------------- EFFECTS ----------------------
  useEffect(() => {
    const loadInitial = async () => {
      setLoading(true);
      try {
        // Always fetch entities first
        await fetchEntities();

        let data = [];
        if (selectedEntityType === "meeting") {
          data = await fetchMeetingData();
          setMeetingData(data);
          setReportData([]);
          setSelectedKeyword("");
          setSelectedCategory("");
          setSelectedUser("");
          setSelectedFileType("");
        } else if (selectedEntityType === "mail") {
          data = await fetchMailData();
          setReportData(data);
          setMeetingData([]);
          setSelectedKeyword("");
          setSelectedCategory("");
          setSelectedUser("");
          setSelectedFileType("");
        } else {
          // Default: load mail data
          data = await fetchMailData();
          setReportData(data);
          setMeetingData([]);
        }

        setCurrentPage(1);
      } catch (err) {
        console.error("Error loading data:", err);
        setReportData([]);
        setMeetingData([]);
        toast({
          title: "Error",
          description: "Failed to load data. Please try again.",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    loadInitial();
  }, [selectedEntityType]);

  // Call updateMailRow on component load with user_id - only once
  useEffect(() => {
    const { userId, orgId } = getUserContext();
    if (userId && orgId) {
      updateMailRow(userId, orgId, true);
    }
  }, []); // Empty dependency array to run only once

  useEffect(() => {
    applyFilter();
  }, [selectedKeyword, selectedCategory, selectedUser, selectedFileType]);

  const { roleId } = getUserContext();
  // ---------------------- RENDER ----------------------
  return (
    <div className="space-y-2 relative">
      {loading && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/30 backdrop-blur-[2px] z-50 mb-0">
          <div className="flex flex-col items-center space-y-4 text-white">
            <Loader2 className="h-10 w-10 animate-spin" />
            <p className="text-xl font-semibold">Loading...</p>
          </div>
        </div>
      )}
      {/* -----------------------Date Range Filter----------------------- */}
      <div className="flex items-center space-x-4 p-2 bg-gray-50 dark:bg-gray-800 rounded-lg">
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
            className=""
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
            className=""
            max={new Date().toISOString().split("T")[0]}
            min={dateRange.from}
            style={{
              color: "var(--color-foreground, var(--foreground))",
              WebkitTextFillColor: "var(--color-foreground, var(--foreground))",
            }}
          />
        </div>
        <div className="flex gap-2  h-11 hidden">
          <DropdownMenu>
            <DropdownMenuTrigger className="flex items-center h-11 overflow-auto  justify-between px-4  border rounded bg-white dark:bg-gray-800 w-60">
              <span className="h-10 py-2">
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

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                onClick={applyFilter}
                disabled={loading}
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
                variant="outline"
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
        {/*---------------Keywords Filter Dropdown---------------*/}
        {selectedEntityType === "mail" && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="relative flex items-center space-x-2">
                  <Select
                    value={selectedKeyword || "none"}
                    onValueChange={(value) => {
                      setSelectedKeyword(value === "none" ? null : value);
                    }}
                  >
                    <SelectTrigger className="w-30">
                      <SelectValue placeholder="Select Keyword" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none" className="text-gray-400">
                        Select Keyword
                      </SelectItem>
                      {allKeywords.map((keyword) => (
                        <SelectItem key={keyword.id} value={keyword.name}>
                          {keyword.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </TooltipTrigger>
              <TooltipContent side="top" align="center">
                Keyword Filter
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}

        {/*---------------Category Filter Dropdown---------------*/}
        {selectedEntityType === "mail" && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="relative flex items-center space-x-2">
                  <Select
                    value={selectedCategory || "none"}
                    onValueChange={(value) => {
                      setSelectedCategory(value === "none" ? null : value);
                    }}
                  >
                    <SelectTrigger className="w-30">
                      <SelectValue placeholder="Select Category" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none" className="text-gray-400">
                        Select Category
                      </SelectItem>
                      {allCategory.map((cat) => (
                        <SelectItem key={cat.id} value={cat.id}>
                          {cat.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </TooltipTrigger>
              <TooltipContent side="top" align="center">
                Category Filter
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}

        {/*---------------User Filter Dropdown---------------*/}
        {Number(roleId) === 1 && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="relative flex items-center space-x-2">
                  <Select
                    value={selectedUser || "none"}
                    onValueChange={(value) => {
                      setSelectedUser(value === "none" ? null : value);
                    }}
                  >
                    <SelectTrigger className="w-30">
                      <SelectValue placeholder="Select User" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none" className="text-gray-400">
                        Select User
                      </SelectItem>
                      {allUsers.map((user) => (
                        <SelectItem key={user.id} value={user.id}>
                          {user.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </TooltipTrigger>
              <TooltipContent side="top" align="center">
                User Filter
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}

        {/*---------------File Type Filter Dropdown---------------*/}
        {selectedEntityType === "mail" && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="relative group flex items-center space-x-2">
                  <Select
                    value={selectedFileType || "none"}
                    onValueChange={(value) => {
                      setSelectedFileType(value === "none" ? null : value);
                    }}
                  >
                    <SelectTrigger className="w-30">
                      <SelectValue placeholder="Select File Type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none" className="text-gray-400">
                        Select File Type
                      </SelectItem>
                      {allFileTypes.map((file) => (
                        <SelectItem key={file.id} value={file.id}>
                          {file.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </TooltipTrigger>
              <TooltipContent side="top" align="center">
                File Type Filter
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}

        {/* Entity Type Dropdown at end */}
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="relative flex items-center space-x-2 ml-auto">
                <Select
                  value={selectedEntityType}
                  onValueChange={(value) =>
                    setSelectedEntityType(value as "" | "mail" | "meeting")
                  }
                >
                  <SelectTrigger className="w-30">
                    <SelectValue placeholder="Select entity type" />
                  </SelectTrigger>
                  <SelectContent>
                    {entities.map((entity) => (
                      <SelectItem
                        key={entity.entity_id}
                        value={entity.entity_name.toLowerCase()}
                      >
                        {entity.entity_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </TooltipTrigger>
            <TooltipContent side="top" align="center">
              Entity Type
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      {/* -----------------------Download Buttons----------------------- */}
      <div className="flex justify-between items-center">
        {/* <div className="flex items-center space-x-2"> */}
        {/* <Checkbox
            id="select-all"
            checked={
              paginatedRows.length > 0 &&
              paginatedRows.every((row) => row.selected)
            }
            onCheckedChange={
              selectedEntityType === "meeting"
                ? handleMeetingSelectAll
                : handleMailSelectAll
            }
          />
          <Label htmlFor="select-all" className="text-sm font-medium">
            Select Page ({currentData.filter((row) => row.selected).length}{" "}
            total selected)
          </Label> */}
        {/* </div> */}
      </div>

      {/* -----------------------Report Table----------------------- */}
      <h2 className="caption-top text-right font-medium text-md mb-2 flex justify-end gap-x-2 justify-center">
        <span className=" ">Efforts in Minutes</span>
        <span>
          <div className="flex space-x-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    onClick={() => handleDownload("excel")}
                    size="sm"
                    disabled={loading}
                  >
                    {loading ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <FileSpreadsheet className="h-4 w-4" />
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="top" align="center">
                  Download Excel
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    onClick={() => handleDownload("pdf")}
                    size="sm"
                    variant="outline"
                    disabled={loading}
                  >
                    {loading ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <FileText className="h-4 w-4" />
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="top" align="center">
                  Download Pdf
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </span>
      </h2>
      <div className="border rounded-lg overflow-hidden">
        <div className="w-full overflow-x-auto">
          {selectedEntityType === "mail" || selectedEntityType === "" ? (
            // -------------------- MAIL TABLE --------------------
            <>
              {loading ? (
                <div className="flex items-center justify-center p-8">
                  <Loader2 className="h-6 w-6 animate-spin mr-2" />
                  <p className="text-gray-500">Loading mail data...</p>
                </div>
              ) : reportData.length === 0 ? (
                <p className="text-center text-gray-500 p-2">
                  No Mail Report data available
                </p>
              ) : (
                <>
                  <ReportTable
                    data={reportData}
                    selectedEntityType="mail"
                    onEditRow={editMailRow}
                    onUpdateRow={(id) =>
                      updateMailRow(
                        id,
                        sessionStorage.getItem("orgid") || "",
                        false
                      )
                    }
                    onCancelRow={cancelMailRow}
                    onPreviewRow={openMailPreview}
                    onEffortChange={(id, value) =>
                      handleMailEffortChange(id, "efforts", value)
                    }
                    onSelectAll={handleMailSelectAll}
                    onSelectRow={handleMailSelectRow}
                  />
                </>
              )}
            </>
          ) : selectedEntityType === "meeting" ? (
            // -------------------- MEETING TABLE --------------------
            <>
              {loading ? (
                <div className="flex items-center justify-center p-8">
                  <Loader2 className="h-6 w-6 animate-spin mr-2" />
                  <p className="text-gray-500">Loading meeting data...</p>
                </div>
              ) : meetingData.length === 0 ? (
                <p className="text-center text-gray-500 p-4">
                  No Meeting Report data available
                </p>
              ) : (
                <>
                  <ReportTable
                    data={meetingData}
                    selectedEntityType="meeting"
                    onEditRow={editMeetingRow}
                    onUpdateRow={updateMeetingRow}
                    onCancelRow={cancelMeetingRow}
                    onPreviewRow={openMeetingPreview}
                    onEffortChange={(id, value) =>
                      handleMeetingEffortChange(id, "efforts", value)
                    }
                    onSelectAll={handleMeetingSelectAll}
                    onSelectRow={handleMeetingSelectRow}
                  />
                </>
              )}
            </>
          ) : null}
        </div>
      </div>

      {/* -----------------------Preview Dialog----------------------- */}
      <Dialog open={isPreviewDialogOpen} onOpenChange={closePreview}>
        <DialogContent className="w-[90vw] h-[80vh] max-w-none overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Preview</DialogTitle>
          </DialogHeader>

          {previewLoading ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="h-6 w-6 animate-spin mr-2" />
              <p className="text-gray-500">Loading preview...</p>
            </div>
          ) : previewData ? (
            <div className="space-y-4 break-words">
              {/* Subject */}
              <div>
                <Label className="text-sm font-medium text-foreground">
                  Subject
                </Label>
                <div className="p-2 border rounded bg-gray-50 dark:bg-gray-800 break-words whitespace-pre-wrap max-w-[440px]">
                  {previewData.subject && previewData.subject.trim() !== "" ? (
                    previewData.subject
                  ) : (
                    <span className="text-gray-500">No subject found</span>
                  )}
                </div>
              </div>

              {/* Body */}
              <div>
                <Label className="text-sm font-medium text-foreground">
                  Body
                </Label>
                <div className="p-2 border rounded bg-gray-50 dark:bg-gray-800 break-words whitespace-pre-wrap max-w-[440px]">
                  {previewData.body && previewData.body.trim() !== "" ? (
                    previewData.body
                  ) : (
                    <span className="text-gray-500">No body found</span>
                  )}
                </div>
              </div>

              {/* Attachments */}
              <div>
                <Label className="text-sm font-medium text-foreground">
                  Attachments
                </Label>
                {previewData.attachments &&
                  previewData.attachments.length > 0 ? (
                  <ul className="list-disc ml-6 space-y-1 max-w-[440px] break-words">
                    {previewData.attachments.map((att, idx) => (
                      <li key={idx} className="break-words">
                        <button
                          onClick={() =>
                            handlePreviewAttachment(
                              previewData.mail_dtl_id,
                              previewData.user_id,
                              previewData.attachments[idx]
                            )
                          }
                          className="text-blue-600 hover:underline break-all"
                        >
                          {att}
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-500">No attachments</p>
                )}
              </div>
            </div>
          ) : (
            <p className="text-gray-500">No preview data</p>
          )}

          <DialogFooter className="mt-auto flex justify-end">
            <Button variant="outline" onClick={closePreview}>
              Cancel
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* -----------------------Pagination----------------------- */}
      {currentData.length > rowsPerPage && (
        <Pagination className="hidden">
          <PaginationContent className="w-full flex justify-end mt-4">
            <PaginationItem>
              <PaginationPrevious
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
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
              />
            </PaginationItem>
          </PaginationContent>
        </Pagination>
      )}
    </div>
  );
}
