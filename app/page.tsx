import type React from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ArrowRight, Mail, FileText, BarChart3, Users, Shield, Zap } from "lucide-react"
import Link from "next/link"
import Login from "./login/page"

export default function HomePage() {
  return (
    // <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
    //   {/* Header */}
    //   <header className="border-b bg-white/90 dark:bg-gray-900/90 backdrop-blur-sm">
    //     <div className="container mx-auto px-4 py-4 flex justify-between items-center">
    //       <div className="flex items-center space-x-2">
    //         <BarChart3 className="h-8 w-8 text-theme-orange" />
    //         <h1 className="text-2xl font-bold font-serif text-gray-900 dark:text-white">R&D Effort Estimator</h1>
    //       </div>
    //       <div className="space-x-4">
    //         <Button variant="ghost" asChild>
    //           <Link href="/login">Login</Link>
    //         </Button>
    //         <Button className="bg-theme-orange hover:bg-theme-green transition-colors" asChild>
    //           <Link href="/register">Get Started</Link>
    //         </Button>
    //       </div>
    //     </div>
    //   </header>

    //   {/* Hero Section */}
    //   <section className="container mx-auto px-4 py-16 text-center">
    //     <Badge variant="secondary" className="mb-4 bg-theme-yellow/20 text-theme-orange border-theme-yellow">
    //       Automated R&D Tracking
    //     </Badge>
    //     <h2 className="text-4xl md:text-6xl font-bold font-serif text-gray-900 dark:text-white mb-6">
    //       Transform Email Analysis into
    //       <span className="text-theme-orange"> R&D Insights</span>
    //     </h2>
    //     <p className="text-xl text-gray-600 dark:text-gray-300 dark:text-gray-300 mb-8 max-w-3xl mx-auto">
    //       Automatically analyze emails and documents to calculate R&D effort based on keywords and predefined rules. Get
    //       comprehensive insights into your team's research and development activities.
    //     </p>
    //     <div className="flex flex-col sm:flex-row gap-4 justify-center">
    //       <Button
    //         size="lg"
    //         className="bg-theme-orange hover:bg-theme-green transition-all duration-300 transform hover:scale-105"
    //         asChild
    //       >
    //         <Link href="/register">
    //           Start Free Trial <ArrowRight className="ml-2 h-4 w-4" />
    //         </Link>
    //       </Button>
    //       <Button
    //         size="lg"
    //         variant="outline"
    //         className="border-theme-orange text-theme-orange hover:bg-theme-orange hover:text-white transition-all duration-300 bg-transparent"
    //         asChild
    //       >
    //         <Link href="/demo">View Demo</Link>
    //       </Button>
    //     </div>
    //   </section>

    //   {/* Workflow Overview */}
    //   <section className="container mx-auto px-4 py-16">
    //     <div className="text-center mb-12">
    //       <h3 className="text-3xl font-bold font-serif text-gray-900 dark:text-white mb-4">How It Works</h3>
    //       <p className="text-lg text-gray-600 dark:text-gray-300 dark:text-gray-300">Simple workflow, powerful insights</p>
    //     </div>

    //     <div className="grid md:grid-cols-3 gap-8">
    //       <WorkflowStep
    //         icon={<Mail className="h-8 w-8" />}
    //         title="Connect Email"
    //         description="Securely connect your email account via OAuth. We scan your inbox daily for R&D-related content."
    //         step="1"
    //         color="orange"
    //       />
    //       <WorkflowStep
    //         icon={<FileText className="h-8 w-8" />}
    //         title="Analyze Content"
    //         description="AI-powered analysis extracts keywords from emails and attachments (PDF, DOCX, XLSX) using NLP."
    //         step="2"
    //         color="green"
    //       />
    //       <WorkflowStep
    //         icon={<BarChart3 className="h-8 w-8" />}
    //         title="Calculate Effort"
    //         description="Apply custom rules to estimate R&D effort. View dashboards and export detailed reports."
    //         step="3"
    //         color="yellow"
    //       />
    //     </div>
    //   </section>

    //   {/* Features Grid */}
    //   <section className="container mx-auto px-4 py-16">
    //     <div className="text-center mb-12">
    //       <h3 className="text-3xl font-bold font-serif text-gray-900 dark:text-white mb-4">Key Features</h3>
    //     </div>

    //     <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
    //       <FeatureCard
    //         icon={<Users className="h-6 w-6" />}
    //         title="Multi-Tenant Support"
    //         description="Super Admin creates company accounts, Admins manage users and contractors."
    //         color="orange"
    //       />
    //       <FeatureCard
    //         icon={<Shield className="h-6 w-6" />}
    //         title="Secure OAuth Integration"
    //         description="Connect Google or Microsoft email accounts securely without storing credentials."
    //         color="green"
    //       />
    //       <FeatureCard
    //         icon={<Zap className="h-6 w-6" />}
    //         title="Automated Scanning"
    //         description="Daily scheduled jobs scan inbox for new emails and attachments automatically."
    //         color="yellow"
    //       />
    //       <FeatureCard
    //         icon={<FileText className="h-6 w-6" />}
    //         title="Document Processing"
    //         description="Extract text from PDF, DOCX, XLSX files with OCR support for scanned documents."
    //         color="orange"
    //       />
    //       <FeatureCard
    //         icon={<BarChart3 className="h-6 w-6" />}
    //         title="Advanced Analytics"
    //         description="Keyword heatmaps, effort trends, and exportable reports (PDF/Excel)."
    //         color="green"
    //       />
    //       <FeatureCard
    //         icon={<Mail className="h-6 w-6" />}
    //         title="Smart Notifications"
    //         description="Alerts for high R&D activity, scan errors, and missing email access."
    //         color="yellow"
    //       />
    //     </div>
    //   </section>

    //   {/* CTA Section */}
    //   <section className="bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 text-white py-16 relative overflow-hidden">
    //     <div className="absolute inset-0 bg-gradient-to-r from-theme-orange/10 via-theme-green/10 to-theme-yellow/10"></div>
    //     <div className="container mx-auto px-4 text-center relative z-10">
    //       <h3 className="text-3xl font-bold font-serif mb-4">Ready to Get Started?</h3>
    //       <p className="text-xl mb-8 opacity-90">
    //         Join companies already using R&D Effort Estimator to track their research activities.
    //       </p>
    //       <Button
    //         size="lg"
    //         className="bg-theme-orange hover:bg-theme-green transition-all duration-300 transform hover:scale-105"
    //         asChild
    //       >
    //         <Link href="/register">
    //           Start Your Free Trial <ArrowRight className="ml-2 h-4 w-4" />
    //         </Link>
    //       </Button>
    //     </div>
    //   </section>

    //   {/* Footer */}
    //   <footer className="bg-gray-900 text-white py-8">
    //     <div className="container mx-auto px-4 text-center">
    //       <p>&copy; 2024 R&D Effort Estimator. All rights reserved.</p>
    //     </div>
    //   </footer>
    // </div
    <Login></Login>
  )
}

function WorkflowStep({
  icon,
  title,
  description,
  step,
  color,
}: {
  icon: React.ReactNode
  title: string
  description: string
  step: string
  color: "orange" | "green" | "yellow"
}) {
  const colorClasses = {
    orange: "bg-theme-orange text-white",
    green: "bg-theme-green text-white",
    yellow: "bg-theme-yellow text-gray-900",
  }

  const iconColorClasses = {
    orange: "text-theme-orange",
    green: "text-theme-green",
    yellow: "text-theme-yellow",
  }

  return (
    <Card className="relative hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1">
      <CardHeader className="text-center">
        <div
          className={`absolute -top-4 left-1/2 transform -translate-x-1/2 ${colorClasses[color]} rounded-full w-8 h-8 flex items-center justify-center font-bold shadow-lg`}
        >
          {step}
        </div>
        <div className={`${iconColorClasses[color]} mb-2 flex justify-center mt-4`}>{icon}</div>
        <CardTitle className="font-serif">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <CardDescription className="text-center">{description}</CardDescription>
      </CardContent>
    </Card>
  )
}

function FeatureCard({
  icon,
  title,
  description,
  color,
}: {
  icon: React.ReactNode
  title: string
  description: string
  color: "orange" | "green" | "yellow"
}) {
  const iconColorClasses = {
    orange: "text-theme-orange",
    green: "text-theme-green",
    yellow: "text-theme-yellow",
  }

  return (
    <Card className="hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1">
      <CardHeader>
        <div className={`${iconColorClasses[color]} mb-2`}>{icon}</div>
        <CardTitle className="text-lg font-serif">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <CardDescription>{description}</CardDescription>
      </CardContent>
    </Card>
  )
}
