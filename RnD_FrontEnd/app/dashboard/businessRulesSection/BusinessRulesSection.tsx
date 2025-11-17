"use client"

import { useEffect, useState, useRef } from "react"
import axiosClient from "@/app/api/axiosClient"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
    DialogFooter,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from "@/components/ui/card"
import { Plus, Edit, Save, X } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { TabsContent } from "@/components/ui/tabs"
import { ArrowRight, UserCog, Zap, Loader2 } from "lucide-react";

type BusinessRule = {
    rule_id: number
    rule_name: string
    rule_value: number
}

interface CreateBusinessRuleDialogProps {
    onClose: () => void
    onSuccess?: () => void | Promise<void> // ✅ optional prop
}

export default function BusinessRulesTab() {
    const [businessRules, setBusinessRules] = useState<BusinessRule[]>([])
    const [editingId, setEditingId] = useState<number | null>(null)
    const [isCreateBusinessRuleDialogOpen, setIsCreateBusinessRuleDialogOpen] = useState(false)
    const { toast } = useToast()
    const [backupValues, setBackupValues] = useState<Record<number, number>>({})
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchBusinessRules()
    }, [])

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

    const fetchBusinessRules = async () => {
        try {
            const orgIdStr = sessionStorage.getItem("orgid") || localStorage.getItem("orgid")
            const userIdStr = sessionStorage.getItem("userid") || localStorage.getItem("userid")
            const orgId = orgIdStr ? Number(orgIdStr) : 0
            const userId = userIdStr ? Number(userIdStr) : 0

            if (!orgId || !userId) {
                console.error("Missing org_id or user_id in storage")
                return
            }

            const res = await axiosClient.post("/reports/fetch_business_rules_by_org_id", {
                org_id: orgId,
                user_id: userId,
            })

            if (!res.data.success) {
                toast({
                    title: "Info",
                    description: res.data.message,
                    variant: "default",
                    duration: 1000,
                })
                setBusinessRules([])
            } else {
                toast({
                    title: "Success",
                    description: res.data.message,
                    variant: "default",
                    duration: 1000,
                })
                setBusinessRules(res.data.rules)
            }
        } catch (err) {
            console.error("Failed to fetch business rules", err)
            toast({
                title: "Error",
                description: "Failed to fetch business rules",
                variant: "destructive",
            })
        }
    }

    const handleEdit = (rule_id: number, rule_value: number) => {
        setEditingId(rule_id)
        setBackupValues(prev => ({ ...prev, [rule_id]: rule_value }))
    }

    const handleCancel = (rule_id: number) => {
        setBusinessRules(prev =>
            prev.map(r =>
                r.rule_id === rule_id
                    ? { ...r, rule_value: backupValues[rule_id] ?? r.rule_value }
                    : r
            )
        )
        setEditingId(null)
        setBackupValues(prev => {
            const newBackups = { ...prev }
            delete newBackups[rule_id] // cleanup
            return newBackups
        })
    }

    const handleChange = (id: number, value: number) => {
        setBusinessRules(prev =>
            prev.map(r => (r.rule_id === id ? { ...r, rule_value: value } : r))
        )
    }

    const handleSave = async (rule_id: number, value: number) => {
        const { userId, orgId } = getUserContext();

        if (!value || value <= 0) {
            toast({
                title: "Validation Error",
                description: "Value must be > 0",
                variant: "destructive"
            });
            return;
        }

        const rule_value = value;
        setLoading(true);

        try {
            // 1️⃣ Update the business rule
            await axiosClient.post("/reports/business_rules/update", {
                rule_id,
                rule_value,
                org_id: orgId
            });

            toast({
                title: "Success",
                description: "Rule updated",
                variant: "default"
            });

            setEditingId(null);

            await new Promise((resolve) => setTimeout(resolve, 3000));

            setLoading(true);
            // 2️⃣ Call recalculation endpoint
            const response = await axiosClient.post("/reports/recalculate_efforts", {
                org_id: orgId,
                user_id: userId
            });

            if (response.status === 200) {
                toast({
                    title: "Success",
                    description: "Efforts recalculated successfully",
                    variant: "default",
                });
            }

            //------------Refresh rules------------
            setTimeout(() => {
                fetchBusinessRules();
            }, 3000);

        } catch (err) {
            toast({
                title: "Error",
                description: "Update or recalculation failed",
                variant: "destructive"
            });
        } finally {
            setLoading(false); //stop loader
        }
    };

    return (
        <TabsContent value="business-rules" className="space-y-4">
            {loading && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/30 backdrop-blur-[2px] z-50">
                    <div className="flex flex-col items-center space-y-4 text-white">
                        <Loader2 className="h-10 w-10 animate-spin" />
                        <p className="text-xl font-semibold">Loading...</p>
                    </div>
                </div>
            )}
            <Card className="gap-2 disable-styles">
                <CardHeader className="flex flex-row items-center justify-between  px-0 mb-[0.5rem]">
                    <div>
                        {/* <CardTitle>Business Rules</CardTitle> */}
                        {/*<CardDescription>Manage R&D effort calculation rules</CardDescription>*/}
                    </div>
                    <Dialog open={isCreateBusinessRuleDialogOpen} onOpenChange={setIsCreateBusinessRuleDialogOpen}>
                        <DialogTrigger asChild>
                            <Button size="sm">
                                <Plus className="h-4 w-4 mr-2" />
                                Create New
                            </Button>
                        </DialogTrigger>
                        <CreateBusinessRuleDialog
                            onClose={() => setIsCreateBusinessRuleDialogOpen(false)}
                            onSuccess={fetchBusinessRules} //  refresh after create
                        />
                    </Dialog>
                </CardHeader>
                <CardContent className="h-[16rem] overflow-y-auto space-y-4  px-0">
                    <div className="space-y-4  overflow-y-auto grid grid-cols-[1fr_1fr] gap-x-2 ">
                        {businessRules.map((rule) => (
                            <div key={rule.rule_id} className="flex items-center space-x-4 p-4 rounded-lg border h-fit">
                                <div className="flex-1">{rule.rule_name.replace(/_/g, " ")}</div>

                                <div className="w-32">
                                    {editingId === rule.rule_id ? (
                                        <Input
                                            type="number"
                                            value={rule.rule_value}
                                            onChange={(e) => handleChange(rule.rule_id, Number(e.target.value))}
                                        />
                                    ) : (
                                        <span>
                                            {rule.rule_value}{" "}
                                            {rule.rule_name.includes("word_count") ? "words" : "min"}
                                        </span>
                                    )}
                                </div>

                                <div className="ml-4">
                                    {editingId === rule.rule_id ? (
                                        <>
                                            <Button size="sm" onClick={() => handleSave(rule.rule_id, rule.rule_value)} className="mr-2">
                                                <Save className="h-4 w-4" />
                                            </Button>
                                            <Button size="sm" variant="outline" onClick={() => handleCancel(rule.rule_id)}>
                                                <X className="h-4 w-4" />
                                            </Button>
                                        </>
                                    ) : (
                                        <Button size="sm" variant="outline" onClick={() => handleEdit(rule.rule_id, rule.rule_value)}>
                                            <Edit className="h-4 w-4" />
                                        </Button>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </TabsContent>
    )
}

// ------------------ Create Business Rule Dialog ------------------
function CreateBusinessRuleDialog({ onClose, onSuccess }: CreateBusinessRuleDialogProps) {
    const { toast } = useToast()

    const emailBodyWordsRef = useRef<HTMLInputElement>(null)
    const emailBodyEffortRef = useRef<HTMLInputElement>(null)
    const attachmentWordsRef = useRef<HTMLInputElement>(null)
    const attachmentEffortRef = useRef<HTMLInputElement>(null)
    const keywordRepeatEffortRef = useRef<HTMLInputElement>(null)
    const minEffortRef = useRef<HTMLInputElement>(null)

    const [loading, setLoading] = useState(false);
    const handleSaveAllRules = async () => {
        setLoading(true); // start loading
        try {
            const orgIdStr = sessionStorage.getItem("orgid") || localStorage.getItem("orgid");
            const orgId = orgIdStr ? Number(orgIdStr) : 0;
            if (!orgId) throw new Error("Invalid org_id");

            const rules = [
                { org_id: orgId, rule_key: "email_body_word_count", rule_value: Number(emailBodyWordsRef.current?.value || 0) },
                { org_id: orgId, rule_key: "email_body_effort", rule_value: Number(emailBodyEffortRef.current?.value || 0) },
                { org_id: orgId, rule_key: "attachment_word_count", rule_value: Number(attachmentWordsRef.current?.value || 0) },
                { org_id: orgId, rule_key: "attachment_effort", rule_value: Number(attachmentEffortRef.current?.value || 0) },
                { org_id: orgId, rule_key: "keyword_repeat_effort", rule_value: Number(keywordRepeatEffortRef.current?.value || 0) },
                { org_id: orgId, rule_key: "minimum_effort", rule_value: Number(minEffortRef.current?.value || 0) },
            ];

            // Validate all fields
            for (const r of rules) {
                if (!r.rule_value || isNaN(r.rule_value) || r.rule_value <= 0) {
                    toast({
                        title: "Validation Error",
                        description: `All fields are mandatory.`,
                        variant: "destructive",
                    });
                    return;
                }
            }

            // Save rules
            const response = await axiosClient.post("/reports/save_business_rules", { rules });
            let hasWarning = false;

            response.data.results.forEach((r: { rule_key: string; message: string }) => {
                const isSuccess = r.message.includes("successfully");
                if (!isSuccess) {
                    hasWarning = true; // mark warning/error
                }

                toast({
                    title: isSuccess ? "Success" : "Warning",
                    description: r.message,
                    variant: isSuccess ? "default" : "destructive",
                    duration: 3000,
                });
            });

            // Delay close + refresh only if no warning
            setTimeout(async () => {
                if (!hasWarning) {
                    if (onSuccess) {
                        await onSuccess(); // ✅ trigger parent refresh only on success
                    }
                    onClose(); // Close modal
                }
            }, 3000);

        } catch (err: any) {
            toast({
                title: "Error!",
                description: err.message || "Something went wrong",
                variant: "destructive",
            });
        }
        finally {
            setLoading(false); // stop loading
        }
    };


    return (
        <DialogContent className="sm:max-w-[610px]">
            <DialogHeader>
                <DialogTitle>Create Business Rule</DialogTitle>
            </DialogHeader>

            <div className="grid gap-4 py-4">
                <div className="grid grid-cols-4 items-center gap-2">
                    <Label htmlFor="email-body-words" className="text-right">Email Body Words :</Label>
                    <Input ref={emailBodyWordsRef} id="email-body-words" type="number" className="col-span-1" placeholder="e.g., 100" />

                    <Label htmlFor="email-body-effort" className="text-right ml-10">Effort (min) :</Label>
                    <Input ref={emailBodyEffortRef} id="email-body-effort" type="number" className="col-span-1" placeholder="e.g., 30" />
                </div>

                <div className="grid grid-cols-4 items-center gap-2">
                    <Label htmlFor="attachment-words" className="text-right">Attachment Words :</Label>
                    <Input ref={attachmentWordsRef} id="attachment-words" type="number" className="col-span-1" placeholder="e.g., 100" />

                    <Label htmlFor="attachment-effort" className="text-right ml-10">Effort (min) :</Label>
                    <Input ref={attachmentEffortRef} id="attachment-effort" type="number" className="col-span-1" placeholder="e.g., 60" />
                </div>

                <div className="grid grid-cols-2 items-center gap-2">
                    <Label htmlFor="keyword-repeat" className="text-right">Effort per Repeated Keyword (min) :</Label>
                    <Input ref={keywordRepeatEffortRef} id="keyword-repeat" type="number" className="col-span-1" placeholder="e.g., 5" />
                </div>

                <div className="grid grid-cols-2 items-center gap-2">
                    <Label htmlFor="min-effort" className="text-right">Minimum Effort (min) :</Label>
                    <Input ref={minEffortRef} id="min-effort" type="number" className="col-span-1" placeholder="e.g., 15" />
                </div>
            </div>

            <DialogFooter>
                <Button onClick={handleSaveAllRules}>{loading ? "Creating..." : "Create Rule"}</Button>
            </DialogFooter>
        </DialogContent>
    )
}
