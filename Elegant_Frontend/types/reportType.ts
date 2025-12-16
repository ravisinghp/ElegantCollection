export type EntityType = "mail" | "meeting";

export interface ReportRow {
  id: string;
  entityType: EntityType;  // must be "mail" or "meeting"
  date: string;
  sender: string;
  recipients: string;
  wordCount?: number;
  attachmentWordCount?: number;
  keywordCount?: number;
  ComputedEfforts?: number;
  keywordEfforts?: number;
  efforts: number | string;
  selected: boolean;
  mail_dtl_id?: string;
  cal_id?: string;
  meetingDuration?: string | number;
  isEditing?: boolean;
  cat_name?:string;
}
