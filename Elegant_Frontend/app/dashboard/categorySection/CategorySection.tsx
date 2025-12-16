"use client";

import { useState, useRef, useEffect, use } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardHeader,
  CardContent,
  CardTitle,
  CardDescription,
  CardFooter,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { TabsContent } from "@/components/ui/tabs";
import { Plus, Save, X, Edit } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import axiosClient from "@/app/api/axiosClient";
import { SearchBar } from "@/components/ui/SearchBar";

import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";

// ------------------- Types -------------------
export interface Category {
  category_id: number;
  category_name: string;
  is_active: number;
  keywords: string;
}

interface CreateCategoryDialogProps {
  onClose: () => void;
  onSuccess?: () => void;
}
const getUserContext = () => {
  let userId =
    sessionStorage.getItem("userid") || localStorage.getItem("userid");
  let orgId = sessionStorage.getItem("orgid") || localStorage.getItem("orgid");
  let roleId =
    sessionStorage.getItem("roleid") || localStorage.getItem("roleid");
  return { userId, orgId, roleId };
};

// ------------------- Main Tab -------------------
export default function CategoriesTab() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [isCreateCategoryDialogOpen, setIsCreateCategoryDialogOpen] =
    useState(false);
  const { toast } = useToast();
  const [backupValues, setBackupValues] = useState<Record<number, Category>>(
    {}
  );
  const [categoriesCurrentPage, setCategoriesCurrentPage] = useState(1); //Search Filter Related
  const [categorySearchQuery, setCategorySearchQuery] = useState(""); //Search Filter Realted

  //-------Pagination Logic--------//
  const [totalCount, setTotalCount] = useState(1);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const [limit, setLimit] = useState(5);

  useEffect(() => {
    fetchCategories();
  }, []);

  // ------------------- fetch categories -------------------
  // const fetchCategories = async () => {
  //     try {
  //         const { userId, orgId } = getUserContext(); // get from session/localStorage

  //         const res = await axiosClient.get("/categories/fetch_categories", {
  //             params: {
  //                 user_id: userId,
  //                 org_id: orgId
  //             }
  //         })

  //         setCategories(res.data.categories || [])
  //     } catch {
  //         toast({ title: "Error", description: "Failed to fetch categories", variant: "destructive" })
  //     }
  // }

  // const fetchCategories = async (
  //   query: string = "",
  //   page: number = 1,
  //   limit: number = 10
  // ) => {
  //   try {
  //     const { userId, orgId } = getUserContext();
  //     let res;
  //     if (query.trim() === "") {
  //       res = await axiosClient.get("/categories/fetch_categories", {
  //         params: { user_id: userId, org_id: orgId },
  //       });
  //       setCategories(res.data.categories || []);
  //     } else {
  //       res = await axiosClient.get("/admin/searchCategory", {
  //         //Search Category Endpoint
  //         params: { org_id: orgId, query, page, limit },
  //       });
  //       setCategories(res.data.categories || []); //use 'categories' returned by backend
  //     }
  //   } catch (err) {
  //     toast({
  //       title: "Error",
  //       description: "Failed to fetch categories",
  //       variant: "destructive",
  //     });
  //     console.error("fetchCategories error:", err);
  //   }
  // };

  //--------------Fetch Categories------------//
  const fetchCategories = async (
    query: string = "",
    page: number = 1,
    limit: number = 5
  ) => {
    try {
      const { userId, orgId } = getUserContext();
      let res;

      if (query.trim() === "") {
        res = await axiosClient.get("/categories/fetch_categories", {
          params: { user_id: userId, org_id: orgId, page, limit },
        });
      } else {
        res = await axiosClient.get("/admin/searchCategory", {
          params: { org_id: orgId, query, page, limit },
        });
      }

      setCategories(res.data.categories || []);
      setTotalCount(res.data.totalCount || 0);
      setTotalPages(Math.ceil((res.data.totalCount || 0) / limit));
      setCurrentPage(page);
    } catch (err) {
      toast({
        title: "Error",
        description: "Failed to fetch categories",
        variant: "destructive",
      });
      console.error("fetchCategories error:", err);
    }
  };

  // Start editing a category
  const handleEdit = (cat: Category) => {
    setEditingId(cat.category_id);
    setBackupValues((prev) => ({ ...prev, [cat.category_id]: { ...cat } }));
  };

  // Cancel editing and restore previous value
  const handleCancel = (cat_id: number) => {
    setCategories((prev) =>
      prev.map((c) => (c.category_id === cat_id ? backupValues[cat_id] : c))
    );
    setEditingId(null);
    setBackupValues((prev) => {
      const newBackups = { ...prev };
      delete newBackups[cat_id];
      return newBackups;
    });
  };

  // Handle inline category name change
  const handleChangeCategoryName = (cat_id: number, value: string) => {
    setCategories((prev) =>
      prev.map((c) =>
        c.category_id === cat_id ? { ...c, category_name: value } : c
      )
    );
  };

  // Save updated category to backend
  const handleUpdate = async (cat_id: number) => {
    const cat = categories.find((c) => c.category_id === cat_id);
    if (!cat || !cat.category_name.trim()) {
      toast({
        title: "Validation Error",
        description: "Category name required",
        variant: "destructive",
      });
      return;
    }

    try {
      const response = await axiosClient.post("/categories/update_category", {
        category_id: cat_id,
        category_name: cat.category_name,
        user_id: getUserContext().userId,
      });
      // store backend response
      console.log("Update response:", response);

      toast({
        title: "Success",
        description: response.data?.message || "Category updated",
        variant: "default",
      });
      setEditingId(null);
      fetchCategories();
    } catch (error: any) {
      const msg = error?.response?.data?.message || "Update failed";
      toast({ title: "Error", description: msg, variant: "destructive" });
    }
  };

  //Toggle Updation On Category----------------------//
  const handleToggle = async (cat_id: number, currentStatus: number) => {
    try {
      const newStatus = currentStatus === 1 ? 0 : 1;

      const response = await axiosClient.post(
        "/categories/updateCategoryStatus", //Update Category Status End point
        null,
        {
          params: { cat_id, is_active: newStatus }, // sending as query params
        }
      );

      toast({
        title: "Success",
        description: response.data?.message || "Status updated",
      });

      // Update UI instantly
      setCategories((prev) =>
        prev.map((c) =>
          c.category_id === cat_id ? { ...c, is_active: newStatus } : c
        )
      );
    } catch (error: any) {
      const msg = error?.response?.data?.message || "Toggle failed";
      toast({ title: "Error", description: msg, variant: "destructive" });
    }
  };

  return (
    <TabsContent value="categories-value" className="space-y-6">
      <Card className="gap-3 disable-styles">
        <CardHeader className="flex justify-between items-center  px-0 mb-[0.5rem]">
          <div>
            {/* <CardTitle>Categories</CardTitle> */}
            {/* <CardDescription>Manage R&D effort Categories</CardDescription> */}
          </div>

          {/* /* -------------Search Filter On Category ---------------- */}
          <div className="flex items-center space-x-2">
            <SearchBar
              value={categorySearchQuery}
              onChange={setCategorySearchQuery}
              onSearch={() => fetchCategories(categorySearchQuery)}
              placeholder="Search categories..."
            />

            <Dialog
              open={isCreateCategoryDialogOpen}
              onOpenChange={setIsCreateCategoryDialogOpen}
            >
              <DialogTrigger asChild>
                <Button size="sm" className="h-9 w-9">
                  <Plus className="h-5 w-5 m-auto" />
                </Button>
              </DialogTrigger>
              <CreateCategoryDialog
                onClose={() => setIsCreateCategoryDialogOpen(false)}
                onSuccess={fetchCategories}
              />
            </Dialog>
          </div>
        </CardHeader>
        <CardContent className="grid grid-cols-3 gap-x-4 gap-y-3  px-0">
          {categories.map((cat) => (
            <div
              key={cat.category_id}
              className="flex items-center space-x-4 p-2 rounded-lg border"
            >
              {editingId === cat.category_id ? (
                <>
                  <Input
                    value={cat.category_name}
                    onChange={(e) =>
                      handleChangeCategoryName(cat.category_id, e.target.value)
                    }
                    className="flex-1"
                  />
                  <Button
                    size="sm"
                    onClick={() => handleUpdate(cat.category_id)}
                    className="mr-2"
                  >
                    <Save className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleCancel(cat.category_id)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </>
              ) : (
                <>
                  {/* <span className="flex-1">{cat.category_name}</span> */}
                  <span className="flex-1">
                    <div className="font-medium">{cat.category_name}</div>
                    {cat.keywords && (
                      <div className="text-sm text-gray-500">
                        Keywords: {cat.keywords || "—"}
                      </div>
                    )}
                  </span>

                  {/* -------------------------Toggle Updation ------------------ */}
                  <div
                    onClick={() =>
                      handleToggle(cat.category_id, (cat as any).is_active || 0)
                    }
                    className={`w-13 h-6 flex items-center rounded-full p-1 cursor-pointer transition-all duration-300 ${
                      (cat as any).is_active === 1
                        ? "bg-orange-500"
                        : "bg-gray-200"
                    }`}
                  >
                    <div
                      className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform duration-300 ${
                        (cat as any).is_active === 1
                          ? "translate-x-7"
                          : "translate-x-0"
                      }`}
                    ></div>
                  </div>
                  {/* <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleEdit(cat)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button> */}
                </>
              )}
            </div>
          ))}
        </CardContent>
        <CardFooter className="px-0">
          {/* Pagination Controls On Category With Dropdown*/}
          <Pagination className="d-flex justify-between items-center">
            <PaginationContent className="flex justify-end mt-4">
              <PaginationItem>
                <PaginationPrevious
                  onClick={() => {
                    if (currentPage > 1)
                      fetchCategories(categorySearchQuery, currentPage - 1);
                  }}
                  className={
                    currentPage === 1 ? "pointer-events-none opacity-50" : ""
                  }
                />
              </PaginationItem>
              <span className="px-4 py-2 text-sm">
                Page {currentPage} of {totalPages}
              </span>
              <PaginationItem>
                <PaginationNext
                  onClick={() => {
                    if (currentPage < totalPages)
                      fetchCategories(categorySearchQuery, currentPage + 1);
                  }}
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
                  fetchCategories(categorySearchQuery, 1, newLimit); //search + limit + page reset
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
  );
}

// ------------------- Create Category Dialog -------------------
function CreateCategoryDialog({
  onClose,
  onSuccess,
}: CreateCategoryDialogProps) {
  const { toast } = useToast();
  const categoryRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(false);

  const handleSave = async () => {
    const { userId, orgId } = getUserContext(); // get current user and org
    const category_name = categoryRef.current?.value || "";

    if (!category_name.trim()) {
      toast({
        title: "Validation Error",
        description: "Category name required",
        variant: "destructive",
      });
      return;
    }

    try {
      setLoading(true);
      // send category_name, userId, orgId to backend
      const response = await axiosClient.post("/categories/save_category", {
        category_name,
        user_id: userId,
        org_id: orgId,
      });

      console.log("Create response:", response); // store response in variable
      toast({
        title: "Success",
        description: response.data?.message || "Category created",
        variant: "default",
      });

      if (onSuccess) await onSuccess();
      onClose();
    } catch (error: any) {
      const msg = error?.response?.data?.message || "Create failed";
      toast({ title: "Error", description: msg, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <DialogContent className="sm:max-w-[400px]">
      <DialogHeader>
        <DialogTitle>Create New Category</DialogTitle>
      </DialogHeader>
      <div className="space-y-4 py-2">
        <div className="flex items-center gap-3">
          <Label className="w-32 text-right">Category Name</Label>
          <Input
            ref={categoryRef}
            placeholder="Enter category name"
            className="flex-1"
          />
        </div>
      </div>
      <DialogFooter>
        <Button onClick={handleSave}>
          {loading ? "Creating..." : "Create Category"}
        </Button>
      </DialogFooter>
    </DialogContent>
  );
}
