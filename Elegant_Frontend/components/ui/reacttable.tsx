"use client";

import React from "react";
import Image from "next/image";
import { MailOpen, CalendarDays, Save, X, Edit, Eye } from "lucide-react";
import {
  useReactTable,
  getCoreRowModel,
  getPaginationRowModel,
  ColumnDef,
  flexRender,
} from "@tanstack/react-table";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ReportRow } from "@/types/reportType";

interface ReportTableProps {
  data: ReportRow[];
  selectedEntityType: "" | "mail" | "meeting";
  onEditRow: (id: string) => void;
  onUpdateRow: (id: string) => void;
  onCancelRow: (id: string) => void;
  onPreviewRow: (id: string) => void;
  onEffortChange: (id: string, value: number) => void;
  onSelectAll?: (checked: boolean, pageRows: ReportRow[]) => void; // updated
  onSelectRow?: (id: string, checked: boolean) => void;
}

const ReportTable: React.FC<ReportTableProps> = ({
  data,
  selectedEntityType,
  onEditRow,
  onUpdateRow,
  onCancelRow,
  onPreviewRow,
  onEffortChange,
  onSelectAll,
  onSelectRow,
}) => {
  // -------------------- Columns --------------------
  const selectColumn: ColumnDef<ReportRow> = {
    id: "select",
    header: ({ table }) => {
      const pageRows = table.getRowModel().rows;
      const allSelected =
        pageRows.length > 0 && pageRows.every((row) => row.original.selected);

      return (
        <Checkbox
          checked={allSelected}
          onCheckedChange={(value) => {
            onSelectAll?.(
              !!value,
              pageRows.map((row) => row.original)
            );
          }}
        />
      );
    },
    cell: ({ row }) => (
      <Checkbox
        checked={row.original.selected}
        onCheckedChange={(checked) => onSelectRow?.(row.original.id, !!checked)}
      />
    ),
    size: 50,
  };

  const entityTypeColumn: ColumnDef<ReportRow> = {
    id: "entityType", // changed from accessorKey
    header: () => (
      <div
        className="flex justify-center items-center min-w-[70px] max-w-[70px] "
        style={{ margin: "0 auto" }}
      >
        <Image
          src="/event_mail_combo.png"
          width={45}
          height={45}
          className="mx-auto dark:hidden"
          alt="Mail"
        />
        <Image
          src="/event_mail_combo_dark.png"
          width={45}
          height={45}
          className="mx-auto hidden dark:block "
          alt="Mail Dark"
        />
      </div>
    ),
    cell: ({ row }) => {
      const type = row.original.entityType.toLowerCase(); // "mail" or "meeting"
      return (
        <div className="flex justify-center">
          <EntityBadge type={type as "mail" | "meeting"} />
        </div>
      );
    },

    size: 80,
    meta: { align: "center" },
  };

  const dateColumn: ColumnDef<ReportRow> = {
    accessorKey: "date",
    header: "Date",
    meta: { align: "center" },
  };
  const senderColumn: ColumnDef<ReportRow> = {
    accessorKey: "sender",
    header: "From",
    cell: ({ row }) => {
      const sender = row.original.sender;
      const displayText =
        sender.length > 10 ? sender.slice(0, 10) + "..." : sender;

      return (
        <span title={sender} className="cursor-default">
          {displayText}
        </span>
      );
    },
  };
  const recipientsColumn: ColumnDef<ReportRow> = {
    accessorKey: "recipients",
    header: "To",
    cell: ({ row }) => {
      const recipients = row.original.recipients;
      const displayText =
        recipients.length > 10 ? recipients.slice(0, 10) + "..." : recipients;

      return (
        <span title={recipients} className="cursor-default">
          {displayText}
        </span>
      );
    },
  };
  const categoriesColumn: ColumnDef<ReportRow> = {
    accessorKey: "cat_name",
    header: "Categories",
    cell: ({ row }) => row.original.cat_name ?? "",
  };
  const wordCountColumn: ColumnDef<ReportRow> = {
    accessorKey: "wordCount",
    header: "Mail Words",
    meta: { align: "center" },
  };
  const attachmentWordCountColumn: ColumnDef<ReportRow> = {
    accessorKey: "attachmentWordCount",
    header: "Attach Words",
    meta: { align: "center" },
  };
  const keywordCountColumn: ColumnDef<ReportRow> = {
    accessorKey: "keywordCount",
    header: "Keywords",
    meta: { align: "center" },
  };
  const computedEffortsColumn: ColumnDef<ReportRow> = {
    accessorKey: "ComputedEfforts",
    header: "Computed Efforts",
    meta: { align: "center" },
  };
  const meetingDurationColumn: ColumnDef<ReportRow> = {
    accessorKey: "meetingDuration",
    header: "Duration",
    meta: { align: "center" },
  };

  const effortsColumn: ColumnDef<ReportRow> = {
    accessorKey: "efforts",
    header:
      selectedEntityType === "mail" ? "Revise Efforts" : "Meeting Efforts",
    cell: ({ row }) => (
      <Input
        type="number"
        value={row.original.efforts}
        disabled={!row.original.isEditing}
        onChange={(e) =>
          onEffortChange(row.original.id, Number(e.target.value))
        }
        className="w-20 text-sm"
      />
    ),
    meta: { align: "center" },
  };

  const actionsColumn: ColumnDef<ReportRow> = {
    id: "actions",
    header: "Action",
    cell: ({ row }) => {
      const r = row.original;
      return (
        <div className="flex items-center space-x-1 justify-center">
          {r.isEditing ? (
            <>
              <Button size="sm" onClick={() => onUpdateRow(r.id)}>
                <Save className="h-3 w-3" />
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => onCancelRow(r.id)}
              >
                <X className="h-3 w-3" />
              </Button>
            </>
          ) : (
            <Button size="sm" variant="outline" onClick={() => onEditRow(r.id)}>
              <Edit className="h-3 w-3" />
            </Button>
          )}
          <Button
            size="sm"
            onClick={() => onPreviewRow(r.mail_dtl_id || r.cal_id || "")}
          >
            <Eye className="h-3 w-3" />
          </Button>
        </div>
      );
    },
    meta: { align: "center" },
  };

  // -------------------- Columns based on entity --------------------
  const columns: ColumnDef<ReportRow>[] =
    selectedEntityType === "mail"
      ? [
          selectColumn,
          entityTypeColumn,
          dateColumn,
          senderColumn,
          recipientsColumn,
          categoriesColumn,
          wordCountColumn,
          attachmentWordCountColumn,
          keywordCountColumn,
          computedEffortsColumn,
          effortsColumn,
          actionsColumn,
        ]
      : [
          selectColumn,
          entityTypeColumn,
          dateColumn,
          senderColumn,
          recipientsColumn,
          meetingDurationColumn,
          effortsColumn,
          actionsColumn,
        ];

  // -------------------- Table --------------------
  const [pageIndex, setPageIndex] = React.useState(0);
  const [pageSize, setPageSize] = React.useState(5);

  const table = useReactTable({
    data,
    columns,
    state: { pagination: { pageIndex, pageSize } },
    onStateChange: (updater) => {
      // no-op: we manage pagination explicitly below
    },
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    // prevent the table from automatically resetting page index when data changes
    autoResetPageIndex: false,
  });

  // Keep pageIndex valid when data or pageSize changes
  React.useEffect(() => {
    const pageCount = table.getPageCount();
    if (pageIndex > pageCount - 1) {
      const newIndex = Math.max(0, pageCount - 1);
      setPageIndex(newIndex);
      table.setPageIndex(newIndex);
    }
  }, [data, pageSize]);

  const getAlignClass = (align?: "left" | "center" | "right") =>
    align === "center"
      ? "text-center"
      : align === "right"
      ? "text-right"
      : "text-left";

  return (
    <div className="p-2">
      <div className="max-h-[calc(100vh-550px)] overflow-y-auto">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead
                    key={header.id}
                    className={getAlignClass(
                      (header.column.columnDef as any).meta?.align
                    )}
                  >
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.map((row) => (
              <TableRow key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <TableCell
                    key={cell.id}
                    className={getAlignClass(
                      (cell.column.columnDef as any).meta?.align
                    )}
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* -------------------- Pagination -------------------- */}
      <div className="flex justify-between mt-4 items-center">
        <div>
          <button
            onClick={() => {
              const newIndex = Math.max(0, pageIndex - 1);
              setPageIndex(newIndex);
              table.setPageIndex(newIndex);
            }}
            disabled={!table.getCanPreviousPage()}
            className="px-3 py-1 border rounded mr-2 disabled:opacity-50"
          >
            Prev
          </button>
          <button
            onClick={() => {
              const newIndex = Math.min(
                table.getPageCount() - 1,
                pageIndex + 1
              );
              setPageIndex(newIndex);
              table.setPageIndex(newIndex);
            }}
            disabled={!table.getCanNextPage()}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>

        <div className="flex items-center space-x-2">
          <span>Rows per page:</span>
          <select
            value={pageSize}
            onChange={(e) => {
              const newSize = Number(e.target.value);
              setPageSize(newSize);
              // adjust pageIndex if needed
              const newPageCount = Math.max(
                1,
                Math.ceil(data.length / newSize)
              );
              if (pageIndex > newPageCount - 1) {
                const newIndex = Math.max(0, newPageCount - 1);
                setPageIndex(newIndex);
                table.setPageIndex(newIndex);
              }
            }}
            className="border rounded px-2 py-1 dark:bg-gray-700 dark:text-white"
          >
            {[5, 10, 20, 50].map((size) => (
              <option key={size} value={size} className="dark:bg-gray-700">
                {size}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
};

export default ReportTable;

const EntityBadge: React.FC<{ type: "mail" | "meeting" }> = ({ type }) => {
  const isMail = type === "mail";
  const icon = isMail ? (
    <MailOpen className="inline-block" size={15} />
  ) : (
    <CalendarDays className="inline-block" size={15} />
  );

  return (
    <span
      className="inline-flex items-center justify-center rounded-md border px-2 py-1 text-xs font-medium w-fit whitespace-nowrap shrink-0 gap-1
                     [&>svg]:pointer-events-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]
                     aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive
                     transition-[color,box-shadow] overflow-hidden border-transparent bg-primary text-primary-foreground [a&]:hover:bg-primary/90"
    >
      {icon}
    </span>
  );
};
