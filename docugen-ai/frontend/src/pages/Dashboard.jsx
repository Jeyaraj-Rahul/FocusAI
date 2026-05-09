import { ArrowRight, Clock3, Download, FileText, Plus, UploadCloud } from "lucide-react";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Button from "../components/common/Button.jsx";
import Card from "../components/common/Card.jsx";
import EmptyState from "../components/common/EmptyState.jsx";
import { useAuth } from "../hooks/useAuth.js";

const recentReports = [
  {
    id: 1,
    title: "Smart Attendance System",
    type: "Academic report",
    status: "Draft",
    updatedAt: "Today, 10:30 AM",
    progress: 72
  },
  {
    id: 2,
    title: "E-Commerce Analytics Dashboard",
    type: "Professional report",
    status: "Generated",
    updatedAt: "Yesterday, 6:45 PM",
    progress: 100
  },
  {
    id: 3,
    title: "AI Crop Disease Detection",
    type: "Research report",
    status: "Review",
    updatedAt: "May 5, 2026",
    progress: 88
  }
];

export default function Dashboard() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = window.setTimeout(() => setLoading(false), 700);
    return () => window.clearTimeout(timer);
  }, []);

  return (
    <section className="space-y-6">
      <div className="flex flex-col justify-between gap-4 xl:flex-row xl:items-center">
        <div>
          <p className="text-sm font-medium text-blue-600 dark:text-blue-300">Welcome back, {user?.full_name || "Creator"}</p>
          <h2 className="mt-1 text-2xl font-bold tracking-normal text-slate-950 dark:text-white sm:text-3xl">Dashboard</h2>
          <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-400">
            Manage generated reports, upload formatting templates, and start new document automation workflows.
          </p>
        </div>
        <Link to="/app/reports/new">
          <Button className="w-full sm:w-auto">
            <Plus size={18} /> Create new report
          </Button>
        </Link>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <MetricCard label="Reports" value="24" detail="8 generated this month" />
        <MetricCard label="Templates" value="6" detail="2 recently analyzed" />
        <MetricCard label="Exports" value="41" detail="DOCX and PDF downloads" />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_380px]">
        <Card className="p-5" delay={0.05}>
          <div className="flex items-center justify-between gap-3">
            <div>
              <h3 className="text-lg font-semibold text-slate-950 dark:text-white">Recent reports</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400">Continue editing or export completed documents.</p>
            </div>
            <Button variant="ghost" className="hidden sm:inline-flex">
              View all <ArrowRight size={16} />
            </Button>
          </div>

          <div className="mt-5 space-y-3">
            {loading
              ? Array.from({ length: 3 }).map((_, index) => <ReportSkeleton key={index} />)
              : recentReports.length
                ? recentReports.map((report) => <ReportRow key={report.id} report={report} />)
                : (
                  <EmptyState
                    icon={<FileText size={22} />}
                    title="No reports yet"
                    description="Create your first report to see recent activity here."
                    actionLabel="Create report"
                  />
                )}
          </div>
        </Card>

        <aside className="space-y-6">
          <Card className="p-5" delay={0.1}>
            <div className="flex items-start gap-3">
              <div className="grid h-11 w-11 shrink-0 place-items-center rounded-md bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-200">
                <UploadCloud size={22} />
              </div>
              <div>
                <h3 className="font-semibold text-slate-950 dark:text-white">Upload template</h3>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Add a DOCX sample report to prepare formatting rules for future generation.</p>
              </div>
            </div>
            <div className="mt-5 rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 px-4 py-8 text-center dark:border-slate-700 dark:bg-slate-950">
              <UploadCloud className="mx-auto h-8 w-8 text-slate-400" />
              <p className="mt-3 text-sm font-semibold text-slate-800 dark:text-slate-100">Drop DOCX template here</p>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Template upload logic will connect to the backend next.</p>
            </div>
            <Link to="/app/templates" className="mt-4 block">
              <Button variant="secondary" className="w-full">Open templates</Button>
            </Link>
          </Card>

          <Card className="border-slate-800 bg-slate-950 p-5 text-white" delay={0.15}>
            <Clock3 className="h-8 w-8 text-blue-300" />
            <h3 className="mt-4 font-semibold">Next workflow</h3>
            <p className="mt-2 text-sm text-slate-300">Create a report, choose a template, then export polished DOCX and PDF files.</p>
          </Card>
        </aside>
      </div>
    </section>
  );
}

function MetricCard({ label, value, detail }) {
  return (
    <Card className="p-5">
      <p className="text-sm text-slate-500 dark:text-slate-400">{label}</p>
      <p className="mt-2 text-3xl font-bold text-slate-950 dark:text-white">{value}</p>
      <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{detail}</p>
    </Card>
  );
}

function ReportRow({ report }) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="grid gap-4 rounded-lg border border-slate-200 p-4 transition hover:border-blue-200 hover:bg-blue-50/40 dark:border-slate-800 dark:hover:border-blue-900 dark:hover:bg-blue-950/20 md:grid-cols-[1fr_auto] md:items-center"
    >
      <div className="flex min-w-0 gap-4">
        <div className="grid h-12 w-12 shrink-0 place-items-center rounded-md bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-200">
          <FileText size={22} />
        </div>
        <div className="min-w-0">
          <h4 className="truncate font-semibold text-slate-950 dark:text-white">{report.title}</h4>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{report.type} - {report.updatedAt}</p>
          <div className="mt-3 h-2 max-w-sm overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
            <div className="h-full rounded-full bg-blue-600 dark:bg-blue-400" style={{ width: `${report.progress}%` }} />
          </div>
        </div>
      </div>
      <div className="flex items-center justify-between gap-3 md:justify-end">
        <span className="rounded-md bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200">{report.status}</span>
        <Button variant="ghost" className="h-9 px-3">
          <Download size={16} /> Export
        </Button>
      </div>
    </motion.article>
  );
}

function ReportSkeleton() {
  return (
    <div className="animate-pulse rounded-lg border border-slate-200 p-4 dark:border-slate-800">
      <div className="flex gap-4">
        <div className="h-12 w-12 rounded-md bg-slate-200 dark:bg-slate-800" />
        <div className="flex-1 space-y-3">
          <div className="h-4 w-2/3 rounded bg-slate-200 dark:bg-slate-800" />
          <div className="h-3 w-1/2 rounded bg-slate-200 dark:bg-slate-800" />
          <div className="h-2 w-full rounded bg-slate-200 dark:bg-slate-800" />
        </div>
      </div>
    </div>
  );
}
