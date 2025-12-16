import type React from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Users,
  Mail,
  FileText,
  Brain,
  Calculator,
  Database,
  BarChart3,
  Settings,
  Search,
  Bell,
  Shield,
  ArrowDown,
  CheckCircle,
} from "lucide-react"

export default function WorkflowPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-800">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">R&D Effort Estimator Workflow</h1>
          <p className="text-lg text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
            Complete step-by-step workflow showing how the system processes emails, analyzes content, and generates R&D
            effort estimates.
          </p>
        </div>

        <div className="space-y-8">
          <WorkflowSection step="1" title="User Onboarding" icon={<Users className="h-6 w-6" />} color="bg-blue-500">
            <div className="grid md:grid-cols-2 gap-4">
              <ProcessCard
                title="Super Admin Setup"
                description="Creates company account with multi-tenant support"
                details={[
                  "Company registration and configuration",
                  "Initial admin user creation",
                  "Tenant isolation setup",
                  "Billing and subscription management",
                ]}
              />
              <ProcessCard
                title="User Management"
                description="Admin adds employees or contractors as Users"
                details={[
                  "User invitation system",
                  "Role assignment (Admin/User)",
                  "Department and team organization",
                  "Access permission configuration",
                ]}
              />
            </div>
            <div className="mt-4">
              <ProcessCard
                title="OAuth Registration"
                description="Users register/login via Google or Microsoft email"
                details={[
                  "OAuth 2.0 integration with Google/Microsoft",
                  "Secure token management",
                  "User profile synchronization",
                  "Multi-factor authentication support",
                ]}
              />
            </div>
          </WorkflowSection>

          <WorkflowSection step="2" title="Email Connection" icon={<Mail className="h-6 w-6" />} color="bg-green-500">
            <div className="grid md:grid-cols-2 gap-4">
              <ProcessCard
                title="OAuth 2.0 Integration"
                description="User connects email account securely"
                details={[
                  "Gmail API / Outlook API integration",
                  "Scope-limited access (read-only inbox)",
                  "Refresh token management",
                  "Connection status monitoring",
                ]}
              />
              <ProcessCard
                title="Scheduled Scanning"
                description="Daily job to scan only the Inbox"
                details={[
                  "Cron job configuration",
                  "Incremental email fetching",
                  "Rate limiting compliance",
                  "Error handling and retry logic",
                ]}
              />
            </div>
          </WorkflowSection>

          <WorkflowSection
            step="3"
            title="Email & Attachment Scanning"
            icon={<FileText className="h-6 w-6" />}
            color="bg-purple-500"
          >
            <div className="grid md:grid-cols-3 gap-4">
              <ProcessCard
                title="Email Processing"
                description="Extract metadata and content"
                details={[
                  "Subject, sender, timestamp extraction",
                  "Plain text body conversion",
                  "HTML content parsing",
                  "Thread and conversation tracking",
                ]}
              />
              <ProcessCard
                title="Attachment Handling"
                description="Download and parse documents"
                details={[
                  "PDF text extraction",
                  "DOCX content parsing",
                  "XLSX data extraction",
                  "File type validation",
                ]}
              />
              <ProcessCard
                title="OCR Processing"
                description="Handle scanned documents"
                details={[
                  "Image-based PDF detection",
                  "OCR engine integration",
                  "Text quality validation",
                  "Language detection",
                ]}
              />
            </div>
          </WorkflowSection>

          <WorkflowSection
            step="4"
            title="Keyword Detection"
            icon={<Brain className="h-6 w-6" />}
            color="bg-orange-500"
          >
            <div className="grid md:grid-cols-2 gap-4">
              <ProcessCard
                title="Rule-Based Matching"
                description="Match against Admin-defined keywords"
                details={[
                  "Exact keyword matching",
                  "Fuzzy string matching",
                  "Regular expression support",
                  "Case-insensitive matching",
                ]}
              />
              <ProcessCard
                title="NLP Analysis"
                description="AI-powered keyword and topic extraction"
                details={[
                  "spaCy or transformers integration",
                  "Named entity recognition",
                  "Topic modeling",
                  "Sentiment analysis",
                ]}
              />
            </div>
            <div className="mt-4">
              <ProcessCard
                title="Domain Classification"
                description="Classify keywords by business domain"
                details={[
                  "Technology keywords",
                  "Research methodology terms",
                  "Product development indicators",
                  "Innovation markers",
                ]}
              />
            </div>
          </WorkflowSection>

          <WorkflowSection
            step="5"
            title="Effort Estimation"
            icon={<Calculator className="h-6 w-6" />}
            color="bg-red-500"
          >
            <div className="grid md:grid-cols-2 gap-4">
              <ProcessCard
                title="Rule Application"
                description="Apply Admin-defined calculation rules"
                details={[
                  "Word count to time conversion",
                  "Keyword weight multipliers",
                  "Document type modifiers",
                  "Complexity scoring",
                ]}
              />
              <ProcessCard
                title="Effort Calculation"
                description="Calculate total effort across dimensions"
                details={[
                  "Per email effort calculation",
                  "Per attachment analysis",
                  "Per user aggregation",
                  "Time period summaries",
                ]}
              />
            </div>
          </WorkflowSection>

          <WorkflowSection step="6" title="Data Mapping" icon={<Database className="h-6 w-6" />} color="bg-indigo-500">
            <ProcessCard
              title="Database Storage"
              description="Store calculated effort with proper associations"
              details={[
                "User-content association",
                "Timestamp tracking",
                "Effort calculation storage",
                "Audit trail maintenance",
              ]}
            />
          </WorkflowSection>

          <WorkflowSection
            step="7"
            title="Dashboard & Reporting"
            icon={<BarChart3 className="h-6 w-6" />}
            color="bg-teal-500"
          >
            <div className="grid md:grid-cols-3 gap-4">
              <ProcessCard
                title="Admin Dashboard"
                description="Comprehensive effort analytics"
                details={[
                  "Effort by user visualization",
                  "Keyword heatmaps",
                  "Trend analysis charts",
                  "Performance metrics",
                ]}
              />
              <ProcessCard
                title="Report Generation"
                description="Exportable reports"
                details={[
                  "PDF report generation",
                  "Excel export functionality",
                  "Custom date ranges",
                  "Filtered data views",
                ]}
              />
              <ProcessCard
                title="Real-time Updates"
                description="Live dashboard updates"
                details={[
                  "WebSocket connections",
                  "Real-time notifications",
                  "Auto-refresh capabilities",
                  "Mobile responsiveness",
                ]}
              />
            </div>
          </WorkflowSection>

          <WorkflowSection
            step="8"
            title="Rule & Keyword Management"
            icon={<Settings className="h-6 w-6" />}
            color="bg-pink-500"
          >
            <div className="grid md:grid-cols-2 gap-4">
              <ProcessCard
                title="Admin Interface"
                description="Update rules and keywords via UI"
                details={[
                  "Keyword list management",
                  "Rule configuration interface",
                  "Bulk import/export",
                  "Version control",
                ]}
              />
              <ProcessCard
                title="Change Management"
                description="Apply changes to future scans only"
                details={[
                  "Forward-only rule application",
                  "Change impact analysis",
                  "Rollback capabilities",
                  "Change notifications",
                ]}
              />
            </div>
          </WorkflowSection>

          <WorkflowSection
            step="9"
            title="Search & Filters"
            icon={<Search className="h-6 w-6" />}
            color="bg-yellow-500"
          >
            <ProcessCard
              title="Advanced Search"
              description="Multi-dimensional search and filtering"
              details={[
                "Employee-based filtering",
                "Keyword search functionality",
                "Date range selection",
                "File type and domain filters",
              ]}
            />
          </WorkflowSection>

          <WorkflowSection step="10" title="Notifications" icon={<Bell className="h-6 w-6" />} color="bg-cyan-500">
            <div className="grid md:grid-cols-3 gap-4">
              <ProcessCard
                title="Activity Alerts"
                description="High R&D activity notifications"
                details={["Threshold-based alerts", "Anomaly detection", "Spike notifications", "Weekly summaries"]}
              />
              <ProcessCard
                title="System Alerts"
                description="Technical issue notifications"
                details={[
                  "Scan failure alerts",
                  "Rule error notifications",
                  "API quota warnings",
                  "System health monitoring",
                ]}
              />
              <ProcessCard
                title="Access Alerts"
                description="Email access issues"
                details={[
                  "Token expiration warnings",
                  "Permission change alerts",
                  "Connection failure notifications",
                  "Re-authentication prompts",
                ]}
              />
            </div>
          </WorkflowSection>

          <WorkflowSection step="11" title="Security" icon={<Shield className="h-6 w-6" />} color="bg-gray-700">
            <div className="grid md:grid-cols-3 gap-4">
              <ProcessCard
                title="OAuth Security"
                description="Secure email access"
                details={["OAuth 2.0 compliance", "Minimal scope requests", "Token encryption", "Secure token storage"]}
              />
              <ProcessCard
                title="Role-Based Access"
                description="Data access control"
                details={["User role management", "Permission-based views", "Data isolation", "Audit logging"]}
              />
              <ProcessCard
                title="Data Protection"
                description="Secure data storage"
                details={["Encryption at rest", "Encryption in transit", "GDPR compliance", "Data retention policies"]}
              />
            </div>
          </WorkflowSection>
        </div>

        {/* Technical Architecture */}
        <div className="mt-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">Technical Architecture</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <TechCard
              title="Frontend"
              technologies={[
                "Next.js 14 (App Router)",
                "React 18",
                "Tailwind CSS",
                "shadcn/ui components",
                "TypeScript",
              ]}
            />
            <TechCard
              title="Backend"
              technologies={["Next.js API Routes", "Server Actions", "Node.js runtime", "Prisma ORM", "Zod validation"]}
            />
            <TechCard
              title="Database"
              technologies={[
                "PostgreSQL",
                "Redis (caching)",
                "Prisma migrations",
                "Connection pooling",
                "Multi-tenant schema",
              ]}
            />
            <TechCard
              title="External APIs"
              technologies={["Gmail API", "Microsoft Graph API", "OAuth 2.0 providers", "NLP services", "OCR services"]}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

function WorkflowSection({
  step,
  title,
  icon,
  color,
  children,
}: {
  step: string
  title: string
  icon: React.ReactNode
  color: string
  children: React.ReactNode
}) {
  return (
    <div className="relative">
      <div className="flex items-center mb-6">
        <div
          className={`${color} text-white rounded-full w-12 h-12 flex items-center justify-center font-bold text-lg mr-4`}
        >
          {step}
        </div>
        <div className="flex items-center space-x-3">
          <div className="text-gray-600 dark:text-gray-300">{icon}</div>
          <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
        </div>
      </div>
      {children}
      {step !== "11" && (
        <div className="flex justify-center mt-8">
          <ArrowDown className="h-6 w-6 text-gray-400" />
        </div>
      )}
    </div>
  )
}

function ProcessCard({
  title,
  description,
  details,
}: {
  title: string
  description: string
  details: string[]
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2">
          {details.map((detail, index) => (
            <li key={index} className="flex items-start space-x-2 text-sm">
              <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
              <span>{detail}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}

function TechCard({
  title,
  technologies,
}: {
  title: string
  technologies: string[]
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2">
          {technologies.map((tech, index) => (
            <li key={index} className="text-sm">
              <Badge variant="secondary" className="text-xs">
                {tech}
              </Badge>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}
