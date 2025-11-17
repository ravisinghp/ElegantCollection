import axiosClient from "@/app/api/axiosClient";

interface UpdateMailRequest {
    user_id: string;
    org_id: string;
    report_id?: string;
    mail_dtl_id?: string;
    efforts?: any;
    keywordEfforts?: any;
}

export async function updateMailRowService(
    id: string,
    org_id: string,
    isOnLoad = false,
    extraData?: Partial<UpdateMailRequest>
): Promise<any> {
    let requestData: any = {};

    if (isOnLoad) {
        // Bulk update all mails of a user
        requestData = {
            user_id: id,
            org_id: org_id,
        };
    } else {
        // Update one mail row (from ReportSection)
        requestData = {
            ...extraData,
            user_id: id,
            org_id: org_id,
        };
    }

    const response = await axiosClient.post("/reports/mail", requestData);
    return response.data;
}
