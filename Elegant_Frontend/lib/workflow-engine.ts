// Workflow Engine - Orchestrates the entire R&D effort estimation process
// This is the core business logic that coordinates all workflow steps

export interface WorkflowContext {
  companyId: string
  userId?: string
  jobId: string
  step: WorkflowStep
  data: Record<string, any>
  errors: string[]
}

export enum WorkflowStep {
  EMAIL_SCAN = "email_scan",
  DOCUMENT_PROCESS = "document_process",
  KEYWORD_DETECTION = "keyword_detection",
  EFFORT_CALCULATION = "effort_calculation",
  DATA_STORAGE = "data_storage",
  NOTIFICATION = "notification",
}

export class WorkflowEngine {
  private steps: Map<WorkflowStep, WorkflowStepHandler> = new Map()

  constructor() {
    this.registerSteps()
  }

  private registerSteps() {
    this.steps.set(WorkflowStep.EMAIL_SCAN, new EmailScanHandler())
    this.steps.set(WorkflowStep.DOCUMENT_PROCESS, new DocumentProcessHandler())
    this.steps.set(WorkflowStep.KEYWORD_DETECTION, new KeywordDetectionHandler())
    this.steps.set(WorkflowStep.EFFORT_CALCULATION, new EffortCalculationHandler())
    this.steps.set(WorkflowStep.DATA_STORAGE, new DataStorageHandler())
    this.steps.set(WorkflowStep.NOTIFICATION, new NotificationHandler())
  }

  async executeWorkflow(context: WorkflowContext): Promise<WorkflowContext> {
    const handler = this.steps.get(context.step)
    if (!handler) {
      throw new Error(`No handler found for step: ${context.step}`)
    }

    try {
      console.log(`Executing workflow step: ${context.step}`)
      const updatedContext = await handler.execute(context)

      // Log successful step completion
      await this.logStepCompletion(updatedContext)

      return updatedContext
    } catch (error) {
      console.error(`Workflow step ${context.step} failed:`, error)
      context.errors.push(`Step ${context.step}: ${error.message}`)

      // Log step failure
      await this.logStepFailure(context, error)

      throw error
    }
  }

  async executeFullWorkflow(companyId: string, userId?: string): Promise<void> {
    const jobId = `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

    const steps = [
      WorkflowStep.EMAIL_SCAN,
      WorkflowStep.DOCUMENT_PROCESS,
      WorkflowStep.KEYWORD_DETECTION,
      WorkflowStep.EFFORT_CALCULATION,
      WorkflowStep.DATA_STORAGE,
      WorkflowStep.NOTIFICATION,
    ]

    let context: WorkflowContext = {
      companyId,
      userId,
      jobId,
      step: WorkflowStep.EMAIL_SCAN,
      data: {},
      errors: [],
    }

    for (const step of steps) {
      context.step = step
      context = await this.executeWorkflow(context)

      // If there are critical errors, stop the workflow
      if (context.errors.length > 0 && this.isCriticalError(step)) {
        throw new Error(`Critical error in step ${step}: ${context.errors.join(", ")}`)
      }
    }

    console.log(`Workflow completed successfully for job: ${jobId}`)
  }

  private isCriticalError(step: WorkflowStep): boolean {
    // Define which steps are critical and should stop the workflow
    return [WorkflowStep.EMAIL_SCAN, WorkflowStep.DATA_STORAGE].includes(step)
  }

  private async logStepCompletion(context: WorkflowContext): Promise<void> {
    // Log to database or monitoring system
    console.log(`Step ${context.step} completed for job ${context.jobId}`)
  }

  private async logStepFailure(context: WorkflowContext, error: Error): Promise<void> {
    // Log error to database or monitoring system
    console.error(`Step ${context.step} failed for job ${context.jobId}:`, error)
  }
}

// Abstract base class for workflow step handlers
abstract class WorkflowStepHandler {
  abstract execute(context: WorkflowContext): Promise<WorkflowContext>
}

// Email Scanning Handler
class EmailScanHandler extends WorkflowStepHandler {
  async execute(context: WorkflowContext): Promise<WorkflowContext> {
    const { companyId, userId } = context

    // Get users to scan (if userId provided, scan only that user)
    const users = userId ? [userId] : await this.getActiveUsers(companyId)

    const scannedEmails = []

    for (const user of users) {
      try {
        const userEmails = await this.scanUserEmails(user, companyId)
        scannedEmails.push(...userEmails)
      } catch (error) {
        context.errors.push(`Failed to scan emails for user ${user}: ${error.message}`)
      }
    }

    context.data.scannedEmails = scannedEmails
    context.data.emailCount = scannedEmails.length

    return context
  }

  private async getActiveUsers(companyId: string): Promise<string[]> {
    // Get all users with connected emails for this company
    return ["user1", "user2", "user3"] // Mock data
  }

  private async scanUserEmails(userId: string, companyId: string): Promise<any[]> {
    // Connect to email API and fetch new emails
    // This would integrate with Gmail API or Microsoft Graph API
    return [
      {
        id: "email_1",
        subject: "Research Update",
        body: "Our machine learning research shows...",
        attachments: ["doc1.pdf"],
      },
    ]
  }
}

// Document Processing Handler
class DocumentProcessHandler extends WorkflowStepHandler {
  async execute(context: WorkflowContext): Promise<WorkflowContext> {
    const scannedEmails = context.data.scannedEmails || []
    const processedDocuments = []

    for (const email of scannedEmails) {
      if (email.attachments && email.attachments.length > 0) {
        for (const attachment of email.attachments) {
          try {
            const processed = await this.processDocument(attachment, email.id)
            processedDocuments.push(processed)
          } catch (error) {
            context.errors.push(`Failed to process document ${attachment}: ${error.message}`)
          }
        }
      }
    }

    context.data.processedDocuments = processedDocuments
    context.data.documentCount = processedDocuments.length

    return context
  }

  private async processDocument(filename: string, emailId: string): Promise<any> {
    // Extract text from PDF, DOCX, XLSX files
    // Use OCR for scanned documents
    const fileType = filename.split(".").pop()?.toLowerCase()

    switch (fileType) {
      case "pdf":
        return await this.processPDF(filename, emailId)
      case "docx":
        return await this.processDOCX(filename, emailId)
      case "xlsx":
        return await this.processXLSX(filename, emailId)
      default:
        throw new Error(`Unsupported file type: ${fileType}`)
    }
  }

  private async processPDF(filename: string, emailId: string): Promise<any> {
    // PDF processing logic with OCR support
    return {
      filename,
      emailId,
      extractedText: "Sample extracted text from PDF...",
      wordCount: 450,
      ocrUsed: false,
    }
  }

  private async processDOCX(filename: string, emailId: string): Promise<any> {
    // DOCX processing logic
    return {
      filename,
      emailId,
      extractedText: "Sample extracted text from DOCX...",
      wordCount: 320,
      ocrUsed: false,
    }
  }

  private async processXLSX(filename: string, emailId: string): Promise<any> {
    // XLSX processing logic
    return {
      filename,
      emailId,
      extractedText: "Sample extracted text from XLSX...",
      wordCount: 200,
      ocrUsed: false,
    }
  }
}

// Keyword Detection Handler
class KeywordDetectionHandler extends WorkflowStepHandler {
  async execute(context: WorkflowContext): Promise<WorkflowContext> {
    const { companyId } = context
    const scannedEmails = context.data.scannedEmails || []
    const processedDocuments = context.data.processedDocuments || []

    // Get company keywords
    const keywords = await this.getCompanyKeywords(companyId)

    const keywordMatches = []

    // Process emails
    for (const email of scannedEmails) {
      const matches = await this.detectKeywords(email.body, keywords, "email", email.id)
      keywordMatches.push(...matches)
    }

    // Process documents
    for (const document of processedDocuments) {
      const matches = await this.detectKeywords(document.extractedText, keywords, "document", document.id)
      keywordMatches.push(...matches)
    }

    context.data.keywordMatches = keywordMatches
    context.data.totalKeywords = keywordMatches.length

    return context
  }

  private async getCompanyKeywords(companyId: string): Promise<any[]> {
    // Fetch keywords from database
    return [
      { id: "kw1", keyword: "machine learning", weight: 20, category: "technology" },
      { id: "kw2", keyword: "artificial intelligence", weight: 25, category: "technology" },
      { id: "kw3", keyword: "research", weight: 12, category: "process" },
    ]
  }

  private async detectKeywords(text: string, keywords: any[], contentType: string, contentId: string): Promise<any[]> {
    const matches = []

    // Rule-based keyword matching
    for (const keyword of keywords) {
      const regex = new RegExp(`\\b${keyword.keyword}\\b`, "gi")
      const matchCount = (text.match(regex) || []).length

      if (matchCount > 0) {
        matches.push({
          keywordId: keyword.id,
          keyword: keyword.keyword,
          contentType,
          contentId,
          matchCount,
          confidence: 0.95, // Rule-based matching has high confidence
        })
      }
    }

    // NLP-based keyword extraction (would integrate with spaCy or transformers)
    const nlpKeywords = await this.extractNLPKeywords(text)
    matches.push(
      ...nlpKeywords.map((kw) => ({
        ...kw,
        contentType,
        contentId,
        confidence: kw.confidence || 0.75,
      })),
    )

    return matches
  }

  private async extractNLPKeywords(text: string): Promise<any[]> {
    // This would integrate with NLP services like spaCy, transformers, or cloud APIs
    // For now, return mock data
    return [
      { keyword: "neural network", matchCount: 1, confidence: 0.85 },
      { keyword: "data analysis", matchCount: 2, confidence: 0.78 },
    ]
  }
}

// Effort Calculation Handler
class EffortCalculationHandler extends WorkflowStepHandler {
  async execute(context: WorkflowContext): Promise<WorkflowContext> {
    const { companyId } = context
    const scannedEmails = context.data.scannedEmails || []
    const processedDocuments = context.data.processedDocuments || []
    const keywordMatches = context.data.keywordMatches || []

    // Get company effort rules
    const rules = await this.getEffortRules(companyId)

    const effortCalculations = []

    // Calculate effort for emails
    for (const email of scannedEmails) {
      const emailKeywords = keywordMatches.filter((m) => m.contentType === "email" && m.contentId === email.id)
      const effort = await this.calculateEffort(email.body, emailKeywords, rules, "email")

      effortCalculations.push({
        contentType: "email",
        contentId: email.id,
        ...effort,
      })
    }

    // Calculate effort for documents
    for (const document of processedDocuments) {
      const docKeywords = keywordMatches.filter((m) => m.contentType === "document" && m.contentId === document.id)
      const effort = await this.calculateEffort(document.extractedText, docKeywords, rules, "document")

      effortCalculations.push({
        contentType: "document",
        contentId: document.id,
        ...effort,
      })
    }

    context.data.effortCalculations = effortCalculations
    context.data.totalEffort = effortCalculations.reduce((sum, calc) => sum + calc.totalEffort, 0)

    return context
  }

  private async getEffortRules(companyId: string): Promise<any> {
    // Fetch effort rules from database
    return {
      wordsToMinutes: 0.3, // 100 words = 30 minutes
      keywordBaseMinutes: 15, // Base minutes per keyword
      documentMultipliers: {
        pdf: 1.5,
        docx: 1.2,
        xlsx: 1.0,
      },
    }
  }

  private async calculateEffort(text: string, keywords: any[], rules: any, contentType: string): Promise<any> {
    // Calculate base effort from word count
    const wordCount = text.split(/\s+/).length
    const baseEffort = Math.round(wordCount * rules.wordsToMinutes)

    // Calculate keyword effort
    let keywordEffort = 0
    for (const keyword of keywords) {
      keywordEffort += keyword.matchCount * rules.keywordBaseMinutes
    }

    // Apply document type multiplier
    let multiplier = 1.0
    if (contentType === "document") {
      // This would be determined by file extension
      multiplier = rules.documentMultipliers.pdf || 1.0
    }

    const totalEffort = Math.round((baseEffort + keywordEffort) * multiplier)

    return {
      wordCount,
      baseEffort,
      keywordEffort,
      multiplier,
      totalEffort,
      keywordCount: keywords.length,
    }
  }
}

// Data Storage Handler
class DataStorageHandler extends WorkflowStepHandler {
  async execute(context: WorkflowContext): Promise<WorkflowContext> {
    const { companyId, jobId } = context

    try {
      // Store all processed data to database
      await this.storeEmails(context.data.scannedEmails, companyId)
      await this.storeDocuments(context.data.processedDocuments, companyId)
      await this.storeKeywordMatches(context.data.keywordMatches, companyId)
      await this.storeEffortCalculations(context.data.effortCalculations, companyId)
      await this.updateJobStatus(jobId, "completed")

      context.data.storageComplete = true
    } catch (error) {
      await this.updateJobStatus(jobId, "failed", error.message)
      throw error
    }

    return context
  }

  private async storeEmails(emails: any[], companyId: string): Promise<void> {
    // Store emails in database
    console.log(`Storing ${emails.length} emails for company ${companyId}`)
  }

  private async storeDocuments(documents: any[], companyId: string): Promise<void> {
    // Store documents in database
    console.log(`Storing ${documents.length} documents for company ${companyId}`)
  }

  private async storeKeywordMatches(matches: any[], companyId: string): Promise<void> {
    // Store keyword matches in database
    console.log(`Storing ${matches.length} keyword matches for company ${companyId}`)
  }

  private async storeEffortCalculations(calculations: any[], companyId: string): Promise<void> {
    // Store effort calculations in database
    console.log(`Storing ${calculations.length} effort calculations for company ${companyId}`)
  }

  private async updateJobStatus(jobId: string, status: string, errorMessage?: string): Promise<void> {
    // Update job status in database
    console.log(`Job ${jobId} status updated to: ${status}`)
  }
}

// Notification Handler
class NotificationHandler extends WorkflowStepHandler {
  async execute(context: WorkflowContext): Promise<WorkflowContext> {
    const { companyId, jobId } = context
    const totalEffort = context.data.totalEffort || 0
    const emailCount = context.data.emailCount || 0
    const documentCount = context.data.documentCount || 0

    // Send completion notification
    await this.sendJobCompletionNotification(companyId, jobId, {
      totalEffort,
      emailCount,
      documentCount,
      errors: context.errors,
    })

    // Check for high activity alerts
    if (totalEffort > 480) {
      // More than 8 hours
      await this.sendHighActivityAlert(companyId, totalEffort)
    }

    // Send error notifications if any
    if (context.errors.length > 0) {
      await this.sendErrorNotifications(companyId, context.errors)
    }

    context.data.notificationsSent = true

    return context
  }

  private async sendJobCompletionNotification(companyId: string, jobId: string, summary: any): Promise<void> {
    console.log(`Sending job completion notification for ${jobId}:`, summary)
    // Send email, push notification, or in-app notification
  }

  private async sendHighActivityAlert(companyId: string, totalEffort: number): Promise<void> {
    console.log(`High activity alert: ${totalEffort} minutes of R&D effort detected`)
    // Send alert to admins
  }

  private async sendErrorNotifications(companyId: string, errors: string[]): Promise<void> {
    console.log(`Sending error notifications:`, errors)
    // Send error alerts to admins
  }
}

// Export the workflow engine instance
export const workflowEngine = new WorkflowEngine()
